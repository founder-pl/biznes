"""
Biznes - Interaktywny interfejs shell
Główny interfejs użytkownika dla gry edukacyjnej
Wersja 2.0 - Pełna interaktywność z menu akcji
"""

import cmd
import os
import sys
import yaml
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
                return True, "Umowa wspólników podpisana!", {'cash': -cost}
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
    
    intro = f"""
{colored('═'*60, Colors.CYAN)}
{colored('  BIZNES - Symulator Startupu v2.0', Colors.BOLD)}
{colored('  Edukacyjna gra o zakładaniu firmy w Polsce', Colors.CYAN)}
{colored('═'*60, Colors.CYAN)}

Wpisz {colored('start', Colors.GREEN)} aby rozpocząć nową grę.
Wpisz {colored('pomoc', Colors.GREEN)} aby zobaczyć komendy.
"""
    
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
    
    def do_pomoc(self, arg):
        """Wyświetla pomoc"""
        help_text = [
            f"{colored('start', Colors.GREEN)}      - Rozpocznij nową grę",
            f"{colored('status', Colors.GREEN)}     - Stan firmy",
            f"{colored('miesiac', Colors.GREEN)}    - Następny miesiąc + akcje",
            f"{colored('akcje', Colors.GREEN)}      - Dostępne akcje",
            f"{colored('historia', Colors.GREEN)}   - Historia decyzji",
            "",
            f"{colored('finanse', Colors.GREEN)}    - Szczegóły finansowe",
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
        
        # ETAP 3: Partner
        print(colored("\n\nETAP 3/6: Partner", Colors.HEADER))
        has_partner = self._ask_yes_no("Masz partnera/co-foundera?", False)
        self.config.has_partner = has_partner
        
        if has_partner:
            self.config.partner_name = self._ask("Imię partnera", "Partner")
            
            print(colored("\n🔍 WERYFIKACJA PARTNERA:", Colors.YELLOW))
            self.config.partner_krs_verified = self._ask_yes_no("Sprawdziłeś w KRS?", False)
            if not self.config.partner_krs_verified:
                print(colored("   ⚠️ RYZYKO: Możesz nie wiedzieć o upadłościach!", Colors.RED))
            
            self.config.partner_debts_verified = self._ask_yes_no("Sprawdziłeś rejestry dłużników?", False)
            if not self.config.partner_debts_verified:
                print(colored("   ⚠️ RYZYKO: Partner może mieć długi!", Colors.RED))
            
            self.config.partner_capital = self._ask_number("Kapitał partnera (PLN)", 0, 1000000, 0)
            self.config.partner_experience_years = int(self._ask_number("Doświadczenie (lata)", 0, 30, 0))
            self.config.partner_has_customers = self._ask_yes_no("Ma klientów/kontakty?", False)
            
            if self.config.partner_has_customers:
                self.config.partner_contacts_count = int(self._ask_number("Ile kontaktów/leadów wnosi?", 1, 500, 10))
                print(colored(f"   ✓ Partner wnosi {self.config.partner_contacts_count} potencjalnych kontaktów", Colors.GREEN))
            else:
                self.config.partner_contacts_count = 0
            
            # Equity
            print(colored("\n📊 REKOMENDACJA EQUITY:", Colors.HEADER))
            player_base, partner_base = 50, 50
            
            if self.config.mvp_calculated_value > 0:
                mvp_bonus = min(20, self.config.mvp_calculated_value / 5000)
                player_base += mvp_bonus
                partner_base -= mvp_bonus
                print(f"   MVP: +{mvp_bonus:.0f}% dla Ciebie")
            
            if self.config.partner_capital > 0:
                cap_bonus = min(15, self.config.partner_capital / 5000)
                partner_base += cap_bonus
                player_base -= cap_bonus
                print(f"   Kapitał: +{cap_bonus:.0f}% dla partnera")
            
            if self.config.partner_contacts_count > 0:
                contacts_bonus = min(10, self.config.partner_contacts_count / 5)
                partner_base += contacts_bonus
                player_base -= contacts_bonus
                print(f"   Kontakty ({self.config.partner_contacts_count}): +{contacts_bonus:.0f}% dla partnera")
            
            esop = 10
            self.config.player_equity = player_base - esop/2
            self.config.partner_equity = partner_base - esop/2
            self.config.esop_pool = esop
            
            print(colored(f"\n   Ty: {self.config.player_equity:.0f}%", Colors.GREEN))
            print(f"   Partner: {self.config.partner_equity:.0f}%")
            print(f"   ESOP: {esop}%")
            
            if not self._ask_yes_no("Akceptujesz?", True):
                self.config.player_equity = self._ask_number("Twój udział %", 1, 95, player_base)
                self.config.partner_equity = self._ask_number("Udział partnera %", 1, 95, partner_base)
                self.config.esop_pool = 100 - self.config.player_equity - self.config.partner_equity
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
            partner = Founder(
                name=self.config.partner_name,
                role="business" if self.config.player_role == "technical" else "technical",
                equity_percentage=self.config.partner_equity,
                initial_investment=self.config.partner_capital,
                experience_years=self.config.partner_experience_years,
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
        
        print(f"\n📊 SYTUACJA:")
        print(f"   Forma: {company.legal_form.value.upper()}")
        print(f"   Gotówka: {company.cash_on_hand:,.0f} PLN")
        print(f"   Runway: {company.runway_months()} mies")
        print(f"   MVP: {'✓' if company.mvp_completed else '✗'}")
        
        print(colored("\n💡 PIERWSZE KROKI:", Colors.YELLOW))
        print("   1. 'akcje' - co możesz zrobić")
        print("   2. 'miesiac' - następny miesiąc")
        print("   3. 'ryzyko' - analiza zagrożeń")
        
        if not company.registered:
            print(colored("\n   ⚠️ PRIORYTET: Zarejestruj spółkę!", Colors.RED))
        if self.config.has_partner and not self.game_state.agreement_signed:
            print(colored("   ⚠️ PRIORYTET: Podpisz umowę wspólników!", Colors.RED))
    
    def do_miesiac(self, arg):
        """Następny miesiąc"""
        if not self.game_state:
            print(colored("Najpierw 'start'", Colors.RED))
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
        
        print(colored("\n─"*60, Colors.CYAN))
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
        """Wykonuje akcję"""
        print(colored(f"\n📋 {action.name}", Colors.HEADER))
        
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
        
        if self._ask_yes_no("\nWykonać?", True):
            success, msg, effects = self.action_system.execute_action(action.id)
            print(colored(f"\n{'✓' if success else '✗'} {msg}", Colors.GREEN if success else Colors.RED))
            
            # Zapisz do historii
            self.action_history.append({
                'month': self.game_state.current_month,
                'type': 'action',
                'name': action.name,
                'success': success,
                'effects': [msg] if msg else []
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
        """Historia decyzji i zdarzeń"""
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
    
    def do_status(self, arg):
        """Status firmy"""
        if not self.game_state:
            print(colored("Najpierw 'start'", Colors.RED))
            return
        
        c = self.game_state.company
        print_box(f"STATUS - Miesiąc {self.game_state.current_month}", [
            f"Gotówka: {c.cash_on_hand:,.0f} PLN",
            f"MRR: {c.mrr:,.0f} PLN | Klienci: {c.paying_customers}",
            f"Runway: {c.runway_months()} mies",
            f"MVP: {'✓' if c.mvp_completed else f'{self.game_state.mvp_progress}%'}",
            f"Spółka: {'✓' if c.registered else '✗'} | SHA: {'✓' if self.game_state.agreement_signed else '✗'}"
        ])
    
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
    
    def do_zapisz(self, arg):
        """Zapisz grę"""
        if not self.game_state:
            return
        name = arg or f"save_{datetime.now().strftime('%Y%m%d_%H%M')}"
        path = self.save_dir / f"{name}.yaml"
        
        data = {
            'month': self.game_state.current_month,
            'cash': self.game_state.company.cash_on_hand,
            'mrr': self.game_state.company.mrr,
            'customers': self.game_state.company.paying_customers
        }
        
        with open(path, 'w') as f:
            yaml.dump(data, f)
        print(colored(f"✓ Zapisano: {path}", Colors.GREEN))


def main():
    """Punkt wejścia"""
    try:
        BiznesShell().cmdloop()
    except KeyboardInterrupt:
        print(colored("\n\nDo zobaczenia!", Colors.CYAN))
        sys.exit(0)


if __name__ == "__main__":
    main()
