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
    FoundersAgreement, VestingSchedule
)
from .scenarios.engine import ScenarioEngine


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
        "real_world_example": """WhatsApp miał 55 pracowników przy 900M użytkowników.
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
    
    def get_available_actions(self) -> List[GameAction]:
        """Zwraca listę dostępnych akcji w danym miesiącu"""
        actions = []
        company = self.state.company
        month = self.state.current_month
        
        # AKCJE PRAWNE
        if not company.registered:
            actions.append(GameAction(
                id="register_company",
                name="Załóż spółkę",
                description=f"Zarejestruj {company.legal_form.value.upper()} w KRS",
                category="legal",
                consequences=[f"Koszt: ~{2000 if company.legal_form == LegalForm.PSA else 2500} PLN"],
                benefits=["Ochrona prawna", "Możliwość pozyskania inwestora"],
                risks=["Koszty księgowości (~500-1500 PLN/mies)"],
                cost=2000 if company.legal_form == LegalForm.PSA else 2500,
                recommended=month >= 1
            ))
        
        if not self.state.agreement_signed:
            has_partner = len([f for f in company.founders if not f.is_player]) > 0
            actions.append(GameAction(
                id="sign_agreement",
                name="Podpisz umowę wspólników (SHA)",
                description="Formalna umowa regulująca prawa founderów",
                category="legal",
                available=has_partner,
                blocked_reason="" if has_partner else "Nie masz partnera",
                consequences=["Koszt prawnika: 3000-8000 PLN"],
                benefits=["Jasne zasady vestingu", "Ochrona przed bad leaver"],
                risks=["Bez umowy: KRYTYCZNE RYZYKO sporów"],
                cost=5000,
                recommended=has_partner,
                warning="⚠️ BEZ UMOWY RYZYKUJESZ WSZYSTKO!" if has_partner and not self.state.agreement_signed else ""
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
                recommended=True
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
        
        actions.append(GameAction(
            id="invite_partner",
            name="Zaproś nowego wspólnika",
            description="Dodaj co-foundera",
            category="partner",
            consequences=["Rozwodnienie udziałów"],
            benefits=["Nowe kompetencje"],
            risks=["Konflikty wizji"],
            warning="⚠️ Weryfikuj w KRS!"
        ))
        
        # SPECJALNE
        actions.append(GameAction(
            id="do_nothing",
            name="Kontynuuj obecną strategię",
            description="Bez większych zmian",
            category="special",
            consequences=["Organiczny wzrost/spadek"]
        ))
        
        return actions
    
    def execute_action(self, action_id: str) -> Tuple[bool, str, Dict]:
        """Wykonuje akcję"""
        company = self.state.company
        effects = {}
        
        if action_id == "register_company":
            cost = 2000 if company.legal_form == LegalForm.PSA else 2500
            if company.cash_on_hand >= cost:
                company.cash_on_hand -= cost
                company.registered = True
                return True, "Spółka zarejestrowana w KRS!", {'cash': -cost}
            return False, f"Brak środków ({cost} PLN)", {}
        
        elif action_id == "sign_agreement":
            cost = 5000
            if company.cash_on_hand >= cost:
                company.cash_on_hand -= cost
                self.state.agreement_signed = True
                self.state.founders_agreement.signed = True
                return True, "Umowa wspólników podpisana!", {'cash': -cost, 'show_portfele': True}
            return False, f"Brak środków ({cost} PLN)", {}
        
        elif action_id == "develop_mvp":
            progress = random.randint(20, 35)
            self.state.mvp_progress = min(100, self.state.mvp_progress + progress)
            if self.state.mvp_progress >= 100:
                company.mvp_completed = True
                return True, "🎉 MVP UKOŃCZONE!", {'mvp_progress': progress}
            return True, f"Postęp MVP: +{progress}% (teraz: {self.state.mvp_progress}%)", {}
        
        elif action_id == "find_customers":
            new_customers = random.randint(1, 5)
            avg_mrr = random.randint(150, 350)
            company.total_customers += new_customers
            company.paying_customers += new_customers
            company.mrr += new_customers * avg_mrr
            return True, f"Pozyskano {new_customers} klientów! MRR +{new_customers * avg_mrr} PLN", {}
        
        elif action_id == "hire_employee":
            company.employees += 1
            company.monthly_burn_rate += 12000
            return True, "Zatrudniono pracownika! Burn +12k PLN/mies", {}
        
        elif action_id == "seek_investor":
            if random.random() < 0.3:
                amount = random.randint(200, 500) * 1000
                dilution = random.randint(15, 25)
                self.state.pending_investment = {'amount': amount, 'dilution': dilution}
                return True, f"🎯 Inwestor zainteresowany! {amount:,} PLN za {dilution}%", {}
            return True, "Rozmowy trwają... Brak oferty w tym miesiącu.", {}
        
        elif action_id == "get_loan":
            amount = 50000
            company.cash_on_hand += amount
            company.monthly_burn_rate += 1000
            return True, f"Pożyczka {amount:,} PLN. Rata: 1k PLN/mies", {}
        
        elif action_id == "pivot":
            self.state.mvp_progress = max(30, self.state.mvp_progress - 40)
            company.total_customers //= 2
            company.paying_customers //= 2
            company.mrr //= 2
            return True, "Pivot wykonany! Stracono połowę klientów.", {}
        
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
        self._show_main_menu()
    
    def _show_main_menu(self):
        """Wyświetla główne menu z opcjami numerycznymi"""
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
            print(f"  {colored('2', Colors.DIM)}. Wczytaj grę (brak zapisów)")
        
        print(f"  {colored('3', Colors.GREEN)}. Pomoc")
        print(f"  {colored('0', Colors.GREEN)}. Wyjście")
        print()
    
    def default(self, line):
        """Obsługuje nieznane komendy i wybór numeryczny"""
        line = line.strip()
        
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
            else:
                print(colored("Wybierz numer z menu", Colors.RED))
                self._show_game_menu()
    
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
            self._show_main_menu()
    
    def _show_game_menu(self):
        """Wyświetla menu podczas gry z widocznymi ryzykami"""
        c = self.game_state.company
        month = self.game_state.current_month
        
        print(colored(f"\n{'═'*60}", Colors.CYAN))
        print(colored(f"  Mies. {month} | 💰 {c.cash_on_hand:,.0f} | MRR: {c.mrr:,.0f} | ⏱️ {c.runway_months()} mies", Colors.DIM))
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
    
    def __init__(self):
        super().__init__()
        self.game_state: Optional[GameState] = None
        self.config: Optional[PlayerConfig] = None
        self.action_system: Optional[ActionSystem] = None
        self.save_dir = Path.home() / ".biznes_saves"
        self.save_dir.mkdir(exist_ok=True)
        self.action_history: List[Dict] = []
        self.actions_this_month: int = 0
        self.max_actions_per_month: int = 2
        self.partners_data: List[Dict] = []  # Dane wielu wspólników
        self.mentor_mode: bool = True  # P2: Tryb mentor domyślnie włączony
    
    def _ask(self, prompt: str, default: str = "") -> str:
        if default:
            prompt = f"{prompt} [{default}]: "
        else:
            prompt = f"{prompt}: "
        try:
            response = input(colored(prompt, Colors.YELLOW))
            return response.strip() or default
        except (EOFError, KeyboardInterrupt):
            return default
    
    def _ask_number(self, prompt: str, min_val: float = 0, max_val: float = float('inf'), default: float = 0) -> float:
        while True:
            response = self._ask(f"{prompt} ({min_val}-{max_val})", str(int(default)) if default else "")
            try:
                value = float(response) if response else default
                if min_val <= value <= max_val:
                    return value
            except ValueError:
                pass
            print(colored(f"Podaj liczbę {min_val}-{max_val}", Colors.RED))
    
    def _ask_choice(self, prompt: str, options: List[str]) -> int:
        print(colored(f"\n{prompt}", Colors.CYAN))
        for i, option in enumerate(options, 1):
            print(f"  {colored(str(i), Colors.GREEN)}. {option}")
        while True:
            try:
                idx = int(self._ask("Twój wybór")) - 1
                if 0 <= idx < len(options):
                    return idx
            except ValueError:
                pass
            print(colored(f"Wybierz 1-{len(options)}", Colors.RED))
    
    def _ask_yes_no(self, prompt: str, default: bool = True) -> bool:
        response = self._ask(f"{prompt} (tak/nie)", "tak" if default else "nie")
        return response.lower() in ['tak', 't', 'yes', 'y', '1']
    
    # ========================================================================
    # P0: PASEK RYZYKA - ZAWSZE WIDOCZNY
    # ========================================================================
    
    def _get_risk_indicators(self) -> str:
        """Zwraca wizualne wskaźniki ryzyka"""
        if not self.game_state:
            return ""
        
        c = self.game_state.company
        risks = []
        
        # Runway
        runway = c.runway_months()
        if runway < 3:
            risks.append("🔴 RUNWAY: KRYTYCZNY!")
        elif runway < 6:
            risks.append("🟡 RUNWAY: NISKI")
        
        # SHA
        if self.config and self.config.has_partner and not self.game_state.agreement_signed:
            risks.append("🔴 SHA: BRAK UMOWY!")
        
        # Spółka
        if not c.registered and self.game_state.current_month > 3:
            risks.append("🟡 SPÓŁKA: NIEZAREJESTROWANA")
        
        # PMF
        if self.game_state.current_month > 6 and c.paying_customers < 5:
            risks.append("🟠 PMF: BRAK TRAKCJI")
        
        # MVP
        if not c.mvp_completed and self.game_state.current_month > 4:
            risks.append("🟡 MVP: NIEUKOŃCZONE")
        
        return " | ".join(risks) if risks else "✅ Brak krytycznych ryzyk"
    
    # ========================================================================
    # P0: PRIORYTET TERAZ - CO JEST NAJWAŻNIEJSZE
    # ========================================================================
    
    def _get_priority_action(self) -> Tuple[str, str, str]:
        """Zwraca (akcja, dlaczego, konsekwencja_braku)"""
        if not self.game_state:
            return ("", "", "")
        
        c = self.game_state.company
        month = self.game_state.current_month
        
        # Hierarchia priorytetów (od najważniejszego)
        
        # 1. Krytyczny runway
        if c.runway_months() < 3:
            return (
                "🚨 SZUKAJ FINANSOWANIA LUB KLIENTÓW",
                f"Masz mniej niż 3 miesiące runway ({c.runway_months()} mies)",
                f"Bez działania: BANKRUCTWO w ~{c.runway_months()} mies"
            )
        
        # 2. Brak SHA z partnerem
        if self.config and self.config.has_partner and not self.game_state.agreement_signed:
            return (
                "📝 PODPISZ SHA (umowę wspólników)",
                "Bez umowy partner może odejść z kodem/klientami",
                "Bez SHA: 40% startupów z konfliktami founderów upada"
            )
        
        # 3. Niezarejestrowana spółka
        if not c.registered and month > 2:
            return (
                "🏢 ZAREJESTRUJ SPÓŁKĘ",
                "Bez spółki nie możesz legalnie pozyskać inwestora",
                "Bez rejestracji: Brak ochrony prawnej, odpowiadasz osobiście"
            )
        
        # 4. Brak MVP
        if not c.mvp_completed:
            return (
                "🔧 DOKOŃCZ MVP",
                "Bez produktu nie zdobędziesz klientów",
                "Bez MVP: Spalisz gotówkę bez walidacji pomysłu"
            )
        
        # 5. Brak klientów po MVP
        if c.mvp_completed and c.paying_customers < 10:
            return (
                "🎯 ZDOBĄDŹ KLIENTÓW",
                "Klienci = walidacja + MRR",
                "Bez klientów: Brak dowodu PMF dla inwestorów"
            )
        
        # 6. Niski runway (ale nie krytyczny)
        if c.runway_months() < 6:
            return (
                "💰 WYDŁUŻ RUNWAY",
                f"Masz tylko {c.runway_months()} miesięcy runway",
                "Zalecane minimum to 6 miesięcy"
            )
        
        return (
            "📈 ROZWIJAJ BIZNES",
            "Masz podstawy, teraz skaluj",
            ""
        )
    
    def _show_priority_box(self):
        """Pokazuje najważniejszą akcję do wykonania"""
        action, why, consequence = self._get_priority_action()
        
        if not action:
            return
        
        print(colored("\n╔══════════════════════════════════════════════════════╗", Colors.YELLOW))
        print(colored("║  🎯 PRIORYTET TERAZ", Colors.BOLD))
        print(colored("╠══════════════════════════════════════════════════════╣", Colors.YELLOW))
        print(f"║  {colored(action, Colors.GREEN)}")
        print(f"║  ")
        print(f"║  📖 DLACZEGO: {why}")
        if consequence:
            print(f"║  ⚠️  RYZYKO: {colored(consequence, Colors.RED)}")
        print(colored("╚══════════════════════════════════════════════════════╝", Colors.YELLOW))
    
    # ========================================================================
    # P0: OSTRZEŻENIA PRZED PROBLEMAMI
    # ========================================================================
    
    def _check_warnings_before_month(self) -> List[Dict]:
        """Sprawdza i zwraca ostrzeżenia przed przejściem do następnego miesiąca"""
        if not self.game_state:
            return []
        
        warnings = []
        c = self.game_state.company
        month = self.game_state.current_month
        
        # Przewidywany runway po następnym miesiącu
        net_burn = c.monthly_burn_rate - c.mrr
        projected_cash = c.cash_on_hand - net_burn
        
        if projected_cash < 0:
            warnings.append({
                "level": "CRITICAL",
                "title": "BANKRUCTWO ZA 1 MIESIĄC",
                "message": f"Po tym miesiącu: {projected_cash:,.0f} PLN",
                "action": "Natychmiast szukaj finansowania lub obetnij koszty"
            })
        elif c.runway_months() <= 3:
            warnings.append({
                "level": "HIGH",
                "title": "NISKI RUNWAY",
                "message": f"Pozostało tylko {c.runway_months()} miesięcy",
                "action": "Zacznij szukać inwestora lub klientów"
            })
        
        # Konflikt partnerski
        if self.config and self.config.has_partner and not self.game_state.agreement_signed:
            if month >= 3:
                warnings.append({
                    "level": "HIGH",
                    "title": "RYZYKO KONFLIKTU",
                    "message": f"{month}+ miesiące bez SHA = rosnące ryzyko sporów",
                    "action": "Podpisz umowę wspólników ASAP"
                })
        
        # PMF
        if month >= 6 and c.paying_customers < 5:
            warnings.append({
                "level": "MEDIUM",
                "title": "BRAK PRODUCT-MARKET FIT",
                "message": f"Po {month} mies. masz tylko {c.paying_customers} klientów",
                "action": "Rozważ pivot lub intensywną sprzedaż"
            })
        
        # MVP nieukończone
        if not c.mvp_completed and month >= 4:
            warnings.append({
                "level": "MEDIUM",
                "title": "MVP OPÓŹNIONE",
                "message": f"Po {month} miesiącach MVP wciąż w {self.game_state.mvp_progress}%",
                "action": "Skup się na ukończeniu MVP"
            })
        
        return warnings
    
    def _show_warnings(self, warnings: List[Dict]) -> bool:
        """Wyświetla ostrzeżenia przed miesiącem. Zwraca False jeśli użytkownik anuluje."""
        if not warnings:
            return True
        
        print(colored("\n⚠️════════ OSTRZEŻENIA ════════⚠️", Colors.RED))
        
        for w in warnings:
            if w["level"] == "CRITICAL":
                color = Colors.RED
                icon = "🔴"
            elif w["level"] == "HIGH":
                color = Colors.YELLOW
                icon = "🟡"
            else:
                color = Colors.CYAN
                icon = "🟠"
            
            print(colored(f"\n{icon} {w['title']}", color + Colors.BOLD))
            print(f"   {w['message']}")
            print(colored(f"   → Zalecenie: {w['action']}", Colors.CYAN))
        
        print(colored("\n════════════════════════════════", Colors.RED))
        
        if any(w["level"] == "CRITICAL" for w in warnings):
            if not self._ask_yes_no("Czy na pewno chcesz kontynuować?", False):
                return False
        return True
    
    # ========================================================================
    # P1: SZCZEGÓŁOWY FEEDBACK PO AKCJI
    # ========================================================================
    
    def _show_action_result(self, action: GameAction, success: bool, 
                            before_state: Dict, after_state: Dict, message: str):
        """Pokazuje szczegółowy raport z konsekwencjami"""
        
        result_color = Colors.GREEN if success else Colors.RED
        print(colored(f"\n┌─── REZULTAT AKCJI {'─'*40}┐", result_color))
        print(f"│ {'✅' if success else '❌'} {action.name}")
        print(f"│ {message}")
        print(colored(f"├{'─'*55}┤", Colors.CYAN))
        
        # CO SIĘ ZMIENIŁO
        print(colored("│ 📊 ZMIANY:", Colors.BOLD))
        
        changes = []
        if before_state.get('cash') != after_state.get('cash'):
            diff = after_state['cash'] - before_state['cash']
            color = Colors.GREEN if diff > 0 else Colors.RED
            after_cash = after_state['cash']
            changes.append(f"   Gotówka: {before_state['cash']:,.0f} → {colored(f'{after_cash:,.0f}', color)} PLN ({diff:+,.0f})")
        
        if before_state.get('mrr') != after_state.get('mrr'):
            diff = after_state['mrr'] - before_state['mrr']
            color = Colors.GREEN if diff > 0 else Colors.RED
            after_mrr = after_state['mrr']
            changes.append(f"   MRR: {before_state['mrr']:,.0f} → {colored(f'{after_mrr:,.0f}', color)} PLN ({diff:+,.0f})")
        
        if before_state.get('customers') != after_state.get('customers'):
            diff = after_state['customers'] - before_state['customers']
            color = Colors.GREEN if diff > 0 else Colors.RED
            changes.append(f"   Klienci: {before_state['customers']} → {colored(str(after_state['customers']), color)} ({diff:+d})")
        
        if before_state.get('registered') != after_state.get('registered') and after_state.get('registered'):
            changes.append(f"   Spółka: ✗ → {colored('✓ ZAREJESTROWANA', Colors.GREEN)}")
        
        if before_state.get('agreement_signed') != after_state.get('agreement_signed') and after_state.get('agreement_signed'):
            changes.append(f"   SHA: ✗ → {colored('✓ PODPISANA', Colors.GREEN)}")
        
        if before_state.get('mvp_progress') != after_state.get('mvp_progress'):
            diff = after_state['mvp_progress'] - before_state['mvp_progress']
            after_mvp = after_state['mvp_progress']
            changes.append(f"   MVP: {before_state['mvp_progress']}% → {colored(f'{after_mvp}%', Colors.GREEN)} (+{diff}%)")
        
        if before_state.get('burn') != after_state.get('burn'):
            diff = after_state['burn'] - before_state['burn']
            color = Colors.RED if diff > 0 else Colors.GREEN
            after_burn = after_state['burn']
            changes.append(f"   Burn: {before_state['burn']:,.0f} → {colored(f'{after_burn:,.0f}', color)} PLN/mies")
        
        for change in changes:
            print(f"│ {change}")
        
        if not changes:
            print("│    Brak bezpośrednich zmian")
        
        # CO TO OZNACZA - kontekstowe wyjaśnienie
        print(colored("│", Colors.CYAN))
        print(colored("│ 💡 CO TO OZNACZA:", Colors.BOLD))
        
        if action.id == "register_company":
            print("│    • Możesz teraz legalnie wystawiać faktury")
            print("│    • Twój majątek osobisty jest chroniony")
            print("│    • Możesz rozmawiać z inwestorami")
            print(colored("│    ⚠️ PAMIĘTAJ: Od teraz masz obowiązki księgowe!", Colors.YELLOW))
        elif action.id == "sign_agreement":
            print("│    • Masz jasne zasady podziału equity")
            print("│    • Vesting chroni przed odejściem partnera")
            print("│    • Możesz bezpiecznie szukać inwestora")
            print(colored("│    ✓ BRAWO: To kluczowa decyzja dla stabilności!", Colors.GREEN))
        elif action.id == "develop_mvp":
            if after_state.get('mvp_progress', 0) >= 100:
                print("│    • 🎉 MVP UKOŃCZONE! Możesz szukać klientów")
                print("│    • Twój produkt jest gotowy do testów rynkowych")
            else:
                remaining = 100 - after_state.get('mvp_progress', 0)
                print(f"│    • Pozostało ~{remaining}% do ukończenia MVP")
                print(f"│    • Szacunkowo {max(1, remaining // 25)} miesiące do końca")
        elif action.id == "find_customers":
            print(f"│    • Nowy MRR = recurring revenue")
            print(f"│    • Każdy klient to dowód PMF")
            if after_state.get('customers', 0) >= 10:
                print(colored("│    ✓ Masz 10+ klientów - solidna podstawa do rundy!", Colors.GREEN))
        elif action.id == "hire_employee":
            new_runway = after_state.get('runway', 0)
            print(f"│    • Burn wzrósł, runway teraz: {new_runway} mies")
            print("│    • Nowy pracownik = szybszy rozwój")
            if new_runway < 6:
                print(colored("│    ⚠️ UWAGA: Runway poniżej 6 mies!", Colors.RED))
        
        # NASTĘPNY KROK
        print(colored("│", Colors.CYAN))
        next_action, why, _ = self._get_priority_action()
        print(colored(f"│ 👉 NASTĘPNY PRIORYTET: {next_action}", Colors.GREEN))
        
        print(colored(f"└{'─'*55}┘", Colors.CYAN))
    
    def _get_state_snapshot(self) -> Dict:
        """Zwraca snapshot aktualnego stanu gry"""
        c = self.game_state.company
        return {
            'cash': c.cash_on_hand,
            'mrr': c.mrr,
            'customers': c.paying_customers,
            'registered': c.registered,
            'agreement_signed': self.game_state.agreement_signed,
            'mvp_progress': self.game_state.mvp_progress,
            'mvp_completed': c.mvp_completed,
            'burn': c.monthly_burn_rate,
            'runway': c.runway_months()
        }
    
    # ========================================================================
    # P1: TABELA POSTĘPU VS CEL
    # ========================================================================
    
    def _show_progress_comparison(self):
        """Pokazuje gdzie jesteś vs gdzie chcesz być"""
        if not self.game_state or not self.config:
            return
        
        c = self.game_state.company
        month = self.game_state.current_month
        
        target_mrr = self.config.target_mrr_12_months
        target_customers = self.config.target_customers_12_months
        
        # Oblicz oczekiwany postęp (liniowy)
        expected_mrr = (target_mrr / 12) * month
        expected_customers = (target_customers / 12) * month
        
        print("\n### 📊 Postęp vs Cel (12 mies.)\n")
        print("| Metryka | Teraz | Oczekiwane | Cel | Status |")
        print("|---------|------:|----------:|----:|:------:|")
        
        # MRR
        mrr_status = "🟢" if c.mrr >= expected_mrr else "🟡" if c.mrr >= expected_mrr * 0.5 else "🔴"
        print(f"| MRR | {c.mrr:,.0f} | {expected_mrr:,.0f} | {target_mrr:,.0f} | {mrr_status} |")
        
        # Klienci
        cust_status = "🟢" if c.paying_customers >= expected_customers else "🟡" if c.paying_customers >= expected_customers * 0.5 else "🔴"
        print(f"| Klienci | {c.paying_customers} | {expected_customers:.0f} | {target_customers} | {cust_status} |")
        
        # Progress bar wizualny
        mrr_pct = min(100, (c.mrr / target_mrr) * 100) if target_mrr > 0 else 0
        cust_pct = min(100, (c.paying_customers / target_customers) * 100) if target_customers > 0 else 0
        
        print(f"\n📈 MRR:     [{'█' * int(mrr_pct/5)}{'░' * (20-int(mrr_pct/5))}] {mrr_pct:.0f}%")
        print(f"👥 Klienci: [{'█' * int(cust_pct/5)}{'░' * (20-int(cust_pct/5))}] {cust_pct:.0f}%")
        
        # Prognoza
        if month > 0 and c.mrr > 0:
            monthly_mrr_growth = c.mrr / month
            projected_mrr_12 = monthly_mrr_growth * 12
            print(f"\n📊 Prognoza MRR w mies. 12: {projected_mrr_12:,.0f} PLN ", end="")
            if projected_mrr_12 >= target_mrr:
                print(colored("(cel osiągalny!)", Colors.GREEN))
            else:
                print(colored(f"(brakuje {target_mrr - projected_mrr_12:,.0f} PLN)", Colors.YELLOW))
    
    # ========================================================================
    # P2: TRYB MENTOR - PODPOWIEDZI EDUKACYJNE
    # ========================================================================
    
    def _mentor_tip(self, topic: str):
        """Pokazuje edukacyjną podpowiedź dla danego tematu"""
        if not getattr(self, 'mentor_mode', True):
            return
        
        tips = {
            "runway": """
💡 MENTOR: RUNWAY
Runway to ile miesięcy przetrwasz przy obecnym burn rate.
Formuła: Gotówka / (Burn - MRR)
ZASADA: Zawsze utrzymuj min. 6 miesięcy runway!
Jeśli masz mniej - natychmiast szukaj finansowania lub klientów.""",
            
            "sha": """
💡 MENTOR: SHA (Umowa Wspólników)
To dokument OBOWIĄZKOWY gdy masz partnera.
Określa: podział equity, vesting, good/bad leaver, decyzje.
ZASADA: Podpisz PRZED wspólną pracą!
Koszt: 3-8k PLN u prawnika, ale oszczędza miliony w sporach.""",
            
            "vesting": """
💡 MENTOR: VESTING
Stopniowe nabywanie udziałów w czasie (zwykle 48 mies).
CLIFF: Pierwsze 12 mies. bez equity, potem 25% od razu.
ZASADA: Chroni przed partnerem który odejdzie po 2 mies z equity.""",
            
            "pmf": """
💡 MENTOR: PRODUCT-MARKET FIT (PMF)
Moment gdy klienci CHCĄ Twojego produktu.
Wskaźniki: >40% "bardzo rozczarowanych" przy utracie, organiczny wzrost.
ZASADA: Bez PMF nie skaluj - najpierw znajdź dopasowanie.""",
            
            "burn": """
💡 MENTOR: BURN RATE
Ile pieniędzy wydajesz miesięcznie.
Net burn = Koszty - Przychody (MRR).
ZASADA: Trzymaj burn niski dopóki nie masz PMF.
Lepiej wolniej rosnąć niż szybko upaść.""",
            
            "mrr": """
💡 MENTOR: MRR (Monthly Recurring Revenue)
Powtarzalny przychód miesięczny - kluczowa metryka SaaS.
Inwestorzy patrzą na: wzrost MoM, churn, LTV/CAC.
ZASADA: MRR > Burn = zyskowność operacyjna.""",
            
            "dilution": """
💡 MENTOR: ROZWODNIENIE (Dilution)
Przy każdej rundzie Twój % equity maleje.
Przykład: Masz 50%, inwestor bierze 20% → zostajesz z 40%.
ZASADA: Lepiej mieć 10% firmy wartej 100M niż 100% wartej 0."""
        }
        
        if topic in tips:
            print(colored(tips[topic], Colors.CYAN))
    
    # ========================================================================
    # P2: RAPORT MIESIĘCZNY
    # ========================================================================
    
    def _show_monthly_report(self):
        """Raport zarządczy po każdym miesiącu"""
        if not self.game_state:
            return
        
        c = self.game_state.company
        month = self.game_state.current_month
        
        print(f"\n## 📋 RAPORT MIESIĘCZNY - Miesiąc {month}\n")
        
        # KPI
        print("### Kluczowe wskaźniki\n")
        print("| KPI | Wartość | Status |")
        print("|-----|--------:|:------:|")
        
        # Runway
        runway = c.runway_months()
        runway_status = "🟢" if runway > 6 else "🟡" if runway > 3 else "🔴"
        print(f"| ⏱️ Runway | {runway} mies | {runway_status} |")
        
        # MRR
        mrr_status = "🟢" if c.mrr > 5000 else "🟡" if c.mrr > 0 else "🔴"
        print(f"| 📈 MRR | {c.mrr:,.0f} PLN | {mrr_status} |")
        
        # Klienci
        cust_status = "🟢" if c.paying_customers >= 10 else "🟡" if c.paying_customers > 0 else "🔴"
        print(f"| 👥 Klienci | {c.paying_customers} | {cust_status} |")
        
        # Gotówka
        cash_status = "🟢" if c.cash_on_hand > 50000 else "🟡" if c.cash_on_hand > 10000 else "🔴"
        print(f"| 💰 Gotówka | {c.cash_on_hand:,.0f} PLN | {cash_status} |")
        
        # Health check
        print("\n### Health Check\n")
        health_items = [
            ("💰 Runway", f"{runway} mies", "🟢" if runway > 6 else "🟡" if runway > 3 else "🔴"),
            ("📝 SHA", "✓" if self.game_state.agreement_signed else "✗", "🟢" if self.game_state.agreement_signed or not (self.config and self.config.has_partner) else "🔴"),
            ("🏢 Spółka", "✓" if c.registered else "✗", "🟢" if c.registered else "🟡"),
            ("🔧 MVP", "✓" if c.mvp_completed else f"{self.game_state.mvp_progress}%", "🟢" if c.mvp_completed else "🟡"),
        ]
        
        print("| Element | Status | |")
        print("|---------|:------:|:-:|")
        for name, value, status in health_items:
            print(f"| {name} | {value} | {status} |")
        
        # P&L
        profit = c.mrr - c.monthly_burn_rate
        print(f"\n### Miesięczny P&L")
        print(f"| Pozycja | Kwota |")
        print(f"|---------|------:|")
        print(f"| Przychody (MRR) | {c.mrr:,.0f} PLN |")
        print(f"| Koszty (burn) | {c.monthly_burn_rate:,.0f} PLN |")
        color = Colors.GREEN if profit >= 0 else Colors.RED
        print(f"| **WYNIK** | {colored(f'{profit:+,.0f} PLN', color)} |")
        
        # Zalecenia
        print(colored("\n### Zalecenia na następny miesiąc\n", Colors.HEADER))
        action, why, _ = self._get_priority_action()
        print(f"🎯 **PRIORYTET:** {action}")
        print(f"   *{why}*")
    
    # ========================================================================
    # P2: HISTORIA Z ANALIZĄ
    # ========================================================================
    
    def _analyze_history(self):
        """Analiza historii decyzji"""
        if not self.action_history:
            return
        
        print(colored("\n### 📚 ANALIZA DECYZJI\n", Colors.HEADER))
        
        # Dobre decyzje
        good = []
        bad = []
        
        for entry in self.action_history:
            if entry.get('type') == 'action':
                effects_str = ' '.join(entry.get('effects', []))
                if 'SHA podpisana' in effects_str or 'agreement' in entry.get('name', '').lower():
                    good.append(("Podpisanie SHA", "Ochrona przed konfliktami"))
                if 'zarejestrowana' in effects_str.lower():
                    good.append(("Rejestracja spółki", "Ochrona prawna"))
                if 'MVP' in effects_str and 'UKOŃCZONE' in effects_str:
                    good.append(("Ukończenie MVP", "Gotowość do sprzedaży"))
            
            if entry.get('type') == 'event':
                if 'Konflikt' in entry.get('name', ''):
                    if self.game_state and not self.game_state.agreement_signed:
                        bad.append(("Brak SHA przy konflikcie", "Konflikt można było ograniczyć umową"))
        
        if good:
            print(colored("✅ DOBRE DECYZJE:", Colors.GREEN))
            for name, why in good:
                print(f"   • {name} - {why}")
        
        if bad:
            print(colored("\n❌ BŁĘDY DO UNIKNIĘCIA:", Colors.RED))
            for name, lesson in bad:
                print(f"   • {name} - {lesson}")
        
        # Statystyki
        print(colored("\n📊 STATYSTYKI:", Colors.CYAN))
        actions_count = len([e for e in self.action_history if e.get('type') == 'action'])
        events_count = len([e for e in self.action_history if e.get('type') == 'event'])
        print(f"   Wykonane akcje: {actions_count}")
        print(f"   Zdarzenia losowe: {events_count}")
    
    def do_pomoc(self, arg):
        """Wyświetla pomoc"""
        help_text = [
            f"{colored('start', Colors.GREEN)}      - Rozpocznij nową grę",
            f"{colored('wczytaj', Colors.GREEN)}    - Wczytaj zapisaną grę",
            f"{colored('status', Colors.GREEN)}     - Stan firmy",
            f"{colored('miesiac', Colors.GREEN)}    - Następny miesiąc + akcje",
            f"{colored('akcje', Colors.GREEN)}      - Dostępne akcje",
            f"{colored('historia', Colors.GREEN)}   - Historia decyzji z analizą",
            f"{colored('postep', Colors.GREEN)}     - Postęp vs cele",
            f"{colored('raport', Colors.GREEN)}     - Raport miesięczny",
            "",
            f"{colored('finanse', Colors.GREEN)}    - Szczegóły finansowe",
            f"{colored('portfele', Colors.GREEN)}   - Portfele wspólników + biznes",
            f"{colored('equity', Colors.GREEN)}     - Podział udziałów",
            f"{colored('ryzyko', Colors.GREEN)}     - Analiza ryzyka",
            "",
            f"{colored('nauka', Colors.GREEN)}      - Materiały edukacyjne",
            f"{colored('slownik', Colors.GREEN)}    - Słownik pojęć",
            "",
            f"{colored('zapisz', Colors.GREEN)}     - Zapisz grę",
            f"{colored('wyjscie', Colors.GREEN)}    - Zakończ"
        ]
        print_box("POMOC", help_text)
    
    def do_help(self, arg):
        self.do_pomoc(arg)
    
    def do_wyjscie(self, arg):
        """Wyjście z gry"""
        if self.game_state and self._ask_yes_no("Zapisać grę?"):
            self.do_zapisz("")
        print(colored("\nDo zobaczenia!", Colors.CYAN))
        return True
    
    def do_exit(self, arg):
        return self.do_wyjscie(arg)
    
    def do_quit(self, arg):
        return self.do_wyjscie(arg)
    
    def do_start(self, arg):
        """Rozpoczyna nową grę"""
        print(colored("\n" + "═"*60, Colors.CYAN))
        print(colored("  NOWA GRA - Konfiguracja", Colors.BOLD))
        print(colored("═"*60 + "\n", Colors.CYAN))
        
        self.config = PlayerConfig()
        
        # ETAP 1: Gracz
        print(colored("ETAP 1/6: Twoje dane", Colors.HEADER))
        self.config.player_name = self._ask("Twoje imię", "Founder")
        
        print("\nTwoja rola?")
        print(f"  {colored('1', Colors.GREEN)}. Technical (programista)")
        print(f"     → {colored('Konsekwencja:', Colors.YELLOW)} Twój czas = wartość MVP")
        print(f"  {colored('2', Colors.GREEN)}. Business (sprzedaż)")
        print(f"     → {colored('Konsekwencja:', Colors.YELLOW)} Potrzebujesz technicznego co-foundera")
        
        role_idx = self._ask_choice("", ["Technical", "Business"])
        self.config.player_role = "technical" if role_idx == 0 else "business"
        
        # ETAP 2: MVP
        print(colored("\n\nETAP 2/6: MVP", Colors.HEADER))
        has_mvp = self._ask_yes_no("Masz już MVP/prototyp?", False)
        self.config.player_has_mvp = has_mvp
        
        if has_mvp:
            hours = self._ask_number("Godziny na MVP", 10, 5000, 200)
            rate = self._ask_number("Stawka PLN/h", 50, 500, 120)
            external = self._ask_number("Koszty zewnętrzne", 0, 100000, 0)
            self.config.mvp_hours = int(hours)
            self.config.mvp_hourly_rate = rate
            self.config.mvp_external_costs = external
            self.config.mvp_calculated_value = hours * rate + external
            print(colored(f"\n✓ Wartość MVP: {self.config.mvp_calculated_value:,.0f} PLN", Colors.GREEN))
            print(colored("💡 MVP daje przewagę - rekomendacja: 55-70% equity", Colors.YELLOW))
        else:
            self.config.mvp_calculated_value = 0
            print(colored("💡 Bez MVP zaczynasz od zera. Priorytet: zbuduj prototyp.", Colors.YELLOW))
        
        # ETAP 3: Partnerzy (wspólnicy)
        print(colored("\n\nETAP 3/6: Wspólnicy", Colors.HEADER))
        has_partner = self._ask_yes_no("Masz partnera/co-foundera?", False)
        self.config.has_partner = has_partner
        
        # Lista partnerów do obsługi wielu wspólników
        self.partners_data = []
        
        if has_partner:
            partner_num = 1
            adding_partners = True
            
            while adding_partners:
                print(colored(f"\n{'─'*40}", Colors.CYAN))
                print(colored(f"  👤 WSPÓLNIK #{partner_num}", Colors.HEADER))
                print(colored("─"*40, Colors.CYAN))
                
                partner = {
                    'name': self._ask(f"Imię wspólnika #{partner_num}", f"Partner{partner_num}"),
                    'role': 'business' if self.config.player_role == 'technical' else 'technical',
                    'capital': 0,
                    'experience_years': 0,
                    'contacts_count': 0,
                    'krs_verified': False,
                    'debts_verified': False
                }
                
                print(colored("\n  🔍 WERYFIKACJA:", Colors.YELLOW))
                partner['krs_verified'] = self._ask_yes_no("  Sprawdziłeś w KRS?", False)
                if not partner['krs_verified']:
                    print(colored("     ⚠️ RYZYKO: Możesz nie wiedzieć o upadłościach!", Colors.RED))
                
                partner['debts_verified'] = self._ask_yes_no("  Sprawdziłeś rejestry dłużników?", False)
                if not partner['debts_verified']:
                    print(colored("     ⚠️ RYZYKO: Partner może mieć długi!", Colors.RED))
                
                partner['capital'] = self._ask_number("  Kapitał wnoszony (PLN)", 0, 1000000, 0)
                partner['experience_years'] = int(self._ask_number("  Doświadczenie (lata)", 0, 30, 0))
                
                has_contacts = self._ask_yes_no("  Ma klientów/kontakty?", False)
                if has_contacts:
                    partner['contacts_count'] = int(self._ask_number("  Ile kontaktów/leadów wnosi?", 1, 500, 10))
                    print(colored(f"     ✓ Wnosi {partner['contacts_count']} potencjalnych kontaktów", Colors.GREEN))
                
                self.partners_data.append(partner)
                
                # Podsumowanie wspólnika
                print(colored(f"\n  ✓ Dodano: {partner['name']}", Colors.GREEN))
                print(f"     Kapitał: {partner['capital']:,.0f} PLN")
                print(f"     Doświadczenie: {partner['experience_years']} lat")
                print(f"     Kontakty: {partner['contacts_count']}")
                
                partner_num += 1
                if partner_num <= 4:  # Max 4 wspólników
                    adding_partners = self._ask_yes_no("\n  Dodać kolejnego wspólnika?", False)
                else:
                    print(colored("\n  ℹ️ Maksymalna liczba wspólników: 4", Colors.YELLOW))
                    adding_partners = False
            
            # Zachowaj kompatybilność z pojedynczym partnerem
            if self.partners_data:
                first = self.partners_data[0]
                self.config.partner_name = first['name']
                self.config.partner_capital = first['capital']
                self.config.partner_experience_years = first['experience_years']
                self.config.partner_contacts_count = first['contacts_count']
                self.config.partner_krs_verified = first['krs_verified']
                self.config.partner_debts_verified = first['debts_verified']
                self.config.partner_has_customers = first['contacts_count'] > 0
            
            # Equity - kalkulacja i uzasadnienie dla wielu wspólników
            print(colored("\n" + "─"*60, Colors.CYAN))
            print(colored("  📊 REKOMENDACJA PODZIAŁU EQUITY", Colors.HEADER))
            print(colored("─"*60, Colors.CYAN))
            
            num_partners = len(self.partners_data)
            total_founders = num_partners + 1  # +1 dla gracza
            
            # Bazowy podział równy
            esop = 10
            available = 100 - esop
            base_share = available / total_founders
            
            player_base = base_share
            partner_shares = {p['name']: base_share for p in self.partners_data}
            reasons = []
            
            print(colored("\n  📖 ZASADA WYJŚCIOWA:", Colors.BOLD))
            print(f"     {total_founders} founderów → {base_share:.0f}% każdy jako baza")
            print(f"     (po odjęciu {esop}% ESOP)\n")
            
            print(colored("  📈 MODYFIKATORY:", Colors.BOLD))
            
            # Bonus za MVP dla gracza
            if self.config.mvp_calculated_value > 0:
                mvp_bonus = min(15, self.config.mvp_calculated_value / 5000)
                player_base += mvp_bonus
                # Odejmij proporcjonalnie od partnerów
                per_partner_penalty = mvp_bonus / num_partners
                for name in partner_shares:
                    partner_shares[name] -= per_partner_penalty
                print(f"     • MVP ({self.config.mvp_calculated_value:,.0f} PLN): +{mvp_bonus:.0f}% dla Ciebie")
                reasons.append(f"Twój MVP wart {self.config.mvp_calculated_value:,.0f} PLN")
            
            # Bonusy dla partnerów
            for p in self.partners_data:
                name = p['name']
                
                if p['capital'] > 0:
                    cap_bonus = min(10, p['capital'] / 5000)
                    partner_shares[name] += cap_bonus
                    player_base -= cap_bonus / num_partners
                    print(f"     • {name} - kapitał ({p['capital']:,.0f} PLN): +{cap_bonus:.0f}%")
                    reasons.append(f"{name} wnosi {p['capital']:,.0f} PLN")
                
                if p['contacts_count'] > 0:
                    contacts_bonus = min(8, p['contacts_count'] / 5)
                    partner_shares[name] += contacts_bonus
                    player_base -= contacts_bonus / num_partners
                    print(f"     • {name} - kontakty ({p['contacts_count']}): +{contacts_bonus:.0f}%")
                    reasons.append(f"{name} ma {p['contacts_count']} kontaktów")
                
                if p['experience_years'] > 5:
                    exp_bonus = min(5, p['experience_years'] / 4)
                    partner_shares[name] += exp_bonus
                    player_base -= exp_bonus / num_partners
                    print(f"     • {name} - doświadczenie ({p['experience_years']} lat): +{exp_bonus:.0f}%")
            
            # Wyjaśnienie ESOP
            print(colored("\n  💡 CO TO JEST ESOP?", Colors.BOLD))
            print("     Employee Stock Option Pool - pula udziałów dla przyszłych")
            print("     pracowników. Standard: 10-15%. Motywuje zespół i jest")
            print("     wymagany przez większość inwestorów VC.")
            
            # Podsumowanie
            print(colored("\n  ══════════════════════════════════════", Colors.CYAN))
            print(colored("  PROPONOWANY PODZIAŁ:", Colors.BOLD))
            print(colored("  ══════════════════════════════════════", Colors.CYAN))
            
            print(colored(f"\n     👤 Ty ({self.config.player_name}): {player_base:.0f}%", Colors.GREEN))
            total_partners_equity = 0
            for p in self.partners_data:
                share = partner_shares[p['name']]
                total_partners_equity += share
                verified = "✓" if p['krs_verified'] and p['debts_verified'] else "⚠️"
                print(f"     👥 {p['name']}: {share:.0f}% {verified}")
            print(colored(f"     🎁 ESOP (pracownicy): {esop}%", Colors.YELLOW))
            print(f"     ─────────────────────────────")
            total = player_base + total_partners_equity + esop
            print(f"     Σ  RAZEM: {total:.0f}%")
            
            if reasons:
                print(colored("\n  📋 UZASADNIENIE:", Colors.BOLD))
                for r in reasons:
                    print(f"     • {r}")
            
            # Zapisz wartości
            self.config.player_equity = player_base
            self.config.partner_equity = total_partners_equity
            self.config.esop_pool = esop
            
            # Przypisz equity do partnerów
            for i, p in enumerate(self.partners_data):
                p['equity'] = partner_shares[p['name']]
            
            print("")
            if not self._ask_yes_no("Akceptujesz ten podział?", True):
                print(colored("\n  Wprowadź własny podział:", Colors.YELLOW))
                self.config.player_equity = self._ask_number("Twój udział %", 1, 95, player_base)
                remaining = 100 - self.config.player_equity - esop
                for p in self.partners_data:
                    suggested = remaining / len(self.partners_data)
                    p['equity'] = self._ask_number(f"Udział {p['name']} %", 1, 90, suggested)
                    remaining -= p['equity']
                self.config.partner_equity = sum(p['equity'] for p in self.partners_data)
                self.config.esop_pool = 100 - self.config.player_equity - self.config.partner_equity
                print(colored(f"     ESOP: {self.config.esop_pool:.0f}%", Colors.DIM))
        else:
            self.config.player_equity = 90
            self.config.partner_equity = 0
            self.config.esop_pool = 10
            print(colored("💡 Solo founding jest trudniejsze, ale możliwe.", Colors.CYAN))
        
        # ETAP 4: Forma prawna
        print(colored("\n\nETAP 4/6: Forma prawna", Colors.HEADER))
        print(colored("\n  1. PSA - ZALECANA dla startupów", Colors.GREEN))
        print("     ✓ Kapitał: 1 PLN, praca jako wkład, łatwy transfer")
        print(colored("\n  2. Sp. z o.o.", Colors.CYAN))
        print("     ✓ Ugruntowana forma, ✗ kapitał min 5000 PLN")
        
        choice = self._ask_choice("Wybierz:", ["PSA", "Sp. z o.o."])
        self.config.legal_form = "psa" if choice == 0 else "sp_zoo"
        
        # ETAP 5: Zasoby
        print(colored("\n\nETAP 5/6: Zasoby", Colors.HEADER))
        self.config.initial_cash = self._ask_number("Gotówka na start (PLN)", 0, 500000, 10000)
        self.config.monthly_burn = self._ask_number("Burn rate (PLN/mies)", 1000, 100000, 5000)
        
        runway = self.config.initial_cash / self.config.monthly_burn if self.config.monthly_burn > 0 else 0
        runway_color = Colors.RED if runway < 6 else Colors.YELLOW if runway < 12 else Colors.GREEN
        print(colored(f"\n📊 Runway: {runway:.1f} miesięcy", runway_color))
        
        # ETAP 6: Cele
        print(colored("\n\nETAP 6/6: Cele (12 mies)", Colors.HEADER))
        self.config.target_mrr_12_months = self._ask_number("Docelowy MRR (PLN)", 1000, 500000, 10000)
        self.config.target_customers_12_months = int(self._ask_number("Docelowi klienci", 1, 10000, 50))
        
        # Inicjalizacja
        self._initialize_game()
        self._show_initial_summary()
    
    def _initialize_game(self):
        """Inicjalizuje stan gry"""
        self.game_state = GameState(
            player_name=self.config.player_name,
            player_role=self.config.player_role
        )
        
        company = Company(name=f"{self.config.player_name}'s Startup")
        company.legal_form = LegalForm.PSA if self.config.legal_form == "psa" else LegalForm.SP_ZOO
        company.cash_on_hand = self.config.initial_cash
        company.monthly_burn_rate = self.config.monthly_burn
        company.esop_pool_percentage = self.config.esop_pool
        company.mvp_completed = self.config.player_has_mvp
        
        player = Founder(
            name=self.config.player_name,
            role=self.config.player_role,
            equity_percentage=self.config.player_equity,
            brought_mvp=self.config.player_has_mvp,
            mvp_value=self.config.mvp_calculated_value,
            is_player=True
        )
        company.founders.append(player)
        
        if self.config.has_partner:
            # Obsługa wielu wspólników
            if hasattr(self, 'partners_data') and self.partners_data:
                for p in self.partners_data:
                    partner = Founder(
                        name=p['name'],
                        role=p.get('role', 'business' if self.config.player_role == "technical" else "technical"),
                        equity_percentage=p.get('equity', self.config.partner_equity / len(self.partners_data)),
                        initial_investment=p['capital'],
                        personal_invested=p['capital'],
                        experience_years=p['experience_years'],
                        contacts_count=p['contacts_count'],
                        krs_verified=p['krs_verified'],
                        debtor_registry_verified=p['debts_verified'],
                        is_player=False
                    )
                    company.founders.append(partner)
            else:
                # Fallback dla pojedynczego partnera
                partner = Founder(
                    name=self.config.partner_name,
                    role="business" if self.config.player_role == "technical" else "technical",
                    equity_percentage=self.config.partner_equity,
                    initial_investment=self.config.partner_capital,
                    personal_invested=self.config.partner_capital,
                    experience_years=self.config.partner_experience_years,
                    contacts_count=self.config.partner_contacts_count if hasattr(self.config, 'partner_contacts_count') else 0,
                    krs_verified=self.config.partner_krs_verified,
                    debtor_registry_verified=self.config.partner_debts_verified,
                    is_player=False
                )
                company.founders.append(partner)
        
        self.game_state.company = company
        self.game_state.founders_agreement = FoundersAgreement()
        self.game_state.mvp_progress = 100 if self.config.player_has_mvp else 0
        self.action_system = ActionSystem(self.game_state, self.config)
    
    def _show_initial_summary(self):
        """Podsumowanie początkowe"""
        print(colored("\n" + "═"*60, Colors.GREEN))
        print(colored("  GRA ROZPOCZĘTA!", Colors.BOLD))
        print(colored("═"*60, Colors.GREEN))
        
        company = self.game_state.company
        
        # Priorytety
        if not company.registered:
            print(colored("\n   ⚠️ PRIORYTET: Zarejestruj spółkę!", Colors.RED))
        if self.config.has_partner and not self.game_state.agreement_signed:
            print(colored("   ⚠️ PRIORYTET: Podpisz umowę wspólników!", Colors.RED))
        
        # Pokaż menu gry
        self._show_game_menu()
    
    def do_miesiac(self, arg):
        """Następny miesiąc"""
        if not self.game_state:
            print(colored("Najpierw 'start'", Colors.RED))
            return
        
        # NOWE: Sprawdź ostrzeżenia PRZED przejściem do następnego miesiąca
        warnings = self._check_warnings_before_month()
        if warnings:
            if not self._show_warnings(warnings):
                print(colored("\n↩️ Anulowano. Wykonaj akcje aby poprawić sytuację.", Colors.YELLOW))
                self._show_game_menu()
                return
        
        self.game_state.current_month += 1
        self.actions_this_month = 0  # Reset licznika akcji
        month = self.game_state.current_month
        
        print(colored(f"\n{'═'*60}", Colors.CYAN))
        print(colored(f"  MIESIĄC {month}", Colors.BOLD))
        print(colored(f"{'═'*60}\n", Colors.CYAN))
        
        # Automatyczne zmiany
        company = self.game_state.company
        changes = []
        
        net_burn = company.monthly_burn_rate - company.mrr
        if net_burn > 0:
            company.cash_on_hand -= net_burn
            changes.append(f"💸 Burn: -{net_burn:,.0f} PLN")
        else:
            company.cash_on_hand -= net_burn
            changes.append(f"💰 Zysk: +{-net_burn:,.0f} PLN")

        # Zapisz do historii (miesięczny snapshot zmian)
        if changes:
            self.action_history.append({
                'month': month,
                'type': 'month',
                'name': 'Zmiany miesiąca',
                'effects': changes
            })
        
        if company.paying_customers > 0:
            growth = random.uniform(0.02, 0.08)
            new_cust = max(1, int(company.paying_customers * growth))
            avg_rev = company.mrr / company.paying_customers if company.paying_customers else 200
            company.total_customers += new_cust
            company.paying_customers += new_cust
            company.mrr += new_cust * avg_rev
            changes.append(f"📈 +{new_cust} klientów, MRR +{new_cust * avg_rev:,.0f}")
        
        if company.mrr > 0:
            company.current_valuation = company.mrr * 12 * 5
        
        # Vesting
        vesting = self.game_state.founders_agreement.vesting_schedule
        for founder in company.founders:
            founder.months_in_company = month
            if month >= vesting.cliff_months and not founder.cliff_completed:
                founder.cliff_completed = True
                cliff_amt = founder.equity_percentage * (vesting.cliff_percentage / 100)
                founder.vested_percentage = cliff_amt
                changes.append(f"🎉 {founder.name}: CLIFF! +{cliff_amt:.1f}% vested")
            elif founder.cliff_completed:
                rem_months = vesting.total_months - vesting.cliff_months
                rem_eq = founder.equity_percentage * (1 - vesting.cliff_percentage/100)
                monthly = rem_eq / rem_months if rem_months > 0 else 0
                founder.vested_percentage = min(founder.equity_percentage, founder.vested_percentage + monthly)
        
        if changes:
            print(colored("📊 ZMIANY:", Colors.CYAN))
            for c in changes:
                print(f"   {c}")
        
        # Sytuacja
        runway = company.runway_months()
        cash_color = Colors.GREEN if company.cash_on_hand > 50000 else Colors.YELLOW if company.cash_on_hand > 10000 else Colors.RED
        
        print(colored("\n📊 SYTUACJA:", Colors.HEADER))
        print(f"   Gotówka: {colored(f'{company.cash_on_hand:,.0f} PLN', cash_color)}")
        print(f"   MRR: {company.mrr:,.0f} PLN | Klienci: {company.paying_customers}")
        print(f"   Runway: {colored(f'{runway} mies', Colors.GREEN if runway > 6 else Colors.RED)}")
        
        # Losowe zdarzenie z konsekwencjami
        if random.random() < 0.4:
            event = self._generate_random_event()
            if event:
                self._apply_event(event)
        
        # Menu akcji
        self._show_action_menu()
        
        # Game over?
        if company.cash_on_hand < 0:
            print(colored("\n💀 GAME OVER - BANKRUCTWO", Colors.RED))
            self._show_lessons()
            self.game_state = None
        elif company.mrr >= self.config.target_mrr_12_months and company.total_customers >= self.config.target_customers_12_months:
            print(colored("\n🎉 SUKCES! Cele osiągnięte!", Colors.GREEN))
    
    def _show_action_menu(self):
        """Menu akcji"""
        if not self.action_system:
            return
        
        actions = self.action_system.get_available_actions()
        
        categories = {
            'legal': ('⚖️ PRAWNE', []),
            'financial': ('💰 FINANSOWE', []),
            'team': ('👥 ZESPÓŁ', []),
            'product': ('🔧 PRODUKT', []),
            'partner': ('🤝 PARTNER', []),
            'special': ('⚡ INNE', [])
        }
        
        for a in actions:
            if a.category in categories:
                categories[a.category][1].append(a)
        
        print(colored("\n" + "─"*60, Colors.CYAN))
        print(colored("  DOSTĘPNE AKCJE", Colors.BOLD))
        print(colored("─"*60, Colors.CYAN))
        
        action_list = []
        idx = 1
        
        for cat_id, (cat_name, cat_actions) in categories.items():
            if cat_actions:
                print(colored(f"\n{cat_name}:", Colors.HEADER))
                for a in cat_actions:
                    if a.available:
                        rec = colored(" [ZALECANE]", Colors.YELLOW) if a.recommended else ""
                        warn = colored(f" {a.warning}", Colors.RED) if a.warning else ""
                        print(f"  {colored(str(idx), Colors.GREEN)}. ✓ {a.name}{rec}{warn}")
                        print(f"     {colored(a.description, Colors.DIM)}")
                        action_list.append(a)
                        idx += 1
                    else:
                        print(f"  {colored('✗', Colors.RED)} {a.name} - {a.blocked_reason}")
        
        print(colored("\n" + "─"*60, Colors.CYAN))
        remaining = self.max_actions_per_month - self.actions_this_month
        print(colored(f"  Pozostało akcji w tym miesiącu: {remaining}", Colors.YELLOW))
        
        while self.actions_this_month < self.max_actions_per_month:
            choice = self._ask("Akcja (numer) lub 'pomiń'", "pomiń")
            
            if choice.lower() in ['pomiń', 'pomin', 'skip', '', 'p']:
                break
            
            try:
                action_idx = int(choice) - 1
                if 0 <= action_idx < len(action_list):
                    self._execute_action(action_list[action_idx])
                    remaining = self.max_actions_per_month - self.actions_this_month
                    if remaining > 0:
                        print(colored(f"\n  Pozostało akcji: {remaining}", Colors.YELLOW))
            except ValueError:
                pass
    
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
        
        if self._ask_yes_no("\nWykonać?", True):
            # P1: Zapisz stan PRZED akcją
            before_state = self._get_state_snapshot()
            
            success, msg, effects = self.action_system.execute_action(action.id)
            
            # P1: Zapisz stan PO akcji
            after_state = self._get_state_snapshot()
            
            # P1: Pokaż szczegółowy raport ze zmianami
            self._show_action_result(action, success, before_state, after_state, msg)
            
            # Pokaż portfele przy podpisaniu SHA
            if effects.get('show_portfele') and success:
                print(colored("\n📋 PODSUMOWANIE FINANSOWE PRZY PODPISANIU SHA:", Colors.HEADER))
                self.do_portfele("")
            
            # Zapisz do historii
            history_effects: List[str] = []
            if msg:
                history_effects.append(msg)
            if isinstance(effects, dict):
                if 'cash' in effects and isinstance(effects['cash'], (int, float)):
                    history_effects.append(f"Gotówka {effects['cash']:+,.0f} PLN")
                if 'mrr' in effects and isinstance(effects['mrr'], (int, float)):
                    history_effects.append(f"MRR {effects['mrr']:+,.0f} PLN")
                if 'burn' in effects and isinstance(effects['burn'], (int, float)):
                    history_effects.append(f"Burn {effects['burn']:+,.0f} PLN/mies")

            self.action_history.append({
                'month': self.game_state.current_month,
                'type': 'action',
                'name': action.name,
                'success': success,
                'effects': history_effects
            })
            self.actions_this_month += 1
    
    def _show_lessons(self):
        """Wnioski po przegranej"""
        print(colored("\n📚 WNIOSKI:", Colors.CYAN))
        if self.config.has_partner and not self.game_state.agreement_signed:
            print("   • Zawsze podpisuj umowę wspólników!")
        print("   • Pilnuj runway - min 6 miesięcy")
        print("   • Szukaj klientów ASAP")
    
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
        if self.config.has_partner and not self.game_state.agreement_signed and month > 3:
            events.append({
                'type': 'negative', 'name': '⚔️ Konflikt z partnerem',
                'desc': 'Spór o podział obowiązków i equity!',
                'effects': {'risk': 20},
                'warning': 'Podpisz SHA aby uniknąć!'
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
            company.monthly_burn_rate = max(0, company.monthly_burn_rate + effects['burn'])
            sign = '+' if effects['burn'] > 0 else ''
            changes.append(f"Burn {sign}{effects['burn']:,.0f}/mies")
        
        if changes:
            print(colored(f"   → Efekt: {', '.join(changes)}", Colors.YELLOW))
        
        if 'warning' in event:
            print(colored(f"   💡 {event['warning']}", Colors.CYAN))
        
        # Zapisz do historii
        self.action_history.append({
            'month': self.game_state.current_month,
            'type': 'event',
            'name': event['name'],
            'effects': changes
        })
    
    def do_historia(self, arg):
        """Historia decyzji i zdarzeń z analizą"""
        if not self.game_state:
            print(colored("Najpierw 'start'", Colors.RED))
            return
        
        if not self.action_history:
            print(colored("Brak historii - zagraj kilka miesięcy.", Colors.YELLOW))
            return
        
        print(colored("\n" + "═"*60, Colors.CYAN))
        print(colored("  HISTORIA GRY", Colors.BOLD))
        print(colored("═"*60, Colors.CYAN))
        
        current_month = -1
        for entry in self.action_history[-20:]:  # Ostatnie 20
            if entry['month'] != current_month:
                current_month = entry['month']
                print(colored(f"\n📅 Miesiąc {current_month}:", Colors.HEADER))
            
            if entry['type'] == 'event':
                print(f"   ⚡ {entry['name']}")
            else:
                icon = '✓' if entry.get('success', True) else '✗'
                print(f"   {icon} {entry['name']}")
            
            if entry.get('effects'):
                print(f"      → {', '.join(entry['effects'])}")
        
        # P2: Dodaj analizę decyzji
        self._analyze_history()
    
    def do_postep(self, arg):
        """Pokazuje postęp vs cele (12 miesięcy)"""
        if not self.game_state:
            print(colored("Najpierw 'start'", Colors.RED))
            return
        self._show_progress_comparison()
    
    def do_raport(self, arg):
        """Raport miesięczny - podsumowanie zarządcze"""
        if not self.game_state:
            print(colored("Najpierw 'start'", Colors.RED))
            return
        self._show_monthly_report()
    
    def do_mentor(self, arg):
        """Włącz/wyłącz tryb mentor (podpowiedzi edukacyjne)"""
        self.mentor_mode = not self.mentor_mode
        status = "WŁĄCZONY" if self.mentor_mode else "WYŁĄCZONY"
        print(colored(f"💡 Tryb mentor: {status}", Colors.CYAN))
    
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
        print("| **Zweryfikowany** | " + " | ".join("✓" if f.krs_verified and f.debtor_registry_verified else "⚠️" for f in founders) + " |")

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
                effects = ', '.join(entry.get('effects', []))[:25] or '-'
                print(f"| {m} | {icon} | {name} | {effects} |")
        
        print()  # Pusta linia na końcu
    
    def do_akcje(self, arg):
        """Pokaż akcje"""
        if not self.game_state:
            print(colored("Najpierw 'start'", Colors.RED))
            return
        self._show_action_menu()
    
    def do_finanse(self, arg):
        """Finanse"""
        if not self.game_state:
            print(colored("Najpierw 'start'", Colors.RED))
            return
        c = self.game_state.company
        print_box("FINANSE", [
            f"MRR: {c.mrr:,.0f} PLN | ARR: {c.mrr*12:,.0f} PLN",
            f"Burn: {c.monthly_burn_rate:,.0f} PLN/mies",
            f"Gotówka: {c.cash_on_hand:,.0f} PLN",
            f"Runway: {c.runway_months()} mies",
            f"Wycena: {c.current_valuation:,.0f} PLN"
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

        print("| **Equity** | " + " | ".join(f"{f.equity_percentage:.0f}%" for f in founders) + " |")
        print("| **Vested** | " + " | ".join(f"{f.vested_percentage:.1f}%" for f in founders) + " |")
        print("| **Zainwestowane** | " + " | ".join(f"{f.personal_invested:,.0f} PLN" for f in founders) + " |")
        print("| **Otrzymane z firmy** | " + " | ".join(f"{f.total_received:,.0f} PLN" for f in founders) + " |")
        print("| **Bilans** | " + " | ".join(f"{(f.total_received - f.personal_invested):+,.0f} PLN" for f in founders) + " |")
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
                effects = ', '.join(entry.get('effects', []))[:40] or '-'
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
        
        if self.config.has_partner and not self.game_state.agreement_signed:
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
        self.config.initial_cash = data.get('cash', 10000)
        self.config.monthly_burn = data.get('burn', 5000)
        
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
        
        print(colored(f"\n✓ Wczytano grę: {save['name']}", Colors.GREEN))
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
            'customers': self.game_state.company.paying_customers,
            'registered': self.game_state.company.registered,
            'mvp_completed': self.game_state.company.mvp_completed,
            'agreement_signed': self.game_state.agreement_signed,
            'mvp_progress': self.game_state.mvp_progress,
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
