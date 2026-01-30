"""
Biznes - Interaktywny interfejs shell
Główny interfejs użytkownika dla gry edukacyjnej
Wersja 2.0 - Pełna interaktywność z menu akcji
"""

import cmd
import os
import sys
try:
    import yaml
except ImportError:
    yaml = None
import random
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field

from .core.models import (
    GameState, PlayerConfig, Company, Founder, 
    LegalForm, EmploymentForm, StartupStage,
    FoundersAgreement, VestingSchedule,
    ActionMode, ActionPointSystem, CostCalculator,
    BusinessModel, MarketAnalysis, BUSINESS_MODELS, MARKET_CONFIGS,
    calculate_customer_acquisition_chance
)
from .scenarios.engine import ScenarioEngine
from .utils.guidance import (
    get_priority_action as _get_priority_action_shared,
    get_risk_indicators as _get_risk_indicators_shared,
    pluralize_months as _pluralize_months_shared,
)
from .utils.shell_context import ShellContext

# ============================================================================
# KOLORY I FORMATOWANIE
# ============================================================================

class Colors:
    """ANSI color codes dla terminala"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    DIM = '\033[2m'
    END = '\033[0m'
    
    @classmethod
    def disable(cls):
        for attr in ['HEADER', 'BLUE', 'CYAN', 'GREEN', 'YELLOW', 'RED', 'BOLD', 'UNDERLINE', 'DIM', 'END']:
            setattr(cls, attr, '')


def colored(text: str, color: str) -> str:
    return f"{color}{text}{Colors.END}"


def _pluralize_months(n: int) -> str:
    return _pluralize_months_shared(n)


def _shorten(text: str, max_len: int) -> str:
    if max_len <= 0:
        return ""
    if len(text) <= max_len:
        return text
    if max_len <= 3:
        return text[:max_len]
    cut = text[: max_len - 3]
    if " " in cut:
        cut = cut[: cut.rfind(" ")]
        if not cut:
            cut = text[: max_len - 3]
    return cut + "..."


def print_box(title: str, content: List[str], color: str = Colors.CYAN):
    """Drukuje tekst w ramce"""
    max_len = max(len(title), max(len(line) for line in content) if content else 0)
    width = max_len + 4
    
    print(colored("┌" + "─" * width + "┐", color))
    print(colored("│", color) + f" {colored(title, Colors.BOLD)}" + " " * (width - len(title) - 1) + colored("│", color))
    print(colored("├" + "─" * width + "┤", color))
    for line in content:
        padding = width - len(line) - 1
        print(colored("│", color) + f" {line}" + " " * padding + colored("│", color))
    print(colored("└" + "─" * width + "┘", color))


# ============================================================================
# AKCJE W GRZE
# ============================================================================

@dataclass
class GameAction:
    """Reprezentuje możliwą akcję w grze"""
    id: str
    name: str
    description: str
    category: str
    available: bool = True
    blocked_reason: str = ""
    consequences: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    benefits: List[str] = field(default_factory=list)
    cost: float = 0.0
    recommended: bool = False
    warning: str = ""

    modes: Dict[str, ActionMode] = field(default_factory=dict)
    base_effect: Dict[str, Any] = field(default_factory=dict)
    educational_tip: str = ""
    
    # P1: Edukacyjne opisy
    educational_why: str = ""  # Dlaczego to ważne
    real_world_example: str = ""  # Przykład z życia
    statistics: str = ""  # Dane/statystyki
    common_mistake: str = ""  # Częsty błąd


# Słownik edukacyjnych opisów akcji
EDUCATIONAL_CONTENT = {
    "register_company": {
        "educational_why": """Rejestracja spółki daje Ci:
  • Ochronę majątku osobistego (odpowiedzialność ograniczona)
  • Możliwość wystawiania faktur i zawierania umów
  • Wiarygodność dla klientów i inwestorów
  • Możliwość pozyskania finansowania""",
        "real_world_example": """HISTORIA: Founder działał 8 mies. bez spółki. Klient 
  zamówił produkt za 50k PLN, ale nie mógł przelać na konto 
  prywatne. Stracił kontrakt.""",
        "statistics": "73% inwestorów odmawia rozmów bez zarejestrowanej spółki",
        "common_mistake": """❌ BŁĄD: "Zarejestruję jak znajdę inwestora"
✅ DOBRZE: Rejestracja w mies. 1-2, nawet bez inwestora"""
    },
    "sign_agreement": {
        "educational_why": """SHA (Shareholders Agreement) określa:
  • Jak dzielicie się udziałami (equity split)
  • Co się dzieje gdy ktoś odchodzi (good/bad leaver)
  • Kto podejmuje jakie decyzje
  • Jak rozwiązywać konflikty
  • Vesting schedule (nabywanie udziałów w czasie)""",
        "real_world_example": """HISTORIA: Dwóch founderów bez SHA zbudowało apkę 
  za 500k PLN. Partner odszedł po 6 mies z 50% equity i kodem.
  Sąd trwał 3 lata. Startup upadł.""",
        "statistics": "67% konfliktów founderów wynika z braku SHA",
        "common_mistake": """❌ BŁĄD: "Podpiszemy jak znajdziemy inwestora"
✅ DOBRZE: SHA PRZED wspólną pracą, nawet prostą"""
    },
    "develop_mvp": {
        "educational_why": """MVP (Minimum Viable Product) to:
  • Najszybszy sposób na walidację pomysłu
  • Minimalna wersja produktu do testów z klientami
  • Podstawa do zbierania feedbacku""",
        "real_world_example": """Dropbox zaczął od 3-minutowego video demo zanim 
  napisali linijkę kodu. Zebrali 70k zapisów na waiting list.""",
        "statistics": "42% startupów upada bo budują produkt którego nikt nie chce",
        "common_mistake": """❌ BŁĄD: Budowanie "idealnego" produktu przez miesiące
✅ DOBRZE: Wypuść cokolwiek w 4-8 tygodni i iteruj"""
    },
    "find_customers": {
        "educational_why": """Klienci płacący to:
  • Walidacja że ktoś chce Twój produkt (PMF)
  • MRR = Monthly Recurring Revenue
  • Feedback do ulepszania produktu
  • Dowód dla inwestorów""",
        "real_world_example": """Airbnb founderzy sami chodzili do pierwszych klientów,
  robili im zdjęcia mieszkań. Bezpośredni kontakt = wiedza.""",
        "statistics": "Startupy z >10 płacących klientów mają 3x większą szansę na rundę",
        "common_mistake": """❌ BŁĄD: "Najpierw dokończę produkt, potem sprzedaż"
✅ DOBRZE: Szukaj klientów od dnia 1, nawet z prototypem"""
    },
    "seek_investor": {
        "educational_why": """Inwestor VC/anioł to:
  • Kapitał na szybki wzrost
  • Kontakty i mentoring (smart money)
  • Walidacja przez doświadczonych
  Ale UWAGA: rozwodnienie i presja na wzrost""",
        "real_world_example": """Slack zebrał 340M$ przed generowaniem przychodu.
  Większość startupów NIE potrzebuje VC - bootstrapping też działa.""",
        "statistics": "Tylko 1% startupów dostaje funding VC. Mediana rundy seed: 2M PLN",
        "common_mistake": """❌ BŁĄD: "Muszę mieć inwestora żeby zacząć"
✅ DOBRZE: Inwestor gdy masz PMF i potrzebujesz skalować"""
    },
    "hire_employee": {
        "educational_why": """Zatrudnienie to:
  • Szybszy rozwój produktu/sprzedaży
  • Nowe kompetencje w zespole
  ALE: +12-15k PLN/mies kosztu, zobowiązania prawne""",
        "real_world_example": """WhatsApp miał 55 pracowników przy 900M użytkownikach.
  Instagram: 13 osób przy sprzedaży za 1B$. Mniej = więcej.""",
        "statistics": "Przedwczesne zatrudnianie to #3 powód upadku startupów",
        "common_mistake": """❌ BŁĄD: Zatrudniać przed product-market fit
✅ DOBRZE: Najpierw PMF, potem skalowanie zespołu"""
    },
    "pivot": {
        "educational_why": """Pivot to zmiana kierunku gdy:
  • Obecny produkt nie znajduje klientów
  • Rynek się zmienił
  • Odkryłeś lepszą okazję
  Lepiej pivotować niż upaść.""",
        "real_world_example": """YouTube zaczął jako serwis randkowy (video dating).
  Slack był grą MMORPG. Twitter - podcasty. Pivot uratował je.""",
        "statistics": "93% udanych startupów zrobiło co najmniej 1 pivot",
        "common_mistake": """❌ BŁĄD: Pivotować co miesiąc bez testów
✅ DOBRZE: Daj pomysłowi 3-6 mies, zbierz dane, decyduj"""
    }
}


class ActionSystem:
    """System zarządzania akcjami w grze"""
    
    def __init__(self, game_state: GameState, config: PlayerConfig):
        self.state = game_state
        self.config = config
        self._cost_calc = CostCalculator()

    def _invite_partner(self, company: Company) -> Tuple[bool, str, Dict]:
        has_partner = any((not f.is_player) and (not f.left_company) for f in company.founders)
        if has_partner:
            return False, "Masz już wspólnika.", {}

        player = next((f for f in company.founders if f.is_player and (not f.left_company)), None)
        if not player:
            return False, "Brak gracza w spółce - nie można dodać wspólnika.", {}

        print(colored("\n👥 DODAJ WSPÓLNIKA", Colors.HEADER))

        partner_name = input(colored("Imię wspólnika [Partner]: ", Colors.YELLOW)).strip() or "Partner"

        print(colored("\nRola", Colors.CYAN))
        print(f"  {colored('1', Colors.GREEN)}. Technical")
        print(f"  {colored('2', Colors.GREEN)}. Business")
        role_choice = input(colored("Twój wybór [1]: ", Colors.YELLOW)).strip() or "1"
        role = "technical" if role_choice == "1" else "business"

        while True:
            raw = input(colored("Kapitał wnoszony (PLN) [0]: ", Colors.YELLOW)).strip() or "0"
            try:
                partner_capital = float(raw)
                partner_capital = max(0.0, min(1000000.0, partner_capital))
                break
            except ValueError:
                print(colored("Podaj liczbę.", Colors.RED))

        while True:
            raw = input(colored("Proponowane equity % [20]: ", Colors.YELLOW)).strip() or "20"
            try:
                partner_equity = float(raw)
                partner_equity = max(5.0, min(45.0, partner_equity))
                break
            except ValueError:
                print(colored("Podaj liczbę.", Colors.RED))

        print(colored("\n🔍 WERYFIKACJA (KRYTYCZNE!):", Colors.YELLOW))
        krs = input(colored("Sprawdziłeś w KRS? (tak/nie) [nie]: ", Colors.YELLOW)).strip().lower() or "nie"
        krs_verified = krs in ["tak", "t", "yes", "y", "1"]
        if not krs_verified:
            print(colored("⚠️ RYZYKO: Możesz nie wiedzieć o upadłościach!", Colors.RED))

        partner = Founder(
            name=partner_name,
            role=role,
            equity_percentage=partner_equity,
            initial_investment=partner_capital,
            personal_invested=partner_capital,
            krs_verified=krs_verified,
            is_player=False,
        )
        company.founders.append(partner)
        company.cash_on_hand += partner_capital

        player.equity_percentage = max(0.0, player.equity_percentage - partner_equity)

        self.config.has_partner = True
        self.config.partner_name = partner.name
        self.config.partner_equity = partner.equity_percentage
        self.config.partner_capital = partner_capital
        self.config.partner_krs_verified = krs_verified
        self.config.player_equity = player.equity_percentage
        self.config.esop_pool = company.esop_pool_percentage

        msg = f"Dodano wspólnika {partner.name} ({partner_equity:.0f}%)"
        if not self.state.agreement_signed:
            msg += " Teraz podpisz SHA."

        return True, msg, {
            'cash': partner_capital,
            'equity_change': -partner_equity,
        }
    
    def get_available_actions(self) -> List[GameAction]:
        """Zwraca listę dostępnych akcji w danym miesiącu"""
        actions = []
        company = self.state.company
        month = self.state.current_month
        
        # AKCJE PRAWNE
        if not company.registered:
            cost = 2000 if company.legal_form == LegalForm.PSA else 2500
            actions.append(GameAction(
                id="register_company",
                name="Załóż spółkę",
                description=f"Zarejestruj {company.legal_form.value.upper()} w KRS",
                category="legal",
                available=company.cash_on_hand >= cost,
                blocked_reason="" if company.cash_on_hand >= cost else f"Potrzebujesz {cost} PLN",
                consequences=[f"Koszt: ~{2000 if company.legal_form == LegalForm.PSA else 2500} PLN"],
                benefits=["Ochrona prawna", "Możliwość pozyskania inwestora"],
                risks=["Koszty księgowości (~500-1500 PLN/mies)"],
                cost=cost,
                recommended=month >= 1
            ))
        
        if not self.state.agreement_signed:
            has_partner = any((not f.is_player) and (not f.left_company) for f in company.founders)
            sha_min_cost = 500
            sha_available = has_partner and company.cash_on_hand >= sha_min_cost
            if not has_partner:
                sha_blocked = "Nie masz partnera"
            elif company.cash_on_hand < sha_min_cost:
                sha_blocked = f"Potrzebujesz {sha_min_cost} PLN"
            else:
                sha_blocked = ""
            actions.append(GameAction(
                id="sign_agreement",
                name="Podpisz umowę wspólników (SHA)",
                description="Formalna umowa regulująca prawa founderów",
                category="legal",
                available=sha_available,
                blocked_reason=sha_blocked,
                consequences=["Koszt prawnika: 3000-8000 PLN"],
                benefits=["Jasne zasady vestingu", "Ochrona przed bad leaver"],
                risks=["Bez umowy: KRYTYCZNE RYZYKO sporów"],
                recommended=has_partner,
                warning="⚠️ BEZ UMOWY RYZYKUJESZ WSZYSTKO!" if has_partner and not self.state.agreement_signed else "",
                modes={
                    "diy": ActionMode(
                        name="🔧 Zrób sam (template)",
                        cost=500,
                        time_cost=2,
                        success_rate=0.4,
                        quality_modifier=0.5,
                        requires_skill="legal",
                    ),
                    "lawyer_basic": ActionMode(
                        name="⚖️ Prawnik (standard)",
                        cost=5000,
                        time_cost=1,
                        success_rate=0.95,
                        quality_modifier=1.0,
                    ),
                    "lawyer_premium": ActionMode(
                        name="🏢 Kancelaria (premium)",
                        cost=15000,
                        time_cost=0,
                        success_rate=0.99,
                        quality_modifier=1.2,
                    ),
                },
                base_effect={"agreement_signed": True},
            ))
        
        # AKCJE FINANSOWE
        if company.registered and company.mrr > 0:
            actions.append(GameAction(
                id="seek_investor",
                name="Szukaj inwestora",
                description="Rozmowy z VC/aniołami",
                category="financial",
                available=company.registered and self.state.agreement_signed,
                blocked_reason="" if (company.registered and self.state.agreement_signed) else "Najpierw zarejestruj spółkę i podpisz SHA",
                consequences=["Czas: 3-6 miesięcy", "Rozwodnienie 15-25%"],
                benefits=["Kapitał na rozwój", "Kontakty i mentoring"],
                risks=["Utrata kontroli", "Presja na szybki wzrost"]
            ))
        
        if company.registered and company.mrr > 5000:
            actions.append(GameAction(
                id="get_loan",
                name="Weź pożyczkę/kredyt",
                description="Finansowanie dłużne",
                category="financial",
                consequences=["Oprocentowanie: 8-15%"],
                benefits=["Brak rozwodnienia"],
                risks=["Konieczność spłaty"]
            ))
        
        # AKCJE ZESPOŁOWE
        if company.registered and company.cash_on_hand > 20000:
            actions.append(GameAction(
                id="hire_employee",
                name="Zatrudnij pracownika",
                description="Dodaj osobę do zespołu",
                category="team",
                consequences=[f"Koszt: 8000-15000 PLN/mies"],
                benefits=["Szybszy rozwój"],
                risks=["Przyspieszone spalanie gotówki"]
            ))
        
        # AKCJE PRODUKTOWE
        if not company.mvp_completed:
            actions.append(GameAction(
                id="develop_mvp",
                name="Rozwijaj MVP",
                description="Kontynuuj prace nad produktem",
                category="product",
                consequences=["Postęp: +20-30%"],
                benefits=["Przybliża do klientów"],
                recommended=True,
                modes={
                    "diy": ActionMode(
                        name="🔧 Zrób sam (koduj wieczorami)",
                        cost=0,
                        time_cost=2,
                        success_rate=0.7,
                        quality_modifier=0.8,
                        requires_skill="technical",
                    ),
                    "contractor": ActionMode(
                        name="👨‍💻 Freelancer", 
                        cost=5000,
                        time_cost=1,
                        success_rate=0.85,
                        quality_modifier=1.0,
                    ),
                    "agency": ActionMode(
                        name="🏢 Agencja dev",
                        cost=15000,
                        time_cost=0,
                        success_rate=0.95,
                        quality_modifier=1.2,
                    ),
                },
                base_effect={"mvp_progress": 25},
            ))
        
        if company.mvp_completed or getattr(self.config, 'player_has_mvp', False):
            actions.append(GameAction(
                id="find_customers",
                name="Szukaj klientów",
                description="Aktywna sprzedaż",
                category="product",
                consequences=["Potencjał: 2-10 nowych klientów"],
                benefits=["Walidacja produktu", "Wzrost MRR"],
                recommended=company.total_customers < 10
            ))
        
        if month > 6 and not company.product_market_fit:
            actions.append(GameAction(
                id="pivot",
                name="Rozważ pivot",
                description="Zmień kierunek produktu",
                category="product",
                consequences=["Reset części pracy"],
                benefits=["Szansa na lepszy PMF"],
                risks=["Strata trakcji"],
                warning="⚠️ 6+ mies bez PMF"
            ))

        if company.runway_months() < 2:
            cut_costs_available = not getattr(self.state, "cut_costs_this_month", False)
            actions.append(GameAction(
                id="cut_costs",
                name="🔻 Obetnij koszty",
                description="Zmniejsz burn rate o 30-50%",
                category="crisis",
                available=cut_costs_available,
                blocked_reason="" if cut_costs_available else "Już obciąłeś koszty w tym miesiącu",
                consequences=["Burn -30-50%", "Możliwe zwolnienia"],
                benefits=["Wydłużony runway"],
                risks=["Wolniejszy rozwój"],
                recommended=True,
                warning="⚠️ TRYB PRZETRWANIA"
            ))

            actions.append(GameAction(
                id="emergency_funding",
                name="💸 Pożyczka ratunkowa",
                description="Szybka pożyczka na przetrwanie",
                category="crisis",
                consequences=["Dług: 10-20k PLN", "Oprocentowanie 15-20%"],
                benefits=["Natychmiastowa gotówka"],
                risks=["Obciążenie finansowe"],
                warning="⚠️ OSTATECZNOŚĆ"
            ))

            if company.mrr > 0:
                can_advance = company.mrr >= 1000 and getattr(self.state, "revenue_advance_months", 0) <= 0
                actions.append(GameAction(
                    id="revenue_advance",
                    name="💰 Zaliczka na przychody",
                    description="Sprzedaj przyszłe przychody za gotówkę teraz",
                    category="crisis",
                    available=can_advance,
                    blocked_reason="" if can_advance else "Masz już aktywną zaliczkę lub MRR < 1000",
                    consequences=[f"Otrzymasz ~{company.mrr * 3:,.0f} PLN", "Stracisz 3 mies. MRR"],
                    benefits=["Szybka gotówka bez długu"],
                    risks=["Mniejszy cashflow przez 3 mies."]
                ))
        
        # AKCJE PARTNERSKIE
        player = next((f for f in company.founders if f.is_player), None)
        if player and player.vested_percentage > 0:
            actions.append(GameAction(
                id="sell_shares",
                name="Sprzedaj część udziałów",
                description=f"Masz {player.vested_percentage:.1f}% vested",
                category="partner",
                available=self.state.agreement_signed,
                blocked_reason="" if self.state.agreement_signed else "❌ Bez SHA nie możesz sprzedać",
                benefits=["Gotówka osobista"],
                risks=["Utrata kontroli"]
            ))
        else:
            actions.append(GameAction(
                id="sell_shares",
                name="Sprzedaj udziały",
                description="Brak vested udziałów",
                category="partner",
                available=False,
                blocked_reason="❌ Nie masz vested udziałów (cliff: 12 mies)"
            ))
        
        has_partner = any((not f.is_player) and (not f.left_company) for f in company.founders)
        actions.append(GameAction(
            id="invite_partner",
            name="Zaproś nowego wspólnika",
            description="Dodaj co-foundera",
            category="partner",
            available=not has_partner,
            blocked_reason="Masz już wspólnika" if has_partner else "",
            consequences=["Rozwodnienie udziałów"],
            benefits=["Nowe kompetencje"],
            risks=["Konflikty wizji"],
            warning="⚠️ Weryfikuj w KRS!"
        ))

        # Rozstanie z partnerem (jeśli jest partner)
        if has_partner:
            partner = next((f for f in company.founders if not f.is_player and not f.left_company), None)
            if partner:
                vesting_info = f"Vested: {partner.vested_percentage:.0f}%" if self.state.agreement_signed else "Brak vestingu (brak SHA)"
                actions.append(GameAction(
                    id="partner_leaves",
                    name="Rozstanie z partnerem",
                    description=f"Partner odchodzi ze spółki ({vesting_info})",
                    category="partner",
                    available=True,
                    consequences=["Zmiana struktury equity", "Potencjalny konflikt"],
                    benefits=["Pełna kontrola", "Brak sporów o wizję"],
                    risks=["Utrata kompetencji", "Bez SHA: partner zachowuje equity!"],
                    warning="⚠️ Sprawdź klauzulę good/bad leaver!" if self.state.agreement_signed else "⚠️ BRAK SHA - RYZYKO!"
                ))
        
        # AKCJE PORTFELA OSOBISTEGO
        player = next((f for f in company.founders if f.is_player), None)
        if player:
            # Pożyczka od foundera do firmy
            if player.personal_cash >= 5000:
                actions.append(GameAction(
                    id="founder_loan",
                    name="💵 Pożycz firmie z własnych środków",
                    description=f"Twoja gotówka osobista: {player.personal_cash:,.0f} PLN",
                    category="personal",
                    available=True,
                    consequences=["Transfer z portfela osobistego do firmy"],
                    benefits=["Szybka gotówka dla firmy", "Brak rozwodnienia"],
                    risks=["Ryzyko osobiste", "Możesz nie odzyskać"]
                ))
            
            # Wypłata pensji (jeśli firma ma gotówkę i jest zarejestrowana)
            if company.registered and company.cash_on_hand >= 5000:
                actions.append(GameAction(
                    id="founder_salary",
                    name="💰 Wypłać sobie pensję",
                    description=f"Dostępne w firmie: {company.cash_on_hand:,.0f} PLN",
                    category="personal",
                    available=True,
                    consequences=["Transfer z firmy do portfela osobistego"],
                    benefits=["Gotówka na życie"],
                    risks=["Zmniejszenie runway firmy"]
                ))
            
            # Dokapitalizowanie (formalna inwestycja)
            if player.personal_cash >= 10000 and company.registered:
                actions.append(GameAction(
                    id="founder_invest",
                    name="📈 Zainwestuj w firmę",
                    description=f"Formalne dokapitalizowanie (min 10k PLN)",
                    category="personal",
                    available=True,
                    consequences=["Zwiększenie kapitału spółki"],
                    benefits=["Więcej gotówki na rozwój", "Dokumentacja inwestycji"],
                    risks=["Ryzyko utraty środków"]
                ))

        # SPECJALNE
        actions.append(GameAction(
            id="do_nothing",
            name="Kontynuuj obecną strategię",
            description="Bez większych zmian",
            category="special",
            consequences=["Organiczny wzrost/spadek"]
        ))

        if company.cash_on_hand <= 0:
            for a in actions:
                if a.category == "crisis":
                    continue
                if a.modes:
                    has_free_mode = any(float(m.cost) <= 0 for m in a.modes.values())
                    if not has_free_mode and a.available:
                        a.available = False
                        if not a.blocked_reason:
                            a.blocked_reason = "Brak gotówki"
                    continue
                if float(getattr(a, "cost", 0.0) or 0.0) > 0 and a.available:
                    a.available = False
                    if not a.blocked_reason:
                        a.blocked_reason = "Brak gotówki"
        
        return actions
    
    def execute_action(self, action_id: str, mode: Optional[ActionMode] = None) -> Tuple[bool, str, Dict]:
        """Wykonuje akcję"""
        company = self.state.company
        effects = {}

        def _adjusted_success_rate(m: ActionMode) -> float:
            rate = float(m.success_rate)
            if m.requires_skill and m.requires_skill not in ["legal", "financial"]:
                if self.state.player_role != m.requires_skill:
                    rate -= 0.2
            return max(0.05, min(0.99, rate))

        def _recalc_burn_delta(before: float) -> float:
            company.monthly_burn_rate = float(self._cost_calc.total_burn(self.state))
            return company.monthly_burn_rate - before
        
        if action_id == "register_company":
            before_burn = company.monthly_burn_rate
            cost = 2000 if company.legal_form == LegalForm.PSA else 2500
            if company.cash_on_hand >= cost:
                company.cash_on_hand -= cost
                company.registered = True
                burn_delta = _recalc_burn_delta(before_burn)
                return True, "Spółka zarejestrowana w KRS!", {'cash': -cost, 'burn': burn_delta}
            return False, f"Brak środków ({cost} PLN)", {}
        
        elif action_id == "sign_agreement":
            before_burn = company.monthly_burn_rate
            has_partner = any((not f.is_player) and (not f.left_company) for f in company.founders)
            if not has_partner:
                return False, "Nie masz partnera - SHA nie ma sensu bez wspólnika.", {}

            selected = mode or ActionMode(name="⚖️ Prawnik (standard)", cost=5000, time_cost=1, success_rate=0.95)
            if company.cash_on_hand < selected.cost:
                return False, f"Brak środków ({selected.cost} PLN)", {}

            company.cash_on_hand -= selected.cost
            roll = random.random()
            if roll <= _adjusted_success_rate(selected):
                self.state.agreement_signed = True
                self.state.founders_agreement.signed = True
                burn_delta = _recalc_burn_delta(before_burn)
                return True, "Umowa wspólników podpisana!", {
                    'cash': -selected.cost,
                    'burn': burn_delta,
                    'show_portfele': True,
                }

            burn_delta = _recalc_burn_delta(before_burn)
            return False, "Nie udało się dopiąć SHA (błędy/negocjacje).", {
                'cash': -selected.cost,
                'burn': burn_delta,
            }
        
        elif action_id == "develop_mvp":
            before_burn = company.monthly_burn_rate

            selected = mode or ActionMode(name="🔧 Zrób sam", cost=0, time_cost=1, success_rate=0.7, quality_modifier=1.0)
            if selected.cost > 0 and company.cash_on_hand < selected.cost:
                return False, f"Brak środków ({selected.cost} PLN)", {}

            if selected.cost:
                company.cash_on_hand -= selected.cost

            rate = _adjusted_success_rate(selected)
            roll = random.random()
            if roll > rate and float(selected.cost) <= 0:
                base = random.uniform(4, 10)
            elif roll > rate:
                burn_delta = _recalc_burn_delta(before_burn)
                return False, "Nie udało się posunąć MVP w tym miesiącu.", {
                    'cash': -selected.cost,
                    'burn': burn_delta,
                }
            else:
                base = random.uniform(20, 30)
            progress = int(round(base * float(selected.quality_modifier)))
            progress = max(1, min(40, progress))

            self.state.mvp_progress = min(100, self.state.mvp_progress + progress)
            if self.state.mvp_progress >= 100:
                company.mvp_completed = True

            burn_delta = _recalc_burn_delta(before_burn)
            if company.mvp_completed:
                return True, "🎉 MVP UKOŃCZONE!", {
                    'mvp_progress': progress,
                    'cash': -selected.cost,
                    'burn': burn_delta,
                }

            return True, f"Postęp MVP: +{progress}% (teraz: {self.state.mvp_progress}%)", {
                'mvp_progress': progress,
                'cash': -selected.cost,
                'burn': burn_delta,
            }
        
        elif action_id == "find_customers":
            # Dynamiczna szansa akwizycji na podstawie modelu i rynku
            acquisition_chance = calculate_customer_acquisition_chance(self.state)
            
            if random.random() > acquisition_chance:
                return True, f"Nie udało się pozyskać klientów (szansa: {acquisition_chance*100:.0f}%)", {}
            
            # Sukces - liczba klientów zależy od modelu
            base_customers = random.randint(1, 5)
            if self.state.business_model:
                if self.state.business_model.model_type == "freemium":
                    base_customers = random.randint(3, 10)  # Więcej free userów
                elif self.state.business_model.model_type == "enterprise":
                    base_customers = random.randint(0, 1)  # Mniej, ale większe kontrakty
            
            # ARPU zależy od modelu
            avg_mrr = random.randint(150, 350)
            if self.state.business_model:
                avg_mrr = int(self.state.business_model.average_revenue_per_user * random.uniform(0.8, 1.2))
            
            new_customers = max(1, base_customers)
            company.total_customers += new_customers
            company.paying_customers += new_customers
            company.mrr += new_customers * avg_mrr
            
            chance_info = f" (szansa: {acquisition_chance*100:.0f}%)" if self.state.business_model or self.state.market_analysis else ""
            return True, f"Pozyskano {new_customers} klientów! MRR +{new_customers * avg_mrr} PLN{chance_info}", {}
        
        elif action_id == "hire_employee":
            before_burn = company.monthly_burn_rate
            company.employees += 1
            burn_delta = _recalc_burn_delta(before_burn)
            return True, "Zatrudniono pracownika!", {'burn': burn_delta}
        
        elif action_id == "seek_investor":
            if random.random() < 0.3:
                amount = random.randint(200, 500) * 1000
                dilution = random.randint(15, 25)
                self.state.pending_investment = {'amount': amount, 'dilution': dilution}
                return True, f"🎯 Inwestor zainteresowany! {amount:,} PLN za {dilution}%", {}
            return True, "Rozmowy trwają... Brak oferty w tym miesiącu.", {}
        
        elif action_id == "get_loan":
            before_burn = company.monthly_burn_rate
            amount = 50000
            company.cash_on_hand += amount
            company.extra_monthly_costs += 1000
            burn_delta = _recalc_burn_delta(before_burn)
            return True, f"Pożyczka {amount:,} PLN. Rata: 1k PLN/mies", {'cash': amount, 'burn': burn_delta}

        elif action_id == "invite_partner":
            return self._invite_partner(company)

        elif action_id == "cut_costs":
            if getattr(self.state, "cut_costs_this_month", False):
                return False, "Już obciąłeś koszty w tym miesiącu. Kolejne cięcia wymagają czasu na wdrożenie.", {}

            before_burn = company.monthly_burn_rate
            reduction = random.uniform(0.15, 0.3)
            company.cost_multiplier *= (1 - reduction)
            self.state.cut_costs_this_month = True
            burn_delta = _recalc_burn_delta(before_burn)
            saved = max(0.0, -burn_delta)
            return True, f"Burn obcięty o {reduction*100:.0f}%! Oszczędność: {saved:,.0f} PLN/mies", {
                'burn': burn_delta
            }

        elif action_id == "emergency_funding":
            before_burn = company.monthly_burn_rate
            amount = random.randint(10000, 20000)
            payment = int(amount * 0.015)
            company.cash_on_hand += amount
            company.extra_monthly_costs += payment
            burn_delta = _recalc_burn_delta(before_burn)
            return True, f"Pożyczka {amount:,.0f} PLN. Rata: ~{payment:,.0f} PLN/mies", {
                'cash': amount,
                'burn': burn_delta
            }

        elif action_id == "revenue_advance":
            if company.mrr <= 0:
                return False, "Brak MRR - nie masz przychodów do sprzedania.", {}
            if company.mrr < 1000:
                return False, "MRR zbyt niski (<1000 PLN).", {}
            if getattr(self.state, "revenue_advance_months", 0) > 0:
                return False, "Masz już aktywną zaliczkę na przychody.", {}

            advance = company.mrr * 3
            company.cash_on_hand += advance
            self.state.revenue_advance_months = 3
            self.state.revenue_advance_mrr = company.mrr
            return True, f"Zaliczka {advance:,.0f} PLN (3x MRR)", {'cash': advance}
        
        elif action_id == "pivot":
            self.state.mvp_progress = max(30, self.state.mvp_progress - 40)
            company.total_customers //= 2
            company.paying_customers //= 2
            company.mrr //= 2
            return True, "Pivot wykonany! Stracono połowę klientów.", {}

        elif action_id == "partner_leaves":
            partner = next((f for f in company.founders if not f.is_player and not f.left_company), None)
            if not partner:
                return False, "Nie masz partnera.", {}

            print(colored("\n⚖️ ROZSTANIE Z PARTNEREM", Colors.HEADER))
            print(f"Partner: {partner.name}")
            print(f"Equity: {partner.equity_percentage:.1f}%")
            print(f"Miesiące w spółce: {partner.months_in_company}")
            print(f"Vested: {partner.vested_percentage:.1f}%")
            print(f"Cliff ukończony: {'Tak' if partner.cliff_completed else 'Nie'}")

            if self.state.agreement_signed and self.state.founders_agreement.has_good_bad_leaver:
                print(colored("\n📋 Masz klauzulę good/bad leaver w SHA.", Colors.GREEN))
                print(colored("  1. Good leaver", Colors.GREEN) + " - partner zachowa vested equity")
                print(colored("  2. Bad leaver", Colors.RED) + " - partner straci część/całość equity")
            else:
                print(colored("\n⚠️ BRAK KLAUZULI GOOD/BAD LEAVER!", Colors.RED))
                print("Partner zachowa CAŁE swoje equity niezależnie od okoliczności!")

            choice = input(colored("\nTyp rozstania (1=good, 2=bad, 0=anuluj): ", Colors.YELLOW)).strip()
            if choice == "0":
                return False, "Anulowano.", {}

            is_good = choice != "2"
            result = self.state.process_founder_leaving(partner, is_good)

            if "warning" in result:
                print(colored(f"\n⚠️ {result['warning']}", Colors.RED))

            msg = f"Partner {partner.name} odszedł jako {'good' if is_good else 'bad'} leaver.\n"
            msg += f"Zachował: {result['equity_kept']:.1f}% equity\n"
            msg += f"Zwrócono do puli: {result['equity_returned']:.1f}%"

            self.config.has_partner = False
            return True, msg, {'equity_change': result['equity_returned']}
        
        elif action_id == "founder_loan":
            player = next((f for f in company.founders if f.is_player), None)
            if not player or player.personal_cash < 5000:
                return False, "Brak środków osobistych (min 5000 PLN).", {}
            
            amount = min(player.personal_cash, 20000)  # Max 20k na raz
            print(colored(f"\n💵 POŻYCZKA OD FOUNDERA", Colors.HEADER))
            print(f"Twoja gotówka osobista: {player.personal_cash:,.0f} PLN")
            print(f"Gotówka firmy: {company.cash_on_hand:,.0f} PLN")
            choice = input(colored(f"Ile pożyczasz firmie? (max {amount:,.0f}, 0=anuluj): ", Colors.YELLOW)).strip()
            try:
                loan = int(choice)
                if loan <= 0:
                    return False, "Anulowano.", {}
                loan = min(loan, int(player.personal_cash))
            except ValueError:
                return False, "Nieprawidłowa kwota.", {}
            
            player.personal_cash -= loan
            player.personal_invested += loan
            company.cash_on_hand += loan
            return True, f"Pożyczyłeś firmie {loan:,.0f} PLN ze środków osobistych.", {
                'personal_cash': -loan,
                'company_cash': loan
            }

        elif action_id == "founder_salary":
            player = next((f for f in company.founders if f.is_player), None)
            if not player:
                return False, "Brak gracza.", {}
            if not company.registered:
                return False, "Firma nie jest zarejestrowana.", {}
            if company.cash_on_hand < 5000:
                return False, "Firma ma za mało gotówki (min 5000 PLN).", {}
            
            max_salary = min(company.cash_on_hand - 2000, 15000)  # Zostaw min 2k w firmie
            print(colored(f"\n💰 WYPŁATA PENSJI", Colors.HEADER))
            print(f"Gotówka firmy: {company.cash_on_hand:,.0f} PLN")
            print(f"Twoja gotówka osobista: {player.personal_cash:,.0f} PLN")
            choice = input(colored(f"Ile wypłacasz? (max {max_salary:,.0f}, 0=anuluj): ", Colors.YELLOW)).strip()
            try:
                salary = int(choice)
                if salary <= 0:
                    return False, "Anulowano.", {}
                salary = min(salary, int(max_salary))
            except ValueError:
                return False, "Nieprawidłowa kwota.", {}
            
            company.cash_on_hand -= salary
            player.personal_cash += salary
            player.total_received += salary
            return True, f"Wypłaciłeś sobie {salary:,.0f} PLN pensji.", {
                'personal_cash': salary,
                'company_cash': -salary
            }

        elif action_id == "founder_invest":
            player = next((f for f in company.founders if f.is_player), None)
            if not player or player.personal_cash < 10000:
                return False, "Brak środków osobistych (min 10000 PLN).", {}
            if not company.registered:
                return False, "Firma musi być zarejestrowana.", {}
            
            max_invest = player.personal_cash
            print(colored(f"\n📈 INWESTYCJA W FIRMĘ", Colors.HEADER))
            print(f"Twoja gotówka osobista: {player.personal_cash:,.0f} PLN")
            print(f"Gotówka firmy: {company.cash_on_hand:,.0f} PLN")
            print(colored("⚠️ To formalna inwestycja - dokumentowana w KRS.", Colors.YELLOW))
            choice = input(colored(f"Ile inwestujesz? (min 10000, max {max_invest:,.0f}, 0=anuluj): ", Colors.YELLOW)).strip()
            try:
                invest = int(choice)
                if invest <= 0:
                    return False, "Anulowano.", {}
                if invest < 10000:
                    return False, "Minimalna inwestycja to 10000 PLN.", {}
                invest = min(invest, int(player.personal_cash))
            except ValueError:
                return False, "Nieprawidłowa kwota.", {}
            
            player.personal_cash -= invest
            player.personal_invested += invest
            company.cash_on_hand += invest
            company.total_raised += invest
            return True, f"Zainwestowałeś {invest:,.0f} PLN w firmę (udokumentowane).", {
                'personal_cash': -invest,
                'company_cash': invest,
                'total_raised': invest
            }

        elif action_id == "do_nothing":
            return True, "Kontynuujesz obecną strategię.", {}
        
        return False, "Nieznana akcja", {}


# ============================================================================
# GŁÓWNA KLASA SHELL
# ============================================================================

class BiznesShell(cmd.Cmd):
    """Interaktywny shell gry Biznes"""
    
    intro = ""  # Ustawiamy dynamicznie w preloop
    
    def preloop(self):
        """Wyświetla intro z menu numerycznym"""
        self._ctx.reset_to_main()
        self._sync_prompt()
        saves = self._get_saved_games()
        
        print(colored('═'*60, Colors.CYAN))
        print(colored('  BIZNES - Symulator Startupu v2.0', Colors.BOLD))
        print(colored('  Edukacyjna gra o zakładaniu firmy w Polsce', Colors.CYAN))
        print(colored('═'*60, Colors.CYAN))
        print()
        
        print(colored("  MENU:", Colors.BOLD))
        print(f"  {colored('1', Colors.GREEN)}. Nowa gra")
        
        if saves:
            print(f"  {colored('2', Colors.GREEN)}. Wczytaj grę ({len(saves)} zapisów)")
        else:
            print(f"  {colored('2', Colors.GREEN)}. Wczytaj grę (brak zapisów)")
        
        print(f"  {colored('3', Colors.GREEN)}. Pomoc")
        print(f"  {colored('0', Colors.GREEN)}. Wyjście")
        print()
    
    def default(self, line):
        """Obsługuje nieznane komendy i wybór numeryczny"""
        line = line.strip()

        if line.lower() in ["..", "back", "b"]:
            if self.game_state:
                self._show_game_menu()
            else:
                self._show_main_menu()
            return
        
        # Obsługa menu numerycznego - ZAWSZE działa
        if not self.game_state:
            # Menu startowe
            if line == '1':
                self.do_start("")
            elif line == '2':
                self.do_wczytaj("")
            elif line == '3':
                self.do_pomoc("")
            elif line == '0':
                return self.do_wyjscie("")
            else:
                print(colored("Wybierz 1-3 lub 0", Colors.RED))
                self._show_main_menu()
        else:
            # Menu w grze
            if line in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']:
                self._handle_game_menu(line)
    def _choose_action_mode(self, action: GameAction, remaining_points: int) -> Optional[ActionMode]:
        if not action.modes:
            return None
        if not self.game_state:
            return None

        self._mode_cancelled = False

        company = self.game_state.company

        print(colored("\n  JAK CHCESZ TO ZROBIĆ?", Colors.CYAN))

        modes: List[Tuple[str, ActionMode]] = list(action.modes.items())
        available_modes: List[Tuple[str, ActionMode]] = []
        for key, m in modes:
            rate = float(m.success_rate)
            if m.requires_skill and m.requires_skill not in ["legal", "financial"]:
                if self.game_state.player_role != m.requires_skill:
                    rate -= 0.2
            available = (float(m.cost) <= 0 or company.cash_on_hand >= float(m.cost)) and remaining_points >= int(m.time_cost)
            if available:
                available_modes.append((key, m))

        if not available_modes:
            print(colored("  Na razie stać Cię tylko na najtańszy tryb (template).", Colors.YELLOW))
            print(colored("  Zbierz więcej środków, aby odblokować lepsze opcje.", Colors.DIM))
            return None

        for i, (_, m) in enumerate(available_modes, 1):
            rate = float(m.success_rate)
            if m.requires_skill and m.requires_skill not in ["legal", "financial"]:
                if self.game_state.player_role != m.requires_skill:
                    rate -= 0.2

            cost_txt = f"{m.cost:,} PLN" if m.cost else "0 PLN"
            time_txt = f"{m.time_cost}" if m.time_cost != 0 else "0"
            succ_txt = f"{rate*100:.0f}%"

            line = f"  {colored(str(i), Colors.GREEN)}. {m.name}"
            meta = f"Koszt: {cost_txt} | Czas: {time_txt} | Sukces: {succ_txt}"
            print(line)
            print(colored(f"     {meta}", Colors.DIM))

        while True:
            print(colored("  [1-n] wybierz tryb | [..] powrót", Colors.DIM))
            raw = self._prompt_input("")
            if raw.lower() in ["..", "back", "b"]:
                self._mode_cancelled = True
                return None
            if not raw:
                # domyślny: pierwszy dostępny
                for _, m in available_modes:
                    return m
                return None
            try:
                idx = int(raw) - 1
            except ValueError:
                print(colored("Wybierz numer.", Colors.RED))
                continue

            if 0 <= idx < len(available_modes):
                _, m = available_modes[idx]
                return m

            print(colored("Nieprawidłowy wybór.", Colors.RED))

    def _execute_action(self, action: GameAction):
        """Wykonuje akcję z pełnym edukacyjnym feedbackiem"""
        print(colored(f"\n📋 {action.name}", Colors.HEADER))
        
        # Pokaż podstawowe informacje
        if action.consequences:
            print(colored("   KONSEKWENCJE:", Colors.YELLOW))
            for c in action.consequences:
                print(f"   • {c}")
        
        if action.benefits:
            print(colored("   KORZYŚCI:", Colors.GREEN))
            for b in action.benefits:
                print(f"   ✓ {b}")
        
        if action.risks:
            print(colored("   RYZYKA:", Colors.RED))
            for r in action.risks:
                print(f"   ⚠️ {r}")
        
        # P1: Pokaż edukacyjną treść jeśli dostępna
        edu_content = EDUCATIONAL_CONTENT.get(action.id, {})
        if edu_content:
            print(colored("\n   📚 EDUKACJA:", Colors.CYAN))
            if edu_content.get('educational_why'):
                print(colored("   Dlaczego to ważne:", Colors.BOLD))
                for line in edu_content['educational_why'].strip().split('\n'):
                    print(f"   {line}")
            if edu_content.get('statistics'):
                print(colored(f"\n   📊 STATYSTYKA: {edu_content['statistics']}", Colors.YELLOW))
            if edu_content.get('common_mistake'):
                print(colored("\n   ⚠️ CZĘSTY BŁĄD:", Colors.RED))
                for line in edu_content['common_mistake'].strip().split('\n'):
                    print(f"   {line}")
        
        remaining_points = max(0, self.max_actions_per_month - self.actions_this_month)
        selected_mode = self._choose_action_mode(action, remaining_points)

        if action.modes and not selected_mode:
            if getattr(self, "_mode_cancelled", False):
                return
            print(colored("\n❌ Brak dostępnych trybów (gotówka/punkty akcji).", Colors.RED))
            return

        if selected_mode:
            cost_val = float(selected_mode.cost)
            cost_txt = f"{cost_val:,.0f} PLN" if cost_val > 0 else "0 PLN"
            time_txt = str(int(selected_mode.time_cost))
            succ_txt = f"{float(selected_mode.success_rate)*100:.0f}%"
            print(colored(f"\n   Wybrany tryb: {selected_mode.name}", Colors.DIM))
            print(colored(f"   Koszt: {cost_txt} | Czas: {time_txt} | Sukces: {succ_txt}", Colors.DIM))

        time_cost = int(selected_mode.time_cost) if selected_mode else 1

        if remaining_points < time_cost:
            print(colored("\n❌ Brak punktów akcji na ten wybór.", Colors.RED))
            return

        if self._ask_yes_no("\nWykonać?", True):
            # P1: Zapisz stan PRZED akcją
            before_state = self._get_state_snapshot()
            
            success, msg, effects = self.action_system.execute_action(action.id, selected_mode)

            # Burn i punkty akcji mogą zależeć od stanu (np. spółka/SHA/klienci)
            self._recalculate_company_burn()
            self._recalculate_action_points()

            # P1: Zapisz stan PO akcji
            after_state = self._get_state_snapshot()
            
            # P1: Pokaż szczegółowy raport ze zmianami
            self._show_action_result(action, success, before_state, after_state, msg)

            if success and action.id == "invite_partner":
                # Uaktualnij config, żeby UX (zapisy/raporty) był spójny
                self.config.has_partner = True
                partner = next((f for f in self.game_state.company.founders if not f.is_player and not f.left_company), None)
                if partner:
                    self.config.partner_name = partner.name
                    self.config.partner_equity = partner.equity_percentage
                player = next((f for f in self.game_state.company.founders if f.is_player), None)
                if player:
                    self.config.player_equity = player.equity_percentage
                self.config.esop_pool = self.game_state.company.esop_pool_percentage
            
            # Pokaż portfele przy podpisaniu SHA
            if effects.get('show_portfele') and success:
                print(colored("\n📋 PODSUMOWANIE FINANSOWE PRZY PODPISANIU SHA:", Colors.HEADER))
                self.do_portfele("")
            
            # Zapisz do historii
            history_effects: List[str] = []
            if msg:
                history_effects.append(msg[:27] + "..." if len(msg) > 30 else msg)
            if isinstance(effects, dict):
                if 'cash' in effects and isinstance(effects['cash'], (int, float)):
                    history_effects.append(f"Gotówka {effects['cash']:+,.0f} PLN")
                if 'mrr' in effects and isinstance(effects['mrr'], (int, float)):
                    history_effects.append(f"MRR {effects['mrr']:+,.0f} PLN")

            history_effects = [_shorten(e, 30) for e in history_effects]

            self.action_history.append({
                'month': self.game_state.current_month,
                'type': 'action',
                'name': action.name[:35],
                'success': success,
                'effects': history_effects
            })
            self.actions_this_month += time_cost
            self.actions_taken_this_month += 1

    def _show_lessons(self):
        """Wnioski po przegranej z analizą błędów"""
        c = self.game_state.company
        month = self.game_state.current_month
        
        print(colored("\n💀 GAME OVER - ANALIZA", Colors.RED))
        print(colored("═"*60, Colors.RED))
        
        print(colored("\n❌ CO POSZŁO NIE TAK:", Colors.RED))
        
        mistakes = []
        
        # Sprawdź runway startowy
        initial_runway = self.config.initial_cash / max(self.config.monthly_burn, 1)
        if initial_runway < 6:
            mistakes.append({
                "error": "Za krótki początkowy runway",
                "detail": f"Zacząłeś z {initial_runway:.1f} mies. runway (min. zalecane: 6)",
                "lesson": "Przed startem zbierz minimum 6 mies. kosztów"
            })
        
        # Sprawdź tempo zdobywania klientów
        expected_customers = month * 2
        if c.paying_customers < expected_customers and month > 2:
            mistakes.append({
                "error": "Za wolne pozyskiwanie klientów",
                "detail": f"{c.paying_customers} klientów w {month} mies. (oczekiwane: ~{expected_customers})",
                "lesson": "Szukaj klientów od dnia 1, nawet bez gotowego produktu"
            })
        
        # Sprawdź burn vs MRR
        if c.mrr < c.monthly_burn_rate * 0.5 and month > 3:
            mistakes.append({
                "error": "MRR nie pokrywa kosztów",
                "detail": f"MRR {c.mrr:,.0f} vs Burn {c.monthly_burn_rate:,.0f}",
                "lesson": "Celuj w MRR > Burn w ciągu 6-12 mies."
            })
        
        # Sprawdź czy szukał finansowania
        if c.total_raised == 0 and month > 6:
            mistakes.append({
                "error": "Brak zewnętrznego finansowania",
                "detail": "Nie pozyskałeś inwestora ani pożyczki",
                "lesson": "Przy niskim runway rozmawiaj z inwestorami"
            })
        
        # Sprawdź SHA
        if self._has_partner() and not self.game_state.agreement_signed:
            mistakes.append({
                "error": "Brak umowy wspólników (SHA)",
                "detail": "Masz partnera bez formalnej umowy",
                "lesson": "Zawsze podpisuj SHA przed rozpoczęciem pracy"
            })
        
        for i, m in enumerate(mistakes, 1):
            print(colored(f"\n{i}. {m['error']}", Colors.YELLOW))
            print(f"   📊 {m['detail']}")
            print(colored(f"   💡 {m['lesson']}", Colors.CYAN))
        
        if not mistakes:
            print("   Trudno wskazać konkretny błąd - czasem po prostu się nie udaje.")
        
        # Co mogłeś zrobić inaczej
        print(colored("\n✅ CO MOGŁEŚ ZROBIĆ INACZEJ:", Colors.GREEN))
        print("   1. Zacząć z większym runway (min. 6 mies.)")
        print("   2. Szukać klientów od pierwszego dnia")
        print("   3. Obciąć koszty wcześniej gdy runway < 4 mies.")
        print("   4. Szukać inwestora/pożyczki gdy runway < 6 mies.")
        
        # Statystyki rozgrywki
        print(colored(f"\n📊 TWOJA GRA:", Colors.CYAN))
        print(f"   Przetrwałeś: {month} miesięcy")
        print(f"   Zdobytych klientów: {c.paying_customers}")
        print(f"   Najwyższe MRR: {c.mrr:,.0f} PLN")
        print(f"   MVP: {'Ukończone' if c.mvp_completed else f'{self.game_state.mvp_progress}%'}")
    
    def _generate_random_event(self) -> Optional[Dict]:
        """Generuje losowe zdarzenie z konsekwencjami"""
        company = self.game_state.company
        month = self.game_state.current_month
        
        events = [
            # Pozytywne
            {
                'type': 'positive', 'name': '🚀 Viral marketing',
                'desc': 'Twój post stał się viralowy!',
                'effects': {'customers': random.randint(5, 15), 'mrr_mult': 1.2}
            },
            {
                'type': 'positive', 'name': '🤝 Strategiczny partner',
                'desc': 'Duża firma chce współpracować.',
                'effects': {'mrr': random.randint(2000, 5000)}
            },
            {
                'type': 'positive', 'name': '🏢 Enterprise klient',
                'desc': 'Korporacja zainteresowana produktem!',
                'effects': {'mrr': random.randint(3000, 8000), 'customers': 1}
            },
            {
                'type': 'positive', 'name': '🏆 Nagroda branżowa',
                'desc': 'Wygrałeś konkurs startupowy!',
                'effects': {'cash': random.randint(10000, 30000), 'customers': random.randint(2, 5)}
            },
            # Negatywne
            {
                'type': 'negative', 'name': '💸 Konkurent z funding',
                'desc': 'Konkurent dostał rundę i obniża ceny.',
                'effects': {'mrr_mult': 0.85, 'churn': random.randint(1, 3)}
            },
            {
                'type': 'negative', 'name': '👋 Kluczowy pracownik odchodzi',
                'desc': 'Stracisz tempo rozwoju.',
                'effects': {'burn': -2000} if company.employees > 0 else {}
            },
            {
                'type': 'negative', 'name': '😤 Klient rezygnuje',
                'desc': 'Duży klient odszedł do konkurencji.',
                'effects': {'churn': random.randint(1, 3), 'mrr': -random.randint(500, 2000)}
            },
            {
                'type': 'negative', 'name': '🔧 Awaria techniczna',
                'desc': 'Poważny bug wymagał naprawy.',
                'effects': {'cash': -random.randint(2000, 5000)}
            },
        ]
        
        # Zdarzenia kontekstowe
        if self._has_partner() and not self.game_state.agreement_signed and month > 3:
            events.append({
                'type': 'negative', 'name': '⚔️ Konflikt z partnerem',
                'desc': 'Spór o podział obowiązków i equity!',
                'effects': {'risk': 20},
                'warning': 'Podpisz SHA aby uniknąć!'
            })

        # Zdarzenia związane z vestingiem
        if self._has_partner() and self.game_state.agreement_signed:
            partner = next((f for f in company.founders if not f.is_player and not f.left_company), None)
            if partner:
                vesting = self.game_state.founders_agreement.vesting_schedule
                # Cliff approaching
                if partner.months_in_company == vesting.cliff_months - 1:
                    events.append({
                        'type': 'neutral', 'name': '📅 Cliff za miesiąc',
                        'desc': f'{partner.name} osiągnie cliff w następnym miesiącu ({vesting.cliff_percentage}% vested).',
                        'effects': {},
                        'info': True
                    })
                # Cliff completed
                elif partner.months_in_company == vesting.cliff_months:
                    events.append({
                        'type': 'positive', 'name': '🎉 Cliff ukończony!',
                        'desc': f'{partner.name} osiągnął cliff - {vesting.cliff_percentage}% equity jest teraz vested.',
                        'effects': {},
                        'info': True
                    })
                # Partner unhappy (random chance after 6 months)
                elif partner.months_in_company > 6 and random.random() < 0.1:
                    events.append({
                        'type': 'negative', 'name': '😤 Partner niezadowolony',
                        'desc': f'{partner.name} rozważa odejście ze spółki.',
                        'effects': {'risk': 15},
                        'warning': f'Vested: {partner.vested_percentage:.0f}% - sprawdź klauzulę leaver!'
                    })
        
        if company.runway_months() < 4:
            events.append({
                'type': 'negative', 'name': '💀 Presja runway',
                'desc': 'Inwestorzy wyczuwają desperację.',
                'effects': {'valuation_mult': 0.8}
            })
        
        return random.choice(events)
    
    def _apply_event(self, event: Dict):
        """Aplikuje zdarzenie i pokazuje efekty"""
        company = self.game_state.company
        effects = event.get('effects', {})
        
        color = Colors.GREEN if event['type'] == 'positive' else Colors.RED
        print(colored(f"\n⚡ ZDARZENIE: {event['name']}", color))
        print(f"   {event['desc']}")
        
        changes = []
        
        if 'customers' in effects:
            delta = effects['customers']
            company.total_customers += delta
            company.paying_customers += delta
            if delta > 0:
                avg_mrr = company.mrr / max(1, company.paying_customers - delta) if company.paying_customers > delta else 200
                company.mrr += delta * avg_mrr
                changes.append(f"+{delta} klientów")
        
        if 'churn' in effects:
            churn = min(effects['churn'], company.paying_customers)
            if churn > 0:
                avg_mrr = company.mrr / max(1, company.paying_customers)
                company.paying_customers -= churn
                company.total_customers -= churn
                company.mrr -= churn * avg_mrr
                changes.append(f"-{churn} klientów (churn)")
        
        if 'mrr' in effects:
            company.mrr = max(0, company.mrr + effects['mrr'])
            sign = '+' if effects['mrr'] > 0 else ''
            changes.append(f"{sign}{effects['mrr']:,.0f} PLN MRR")
        
        if 'mrr_mult' in effects:
            old_mrr = company.mrr
            company.mrr = int(company.mrr * effects['mrr_mult'])
            diff = company.mrr - old_mrr
            sign = '+' if diff > 0 else ''
            changes.append(f"MRR {sign}{diff:,.0f} PLN")
        
        if 'cash' in effects:
            company.cash_on_hand += effects['cash']
            sign = '+' if effects['cash'] > 0 else ''
            changes.append(f"{sign}{effects['cash']:,.0f} PLN gotówki")
        
        if 'burn' in effects:
            company.extra_monthly_costs += effects['burn']
            self._recalculate_company_burn()
            sign = '+' if effects['burn'] > 0 else ''
            changes.append(f"Burn {sign}{effects['burn']:,.0f}/mies")
        
        if changes:
            print(colored("   → Efekt: {', '.join(changes)}", Colors.YELLOW))
        
        if 'warning' in event:
            print(colored(f"   💡 {event['warning']}", Colors.CYAN))
        
        # Zapisz do historii
        self.action_history.append({
            'month': self.game_state.current_month,
            'type': 'event',
            'name': event['name'],
            'effects': changes
        })
    
    def _show_game_menu(self):
        """Wyświetla menu podczas gry z widocznymi ryzykami"""
        self._ctx.reset_to_game()
        self._sync_prompt()
        c = self.game_state.company
        month = self.game_state.current_month
        
        remaining = max(0, self.max_actions_per_month - self.actions_this_month)
        print(colored(f"\n{'═'*60}", Colors.CYAN))
        print(colored(f"  Mies. {month} | 💰 {c.cash_on_hand:,.0f} | MRR: {c.mrr:,.0f} | ⏱️ {c.runway_months()} mies | ⚡ {remaining}/{self.max_actions_per_month}", Colors.DIM))
        print(colored(f"{'═'*60}", Colors.CYAN))
        
        # NOWE: Pasek ryzyka ZAWSZE widoczny
        risk_bar = self._get_risk_indicators()
        risk_color = Colors.RED if "🔴" in risk_bar else Colors.YELLOW if "🟡" in risk_bar or "🟠" in risk_bar else Colors.GREEN
        print(colored(f"  ⚠️  {risk_bar}", risk_color))
        print(colored(f"{'─'*60}", Colors.CYAN))
        
        # NOWE: Priorytet teraz
        self._show_priority_box()
        
        print(colored(f"\n{'─'*60}", Colors.CYAN))
        print(f"  {colored('1', Colors.GREEN)}. ▶️  Następny miesiąc")
        print(f"  {colored('2', Colors.GREEN)}. 📊 Status")
        print(f"  {colored('3', Colors.GREEN)}. ⚡ Akcje")
        print(f"  {colored('4', Colors.GREEN)}. 💰 Finanse")
        print(f"  {colored('5', Colors.GREEN)}. 💼 Portfele")
        print(f"  {colored('6', Colors.GREEN)}. 📈 Equity")
        print(f"  {colored('7', Colors.GREEN)}. ⚠️  Ryzyko")
        print(f"  {colored('8', Colors.GREEN)}. 💾 Zapisz")
        print(f"  {colored('9', Colors.GREEN)}. ❓ Pomoc")
        print(f"  {colored('0', Colors.GREEN)}. 🚪 Wyjście")
        print()
    
    prompt = colored("biznes> ", Colors.GREEN)
    
    def _handle_game_menu(self, choice: str):
        """Obsługuje wybór z menu gry"""
        if choice == '1':
            self.do_miesiac("")
        elif choice == '2':
            self.do_status("")
        elif choice == '3':
            self.do_akcje("")
        elif choice == '4':
            self.do_finanse("")
        elif choice == '5':
            self.do_portfele("")
        elif choice == '6':
            self.do_equity("")
        elif choice == '7':
            self.do_ryzyko("")
        elif choice == '8':
            self.do_zapisz("")
        elif choice == '9':
            self.do_pomoc("")
        elif choice == '0':
            if self._ask_yes_no("Zapisać grę przed wyjściem?"):
                self.do_zapisz("")
            self.game_state = None
            self._ctx.reset_to_main()
            self._sync_prompt()
            self._show_main_menu()
    
    def _show_main_menu(self):
        """Wyświetla główne menu z opcjami numerycznymi"""
        self._ctx.reset_to_main()
        self._sync_prompt()
        saves = self._get_saved_games()
        
        print(colored('═'*60, Colors.CYAN))
        print(colored('  BIZNES - Symulator Startupu v2.0', Colors.BOLD))
        print(colored('  Edukacyjna gra o zakładaniu firmy w Polsce', Colors.CYAN))
        print(colored('═'*60, Colors.CYAN))
        print()
        
        print(colored("  MENU:", Colors.BOLD))
        print(f"  {colored('1', Colors.GREEN)}. Nowa gra")
        
        if saves:
            print(f"  {colored('2', Colors.GREEN)}. Wczytaj grę ({len(saves)} zapisów)")
        else:
            print(f"  {colored('2', Colors.GREEN)}. Wczytaj grę (brak zapisów)")
        
        print(f"  {colored('3', Colors.GREEN)}. Pomoc")
        print(f"  {colored('0', Colors.GREEN)}. Wyjście")
        print()
    
    def do_status(self, arg):
        """Status firmy - pełny przegląd w formacie Markdown"""
        if not self.game_state:
            print(colored("Najpierw 'start'", Colors.RED))
            return
        
        c = self.game_state.company
        month = self.game_state.current_month
        founders = c.founders
        profit = c.mrr - c.monthly_burn_rate

        print(f"\n## 📊 STATUS - Miesiąc {month}\n")

        # === TABELA WSPÓLNIKÓW (Markdown) ===
        print("### Wspólnicy\n")
        
        # Nagłówek
        header = "| Pozycja | " + " | ".join(f.name for f in founders) + " |"
        separator = "|:--------|" + "|".join(":------:" for _ in founders) + "|"
        print(header)
        print(separator)
        
        # Wiersze danych
        print("| **Equity** | " + " | ".join(f"{f.equity_percentage:.0f}%" for f in founders) + " |")
        print("| **Vested** | " + " | ".join(f"{f.vested_percentage:.1f}%" for f in founders) + " |")
        print("| **Zainwestowane** | " + " | ".join(f"{f.personal_invested:,.0f} PLN" for f in founders) + " |")
        print("| **MVP wniesione** | " + " | ".join(f"{f.mvp_value:,.0f} PLN" if f.mvp_value > 0 else "-" for f in founders) + " |")
        print("| **Kontakty** | " + " | ".join(str(f.contacts_count) if f.contacts_count > 0 else "-" for f in founders) + " |")
        print("| **Zweryfikowany** | " + " | ".join("✓" if f.krs_verified else "⚠️" for f in founders) + " |")

        # === STAN FIRMY (Markdown) ===
        print("\n### Stan firmy\n")
        print("| Metryka | Wartość |")
        print("|:--------|-------:|")
        print(f"| 💰 Gotówka | {c.cash_on_hand:,.0f} PLN |")
        print(f"| 📈 MRR | {c.mrr:,.0f} PLN |")
        print(f"| 🔥 Burn/mies | {c.monthly_burn_rate:,.0f} PLN |")
        print(f"| 👥 Klienci | {c.paying_customers} |")
        print(f"| ⏱️ Runway | {c.runway_months()} mies |")

        print(f"| 💹 Wynik/mies | {profit:+,.0f} PLN |")

        # === STATUS PRAWNY (Markdown) ===
        print("\n### Status prawny i produkt\n")
        print("| Element | Status |")
        print("|:--------|:------:|")
        reg = "✓ Zarejestrowana" if c.registered else "✗ Nie"
        sha = "✓ Podpisana" if self.game_state.agreement_signed else "✗ Brak"
        mvp = "✓ Ukończone" if c.mvp_completed else f"{self.game_state.mvp_progress}%"
        print(f"| 🏢 Spółka | {reg} |")
        print(f"| 📝 SHA | {sha} |")
        print(f"| 🔧 MVP | {mvp} |")
        print(f"| 📋 ESOP | {c.esop_pool_percentage:.0f}% |")

        # === HISTORIA (Markdown) ===
        if self.action_history:
            print("\n### Ostatnie wydarzenia\n")
            print("| Mies. | Typ | Wydarzenie | Efekt |")
            print("|:-----:|:---:|:-----------|:------|")
            for entry in self.action_history[-5:]:
                m = entry.get('month', '?')
                etype = entry.get('type')
                if etype == 'event':
                    icon = '⚡'
                elif etype == 'month':
                    icon = '📅'
                else:
                    icon = '✓' if entry.get('success', True) else '✗'
                name = entry.get('name', '')[:35]
                effects = _shorten(', '.join(entry.get('effects', [])) or '-', 40)
                print(f"| {m} | {icon} | {name} | {effects} |")
        
        print()  # Pusta linia na końcu
    
    def do_akcje(self, arg):
        """Pokaż akcje"""
        if not self.game_state:
            print(colored("Najpierw 'start'", Colors.RED))
            return
        self._show_action_menu()
    
    def do_dashboard(self, arg):
        """Skonsolidowany widok wszystkiego"""
        if not self.game_state:
            print(colored("Najpierw 'start'", Colors.RED))
            return
        
        c = self.game_state.company
        month = self.game_state.current_month
        self._recalculate_company_burn()
        
        print(colored("\n" + "═"*70, Colors.CYAN))
        print(colored(f"  📊 DASHBOARD - Miesiąc {month}", Colors.BOLD))
        print(colored("═"*70, Colors.CYAN))
        
        # SEKCJA 1: KRYTYCZNE WSKAŹNIKI
        runway = c.runway_months()
        runway_color = Colors.RED if runway < 3 else Colors.YELLOW if runway < 6 else Colors.GREEN
        net_result = c.mrr - c.monthly_burn_rate
        result_color = Colors.GREEN if net_result >= 0 else Colors.RED
        
        print(f"\n  💰 GOTÓWKA: {colored(f'{c.cash_on_hand:>10,.0f} PLN', runway_color)}    ⏱️ RUNWAY: {colored(f'{runway:>2}', runway_color)} mies")
        print(f"  📈 MRR:     {c.mrr:>10,.0f} PLN    🔥 BURN:   {c.monthly_burn_rate:>6,.0f} PLN/mies")
        print(f"  👥 KLIENCI: {c.paying_customers:>10}         💹 WYNIK:  {colored(f'{net_result:>+6,.0f} PLN/mies', result_color)}")
        
        # SEKCJA 2: RYZYKA
        risks = self._get_all_risks()
        if risks:
            print(colored("\n⚠️ AKTYWNE RYZYKA:", Colors.RED))
            for risk in risks[:3]:
                print(f"   {risk['icon']} {risk['name']}: {risk['action']}")
        
        # SEKCJA 3: PRIORYTET
        action, why, _ = self._get_priority_action()
        print(colored(f"\n🎯 PRIORYTET: {action}", Colors.YELLOW))
        print(f"   {why}")
        
        # SEKCJA 4: STATUS CHECKLIST
        print(colored("\n📋 CHECKLIST:", Colors.CYAN))
        items = [
            ("Spółka", c.registered, "Zarejestruj w KRS"),
            ("SHA", self.game_state.agreement_signed or not self.config.has_partner, "Podpisz umowę wspólników"),
            ("MVP", c.mvp_completed, f"Ukończ produkt ({self.game_state.mvp_progress}%)"),
            ("PMF", c.paying_customers >= 10, f"Zdobądź klientów ({c.paying_customers}/10)"),
        ]
        for name, done, todo in items:
            status = colored("✅", Colors.GREEN) if done else colored("⬜", Colors.DIM)
            text = colored(name, Colors.GREEN) if done else f"{name} → {todo}"
            print(f"   {status} {text}")
        
        # SEKCJA 5: WSPÓLNICY
        print(colored("\n👥 WSPÓLNICY:", Colors.CYAN))
        for f in c.founders:
            verified = "✓" if f.krs_verified else "⚠️"
            vested_pct = (f.vested_percentage / f.equity_percentage * 100) if f.equity_percentage > 0 else 0
            print(f"   {f.name}: {f.equity_percentage:.0f}% equity (vested: {vested_pct:.0f}%) {verified}")
        
        print(colored("\n" + "═"*70, Colors.CYAN))

    def do_finanse(self, arg):
        """Finanse"""
        if not self.game_state:
            print(colored("Najpierw 'start'", Colors.RED))
            return
        c = self.game_state.company
        self._recalculate_company_burn()

        breakdown = self._cost_calc.calculate_monthly_burn(self.game_state)
        total = sum(breakdown.values())
        cost_lines: List[str] = []
        if breakdown:
            for k, v in sorted(breakdown.items(), key=lambda x: -x[1]):
                cost_lines.append(f"{k}: {v:,.0f} PLN")
        cost_summary = ", ".join(cost_lines[:3])
        if len(cost_lines) > 3:
            cost_summary += ", ..."
        print_box("FINANSE", [
            f"MRR: {c.mrr:,.0f} PLN | ARR: {c.mrr*12:,.0f} PLN",
            f"Burn: {c.monthly_burn_rate:,.0f} PLN/mies",
            f"Gotówka: {c.cash_on_hand:,.0f} PLN",
            f"Runway: {c.runway_months()} mies",
            f"Wycena: {c.current_valuation:,.0f} PLN",
            f"Koszty (top): {cost_summary}" if breakdown else "Koszty: (brak danych)"
        ])
    
    def do_portfele(self, arg):
        """Portfele wspólników i biznesu - przejrzystość finansowa (Markdown)"""
        if not self.game_state:
            print(colored("Najpierw 'start'", Colors.RED))
            return
        
        c = self.game_state.company
        month = self.game_state.current_month
        founders = c.founders
        profit = c.mrr - c.monthly_burn_rate

        print(f"\n## 💼 PRZEJRZYSTOŚĆ FINANSOWA - Miesiąc {month}\n")

        print("### Portfele wspólników\n")
        header = "| Pozycja | " + " | ".join(f.name for f in founders) + " |"
        separator = "|:--------|" + "|".join("------:" for _ in founders) + "|"
        print(header)
        print(separator)

        print("| **Gotówka osobista** | " + " | ".join(f"{f.personal_cash:,.0f} PLN" for f in founders) + " |")
        print("| **Equity** | " + " | ".join(f"{f.equity_percentage:.0f}%" for f in founders) + " |")
        print("| **Vested** | " + " | ".join(f"{f.vested_percentage:.1f}%" for f in founders) + " |")
        print("| **Zainwestowane** | " + " | ".join(f"{f.personal_invested:,.0f} PLN" for f in founders) + " |")
        print("| **Otrzymane z firmy** | " + " | ".join(f"{f.total_received:,.0f} PLN" for f in founders) + " |")
        print("| **Bilans netto** | " + " | ".join(f"{(f.total_received - f.personal_invested):+,.0f} PLN" for f in founders) + " |")
        print("| **MVP wniesione** | " + " | ".join(f"{f.mvp_value:,.0f} PLN" if f.mvp_value > 0 else "-" for f in founders) + " |")
        print("| **Kontakty** | " + " | ".join(str(f.contacts_count) if f.contacts_count > 0 else "-" for f in founders) + " |")
        print("| **Zweryfikowany** | " + " | ".join("✓" if f.krs_verified and f.debtor_registry_verified else "⚠️" for f in founders) + " |")

        print("\n### Finanse firmy\n")
        print("| Metryka | Wartość |")
        print("|:--------|-------:|")
        print(f"| 💰 Gotówka | {c.cash_on_hand:,.0f} PLN |")
        print(f"| 📈 MRR | {c.mrr:,.0f} PLN |")
        print(f"| 🔥 Burn/mies | {c.monthly_burn_rate:,.0f} PLN |")
        print(f"| 👥 Klienci | {c.paying_customers} |")
        print(f"| ⏱️ Runway | {c.runway_months()} mies |")
        print(f"| 💹 Wynik/mies | {profit:+,.0f} PLN |")

        print("\n### Umowy i struktura\n")
        print("| Element | Status |")
        print("|:--------|:------:|")
        print(f"| 🏢 Spółka zarejestrowana | {'TAK' if c.registered else 'NIE'} |")
        print(f"| 📝 SHA podpisana | {'TAK' if self.game_state.agreement_signed else 'NIE'} |")
        print(f"| 📋 ESOP | {c.esop_pool_percentage:.0f}% |")

        if profit > 0 and len(founders) > 1:
            print("\n### Potencjalny podział zysku (dywidenda)\n")
            print("| Wspólnik | Equity | Zysk/mies |")
            print("|:--------|------:|---------:|")
            for f in founders:
                share = profit * (f.equity_percentage / 100)
                print(f"| {f.name} | {f.equity_percentage:.0f}% | {share:,.0f} PLN |")

        if self.action_history:
            print("\n### Historia (ostatnie 10)\n")
            print("| Mies. | Typ | Wydarzenie | Efekt |")
            print("|:-----:|:---:|:-----------|:------|")
            for entry in self.action_history[-10:]:
                m = entry.get('month', '?')
                etype = entry.get('type')
                if etype == 'event':
                    icon = '⚡'
                elif etype == 'month':
                    icon = '📅'
                else:
                    icon = '✓' if entry.get('success', True) else '✗'
                name = entry.get('name', '')[:35]
                effects = _shorten(', '.join(entry.get('effects', [])) or '-', 60)
                print(f"| {m} | {icon} | {name} | {effects} |")

        print()
    
    def do_equity(self, arg):
        """Cap table"""
        if not self.game_state:
            print(colored("Najpierw 'start'", Colors.RED))
            return
        lines = []
        for f in self.game_state.company.founders:
            status = "✓" if f.cliff_completed else f"{f.months_in_company}/12"
            lines.append(f"{f.name}: {f.equity_percentage:.0f}% (vested: {f.vested_percentage:.1f}%) [{status}]")
        lines.append(f"ESOP: {self.game_state.company.esop_pool_percentage}%")
        print_box("EQUITY", lines)
    
    def do_ryzyko(self, arg):
        """Analiza ryzyka"""
        if not self.game_state:
            print(colored("Najpierw 'start'", Colors.RED))
            return
        
        c = self.game_state.company
        risks = []
        score = 0
        
        runway = c.runway_months()
        if runway < 3:
            risks.append(("KRYTYCZNE", "Runway < 3 mies!"))
            score += 40
        elif runway < 6:
            risks.append(("WYSOKIE", "Runway < 6 mies"))
            score += 25
        
        if self._has_partner() and not self.game_state.agreement_signed:
            risks.append(("KRYTYCZNE", "Brak umowy wspólników!"))
            score += 30
        
        if not c.registered and self.game_state.current_month > 3:
            risks.append(("WYSOKIE", "Spółka niezarejestrowana"))
            score += 15
        
        color = Colors.GREEN if score < 30 else Colors.YELLOW if score < 60 else Colors.RED
        print(colored(f"\n📊 RYZYKO: {score}/100", color))
        
        for level, msg in risks:
            c = Colors.RED if level == "KRYTYCZNE" else Colors.YELLOW
            print(f"   {colored(level, c)}: {msg}")
    
    def do_nauka(self, arg):
        """Edukacja"""
        topics = {
            "1": ("PSA vs Sp. z o.o.", "PSA: 1 PLN, praca jako wkład\nSp. z o.o.: 5000 PLN, notariusz"),
            "2": ("Vesting", "48 mies, cliff 12 mies, 25% po cliffie"),
            "3": ("Good/Bad leaver", "Good: zachowuje vested\nBad: traci wszystko"),
            "4": ("Tag/Drag-along", "Tag: mniejszościowy może dołączyć\nDrag: większościowy może zmusić")
        }
        
        print_box("EDUKACJA", [f"{k}. {v[0]}" for k, v in topics.items()])
        choice = self._ask("Temat (1-4)", "")
        if choice in topics:
            print(colored(f"\n{topics[choice][0]}:", Colors.HEADER))
            print(topics[choice][1])
    
    def do_slownik(self, arg):
        """Słownik"""
        terms = [
            "MRR: przychód miesięczny",
            "Runway: ile miesięcy przetrwasz",
            "Vesting: nabywanie udziałów w czasie",
            "Cliff: okres próbny (12 mies)",
            "SHA: umowa wspólników"
        ]
        print_box("SŁOWNIK", terms)
    
    def _get_saved_games(self) -> List[Dict]:
        """Zwraca listę zapisanych gier"""
        saves = []
        if self.save_dir.exists():
            for f in sorted(self.save_dir.glob("*.yaml"), reverse=True):
                try:
                    with open(f) as file:
                        data = yaml.safe_load(file) if yaml else {}
                        saves.append({
                            'path': f,
                            'name': f.stem,
                            'data': data,
                            'modified': datetime.fromtimestamp(f.stat().st_mtime)
                        })
                except Exception:
                    pass
        return saves
    
    def do_wczytaj(self, arg):
        """Wczytaj zapisaną grę"""
        saves = self._get_saved_games()
        
        if not saves:
            print(colored("Brak zapisanych gier.", Colors.YELLOW))
            return
        
        print(colored("\n" + "═"*60, Colors.CYAN))
        print(colored("  📂 ZAPISANE GRY", Colors.HEADER))
        print(colored("═"*60, Colors.CYAN))
        
        for i, save in enumerate(saves[:10], 1):  # Max 10 zapisów
            data = save['data']
            month = data.get('month', '?')
            cash = data.get('cash', 0)
            mrr = data.get('mrr', 0)
            player = data.get('player_name', 'Nieznany')
            modified = save['modified'].strftime('%Y-%m-%d %H:%M')
            
            print(f"\n  {colored(str(i), Colors.GREEN)}. {save['name']}")
            print(f"     👤 {player} | Miesiąc {month}")
            print(f"     💰 {cash:,.0f} PLN | MRR: {mrr:,.0f} PLN")
            print(f"     📅 {modified}")
        
        print(colored("\n" + "─"*60, Colors.CYAN))
        choice = self._ask("Wybierz numer (lub Enter aby anulować)", "")
        
        if not choice:
            return
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(saves):
                self._load_game(saves[idx])
            else:
                print(colored("Nieprawidłowy numer.", Colors.RED))
        except ValueError:
            print(colored("Wprowadź numer.", Colors.RED))
    
    def _load_game(self, save: Dict):
        """Wczytuje grę z zapisu"""
        data = save['data']
        
        # Odtwórz konfigurację
        self.config = PlayerConfig()
        self.config.player_name = data.get('player_name', 'Founder')
        self.config.player_role = data.get('player_role', 'technical')
        self.config.has_partner = data.get('has_partner', False)
        self.config.partner_name = data.get('partner_name', '')
        self.config.player_equity = data.get('player_equity', 50)
        self.config.partner_equity = data.get('partner_equity', 40)
        self.config.esop_pool = data.get('esop_pool', 10)
        self.config.legal_form = data.get('legal_form', 'psa')
        self.config.month = data.get('month', 0)
        self.config.cash = data.get('cash', 10000)
        self.config.burn = data.get('burn', 5000)
        
        # Odtwórz stan gry
        self._initialize_game()
        
        # Nadpisz wartości z zapisu
        self.game_state.current_month = data.get('month', 0)
        self.game_state.company.cash_on_hand = data.get('cash', 10000)
        self.game_state.company.mrr = data.get('mrr', 0)
        self.game_state.company.paying_customers = data.get('customers', 0)
        self.game_state.company.total_customers = data.get('customers', 0)
        self.game_state.company.registered = data.get('registered', False)
        self.game_state.company.mvp_completed = data.get('mvp_completed', False)
        self.game_state.agreement_signed = data.get('agreement_signed', False)
        self.game_state.mvp_progress = data.get('mvp_progress', 0)

        if 'founder_living_cost' in data:
            self.game_state.company.founder_living_cost = float(data.get('founder_living_cost', 3000.0) or 3000.0)
        if 'cost_multiplier' in data:
            self.game_state.company.cost_multiplier = float(data.get('cost_multiplier', 1.0) or 1.0)

        if 'extra_monthly_costs' in data:
            self.game_state.company.extra_monthly_costs = float(data.get('extra_monthly_costs', 0.0) or 0.0)
        else:
            burn = float(data.get('burn', self.config.monthly_burn) or self.config.monthly_burn)
            base = float(getattr(self.game_state.company, 'founder_living_cost', 3000.0) or 3000.0)
            self.game_state.company.extra_monthly_costs = max(0.0, burn - base)

        self._recalculate_company_burn()
        self._recalculate_action_points()

        self.game_state.revenue_advance_months = int(data.get('revenue_advance_months', 0) or 0)
        self.game_state.revenue_advance_mrr = float(data.get('revenue_advance_mrr', 0.0) or 0.0)

        # Jeśli zapis zawiera listę founderów, odtwórz ją (backward compatible)
        founders_data = data.get('founders')
        if isinstance(founders_data, list) and founders_data:
            restored: List[Founder] = []
            for fdata in founders_data:
                if not isinstance(fdata, dict):
                    continue
                restored.append(Founder(
                    name=fdata.get('name', ''),
                    role=fdata.get('role', ''),
                    equity_percentage=float(fdata.get('equity_percentage', 0.0) or 0.0),
                    vested_percentage=float(fdata.get('vested_percentage', 0.0) or 0.0),
                    months_in_company=int(fdata.get('months_in_company', 0) or 0),
                    cliff_completed=bool(fdata.get('cliff_completed', False)),
                    personal_invested=float(fdata.get('personal_invested', 0.0) or 0.0),
                    total_received=float(fdata.get('total_received', 0.0) or 0.0),
                    contacts_count=int(fdata.get('contacts_count', 0) or 0),
                    experience_years=int(fdata.get('experience_years', 0) or 0),
                    krs_verified=bool(fdata.get('krs_verified', False)),
                    debtor_registry_verified=bool(fdata.get('debtor_registry_verified', False)),
                    brought_mvp=bool(fdata.get('brought_mvp', False)),
                    mvp_value=float(fdata.get('mvp_value', 0.0) or 0.0),
                    is_player=bool(fdata.get('is_player', False)),
                ))

            if restored:
                if not any(f.is_player for f in restored):
                    restored[0].is_player = True
                self.game_state.company.founders = restored

                # Uaktualnij config na podstawie stanu (żeby UX był spójny)
                self.config.has_partner = any((not f.is_player) for f in restored)
                player = next((f for f in restored if f.is_player), None)
                if player:
                    self.config.player_name = player.name or self.config.player_name
                    self.config.player_role = player.role or self.config.player_role
                    self.config.player_equity = player.equity_percentage
                partner = next((f for f in restored if not f.is_player), None)
                if partner:
                    self.config.partner_name = partner.name or self.config.partner_name
                    self.config.partner_equity = partner.equity_percentage
                self.config.esop_pool = self.game_state.company.esop_pool_percentage
        
        print(colored(f"\n✓ Wczytano grę: {save['name']}", Colors.GREEN))
        self._ctx.enter_game()
        self._sync_prompt()
        self._show_game_menu()
    
    def do_zapisz(self, arg):
        """Zapisz grę"""
        if not self.game_state:
            return
        name = arg or f"save_{datetime.now().strftime('%Y%m%d_%H%M')}"
        path = self.save_dir / f"{name}.yaml"
        
        # Zapisz pełny stan gry
        data = {
            'player_name': self.config.player_name,
            'player_role': self.config.player_role,
            'has_partner': self.config.has_partner,
            'partner_name': self.config.partner_name,
            'player_equity': self.config.player_equity,
            'partner_equity': self.config.partner_equity,
            'esop_pool': self.config.esop_pool,
            'legal_form': self.config.legal_form,
            'month': self.game_state.current_month,
            'cash': self.game_state.company.cash_on_hand,
            'mrr': self.game_state.company.mrr,
            'burn': self.game_state.company.monthly_burn_rate,
            'founder_living_cost': getattr(self.game_state.company, 'founder_living_cost', 3000.0),
            'cost_multiplier': getattr(self.game_state.company, 'cost_multiplier', 1.0),
            'extra_monthly_costs': getattr(self.game_state.company, 'extra_monthly_costs', 0.0),
            'customers': self.game_state.company.paying_customers,
            'registered': self.game_state.company.registered,
            'mvp_completed': self.game_state.company.mvp_completed,
            'agreement_signed': self.game_state.agreement_signed,
            'mvp_progress': self.game_state.mvp_progress,
            'revenue_advance_months': getattr(self.game_state, 'revenue_advance_months', 0),
            'revenue_advance_mrr': getattr(self.game_state, 'revenue_advance_mrr', 0.0),
            'founders': [
                {
                    'name': f.name,
                    'role': f.role,
                    'equity_percentage': f.equity_percentage,
                    'vested_percentage': f.vested_percentage,
                    'months_in_company': f.months_in_company,
                    'cliff_completed': f.cliff_completed,
                    'personal_invested': f.personal_invested,
                    'total_received': f.total_received,
                    'contacts_count': f.contacts_count,
                    'experience_years': f.experience_years,
                    'krs_verified': f.krs_verified,
                    'debtor_registry_verified': f.debtor_registry_verified,
                    'brought_mvp': f.brought_mvp,
                    'mvp_value': f.mvp_value,
                    'is_player': f.is_player,
                }
                for f in self.game_state.company.founders
            ],
        }
        
        if yaml:
            with open(path, 'w') as f:
                yaml.dump(data, f)
            print(colored(f"✓ Zapisano: {path}", Colors.GREEN))
        else:
            print(colored("Brak modułu yaml - zapis niedostępny.", Colors.RED))


def main():
    """Punkt wejścia"""
    try:
        BiznesShell().cmdloop()
    except KeyboardInterrupt:
        print(colored("\n\nDo zobaczenia!", Colors.CYAN))
        sys.exit(0)


if __name__ == "__main__":
    main()
