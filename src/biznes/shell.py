"""
Biznes - Interaktywny interfejs shell
Główny interfejs użytkownika dla gry edukacyjnej
"""

import cmd
import os
import sys
import yaml
import random
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

from .core.models import (
    GameState, PlayerConfig, Company, Founder, 
    LegalForm, EmploymentForm, StartupStage,
    FoundersAgreement, VestingSchedule
)
from .scenarios.engine import get_scenario_engine, ScenarioEngine


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
    END = '\033[0m'
    
    @classmethod
    def disable(cls):
        cls.HEADER = ''
        cls.BLUE = ''
        cls.CYAN = ''
        cls.GREEN = ''
        cls.YELLOW = ''
        cls.RED = ''
        cls.BOLD = ''
        cls.UNDERLINE = ''
        cls.END = ''


def colored(text: str, color: str) -> str:
    """Zwraca kolorowy tekst"""
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


def print_risk(level: str, message: str):
    """Drukuje komunikat o ryzyku z odpowiednim kolorem"""
    if level == "KRYTYCZNE" or level == "CRITICAL":
        print(f"  {colored('⚠️  ' + level, Colors.RED)}: {message}")
    elif level == "WYSOKIE" or level == "HIGH":
        print(f"  {colored('⚡ ' + level, Colors.YELLOW)}: {message}")
    elif level == "ŚREDNIE" or level == "MEDIUM":
        print(f"  {colored('📊 ' + level, Colors.BLUE)}: {message}")
    else:
        print(f"  {colored('✓ ' + level, Colors.GREEN)}: {message}")


# ============================================================================
# GŁÓWNA KLASA SHELL
# ============================================================================

class BiznesShell(cmd.Cmd):
    """Interaktywny shell gry Biznes"""
    
    intro = f"""
{colored('='*60, Colors.CYAN)}
{colored('  BIZNES - Symulator Startupu dla Founderów', Colors.BOLD)}
{colored('  Edukacyjna gra o zakładaniu firmy w Polsce', Colors.CYAN)}
{colored('='*60, Colors.CYAN)}

Wpisz {colored('pomoc', Colors.GREEN)} aby zobaczyć dostępne komendy.
Wpisz {colored('start', Colors.GREEN)} aby rozpocząć nową grę.
Wpisz {colored('wczytaj', Colors.GREEN)} aby wczytać zapisaną grę.
"""
    
    prompt = colored("biznes> ", Colors.GREEN)
    
    def __init__(self):
        super().__init__()
        self.game_state: Optional[GameState] = None
        self.config: Optional[PlayerConfig] = None
        self.scenario_engine: Optional[ScenarioEngine] = None
        self.save_dir = Path.home() / ".biznes_saves"
        self.save_dir.mkdir(exist_ok=True)
        
    # =========================================================================
    # PODSTAWOWE KOMENDY
    # =========================================================================
    
    def do_pomoc(self, arg):
        """Wyświetla pomoc"""
        help_text = [
            f"{colored('start', Colors.GREEN)}      - Rozpocznij nową grę",
            f"{colored('wczytaj', Colors.GREEN)}    - Wczytaj zapisaną grę",
            f"{colored('zapisz', Colors.GREEN)}     - Zapisz aktualny stan gry",
            "",
            f"{colored('status', Colors.GREEN)}     - Pokaż aktualny stan firmy",
            f"{colored('ryzyko', Colors.GREEN)}     - Analiza ryzyka",
            f"{colored('finanse', Colors.GREEN)}    - Szczegóły finansowe",
            f"{colored('equity', Colors.GREEN)}     - Podział udziałów",
            f"{colored('umowa', Colors.GREEN)}      - Pokaż umowę wspólników",
            "",
            f"{colored('miesiac', Colors.GREEN)}    - Przejdź do następnego miesiąca",
            f"{colored('decyzja', Colors.GREEN)}    - Podejmij ważną decyzję",
            "",
            f"{colored('nauka', Colors.GREEN)}      - Materiały edukacyjne",
            f"{colored('slownik', Colors.GREEN)}    - Słownik pojęć",
            "",
            f"{colored('eksport', Colors.GREEN)}    - Eksportuj konfigurację do YAML",
            f"{colored('wyjscie', Colors.GREEN)}    - Zakończ grę"
        ]
        print_box("POMOC - Dostępne komendy", help_text)
    
    def do_help(self, arg):
        """Alias dla pomoc"""
        self.do_pomoc(arg)
    
    def do_wyjscie(self, arg):
        """Wyjście z gry"""
        if self.game_state:
            response = self._ask("Czy chcesz zapisać grę przed wyjściem? (tak/nie)")
            if response.lower() in ['tak', 't', 'yes', 'y']:
                self.do_zapisz("")
        print(colored("\nDziękujemy za grę! Do zobaczenia!", Colors.CYAN))
        return True
    
    def do_quit(self, arg):
        """Alias dla wyjscie"""
        return self.do_wyjscie(arg)
    
    def do_exit(self, arg):
        """Alias dla wyjscie"""
        return self.do_wyjscie(arg)
    
    # =========================================================================
    # ROZPOCZĘCIE GRY
    # =========================================================================
    
    def do_start(self, arg):
        """Rozpoczyna nową grę"""
        print(colored("\n" + "="*60, Colors.CYAN))
        print(colored("  NOWA GRA - Konfiguracja początkowa", Colors.BOLD))
        print(colored("="*60 + "\n", Colors.CYAN))
        
        self.config = PlayerConfig()
        self.game_state = GameState()
        
        # Etap 1: Dane gracza
        self._setup_player()
        
        # Etap 2: MVP
        self._setup_mvp()
        
        # Etap 3: Partner
        self._setup_partner()
        
        # Etap 4: Equity
        self._setup_equity()
        
        # Etap 5: Forma prawna
        self._setup_legal_form()
        
        # Etap 6: Zabezpieczenia
        self._setup_protections()
        
        # Etap 7: Cele
        self._setup_goals()
        
        # Etap 8: Symulacja
        self._setup_simulation()
        
        # Inicjalizacja silnika scenariuszy
        self.scenario_engine = get_scenario_engine(self.config.difficulty)
        
        # Podsumowanie
        self._show_setup_summary()
        
        print(colored("\n✓ Gra rozpoczęta! Wpisz 'status' aby zobaczyć stan firmy.", Colors.GREEN))
        print(colored("  Wpisz 'miesiac' aby przejść do następnego miesiąca.\n", Colors.CYAN))
    
    def _setup_player(self):
        """Konfiguracja danych gracza"""
        print(colored("\n── ETAP 1: Twoje dane ──\n", Colors.YELLOW))
        
        self.config.player_name = self._ask("Jak masz na imię?", default="Founder")
        
        print("\nJaka jest Twoja rola?")
        print("  1. Technical co-founder (programista, CTO)")
        print("  2. Business co-founder (biznes, CEO)")
        
        role = self._ask("Wybierz (1/2)", default="1")
        self.config.player_role = "technical" if role == "1" else "business"
        
        self.game_state.player_name = self.config.player_name
        self.game_state.player_role = self.config.player_role
        
    def _setup_mvp(self):
        """Konfiguracja MVP"""
        print(colored("\n── ETAP 2: MVP (Minimum Viable Product) ──\n", Colors.YELLOW))
        
        has_mvp = self._ask("Czy masz już gotowy prototyp/MVP? (tak/nie)", default="nie")
        self.config.has_mvp = has_mvp.lower() in ['tak', 't', 'yes', 'y']
        
        if self.config.has_mvp:
            print(colored("\n📊 Wycena MVP metodą kosztową:", Colors.CYAN))
            
            hours = self._ask_int("Ile godzin pracy włożyłeś w MVP?", default=200)
            self.config.mvp_hours_invested = hours
            
            rate = self._ask_int("Jaka jest Twoja stawka godzinowa (PLN)?", default=150)
            self.config.mvp_hourly_rate = rate
            
            costs = self._ask_float("Koszty zewnętrzne (serwery, API, narzędzia)?", default=5000)
            self.config.mvp_external_costs = costs
            
            mvp_value = hours * rate + costs
            
            print(colored(f"\n💰 Szacowana wartość MVP: {mvp_value:,.0f} PLN", Colors.GREEN))
            print(f"   ({hours}h × {rate} PLN + {costs:,.0f} PLN kosztów)")
            
            # Utwórz foundera z MVP
            player_founder = Founder(
                name=self.config.player_name,
                role=self.config.player_role,
                brought_mvp=True,
                mvp_value=mvp_value
            )
            self.game_state.company.founders.append(player_founder)
            self.game_state.company.mvp_completed = True
            
    def _setup_partner(self):
        """Konfiguracja partnera"""
        print(colored("\n── ETAP 3: Partner biznesowy ──\n", Colors.YELLOW))
        
        print(colored("⚠️  UWAGA: To kluczowy moment! Weryfikacja partnera jest krytyczna.", Colors.RED))
        print()
        
        self.config.partner_name = self._ask("Jak nazywa się Twój potencjalny partner?", default="Partner")
        
        # Weryfikacja
        print(colored("\n📋 WERYFIKACJA PARTNERA:", Colors.YELLOW))
        
        verified_krs = self._ask("Czy sprawdziłeś go w KRS (ekrs.ms.gov.pl)? (tak/nie)", default="nie")
        self.config.partner_verified_krs = verified_krs.lower() in ['tak', 't']
        
        verified_debts = self._ask("Czy sprawdziłeś rejestry dłużników (BIG, KRD)? (tak/nie)", default="nie")
        self.config.partner_verified_debts = verified_debts.lower() in ['tak', 't']
        
        if not self.config.partner_verified_krs or not self.config.partner_verified_debts:
            print(colored("\n⚠️  RED FLAG: Partner niezweryfikowany!", Colors.RED))
            print("   Rekomendacja: Sprawdź przed jakąkolwiek współpracą!")
            print("   - KRS: ekrs.ms.gov.pl")
            print("   - BIG InfoMonitor, KRD, ERIF (koszt ~30-50 PLN)")
        
        # Co wnosi partner
        print(colored("\n💼 Co wnosi partner?", Colors.CYAN))
        
        capital = self._ask_float("Kapitał finansowy (PLN)?", default=0)
        self.config.partner_brings_capital = capital
        
        customers = self._ask_int("Ilu ma klientów/kontaktów?", default=0)
        self.config.partner_brings_customers = customers
        
        exp_years = self._ask_int("Lat doświadczenia w branży?", default=0)
        self.config.partner_industry_experience_years = exp_years
        
        startup_exp = self._ask_int("Ile startupów wcześniej zakładał?", default=0)
        self.config.partner_startup_experience = startup_exp
        
        contacts = self._ask("Czy ma wartościowe kontakty biznesowe? (tak/nie)", default="nie")
        self.config.partner_has_contacts = contacts.lower() in ['tak', 't']
        
        # Sprawdź red flags
        if capital == 0 and customers == 0 and exp_years == 0:
            print(colored("\n🚨 KRYTYCZNY RED FLAG: Partner nie wnosi nic mierzalnego!", Colors.RED))
            print("   Sam 'pomysł' bez walidacji to maksymalnie 5-10% wartości.")
            print("   Rozważ ponownie tę współpracę.")
        
        # Dodaj partnera
        partner_founder = Founder(
            name=self.config.partner_name,
            role="business" if self.config.player_role == "technical" else "technical",
            initial_investment=capital,
            experience_years=exp_years,
            krs_verified=self.config.partner_verified_krs,
            debtor_registry_verified=self.config.partner_verified_debts
        )
        self.game_state.company.founders.append(partner_founder)
    
    def _setup_equity(self):
        """Konfiguracja podziału equity"""
        print(colored("\n── ETAP 4: Podział equity ──\n", Colors.YELLOW))
        
        # Oblicz rekomendację
        engine = get_scenario_engine()
        recommendation = engine.get_equity_recommendation(
            player_brings_mvp=self.config.has_mvp,
            mvp_value=self.config.mvp_hours_invested * self.config.mvp_hourly_rate + self.config.mvp_external_costs,
            partner_brings_capital=self.config.partner_brings_capital,
            partner_has_industry_exp=self.config.partner_industry_experience_years > 2,
            partner_has_customers=self.config.partner_brings_customers > 0
        )
        
        print(colored("📊 REKOMENDACJA na podstawie wkładów:", Colors.CYAN))
        print(f"\n   Ty: {recommendation['player_percentage']}%")
        print(f"   Partner: {recommendation['partner_percentage']}%")
        print(f"   ESOP (dla przyszłych pracowników): {recommendation['esop_pool']}%")
        
        print(colored("\n   Uzasadnienie:", Colors.CYAN))
        for reason in recommendation['reasoning']:
            print(f"   • {reason}")
            
        if recommendation['warning']:
            print(colored(f"\n   ⚠️  {recommendation['warning']}", Colors.YELLOW))
        
        # Zapytaj o preferencje
        print()
        accept = self._ask("Czy akceptujesz ten podział? (tak/nie/własny)", default="tak")
        
        if accept.lower() in ['tak', 't']:
            self.config.proposed_equity_split_player = recommendation['player_percentage']
            self.config.proposed_equity_split_partner = recommendation['partner_percentage']
            self.config.esop_pool = recommendation['esop_pool']
        else:
            player_pct = self._ask_float("Twój udział (%):", default=50)
            partner_pct = self._ask_float("Udział partnera (%):", default=40)
            esop = self._ask_float("ESOP pool (%):", default=10)
            
            if player_pct + partner_pct + esop != 100:
                print(colored("⚠️  Suma musi wynosić 100%. Dostosowuję...", Colors.YELLOW))
                total = player_pct + partner_pct + esop
                player_pct = player_pct / total * 100
                partner_pct = partner_pct / total * 100
                esop = esop / total * 100
            
            self.config.proposed_equity_split_player = player_pct
            self.config.proposed_equity_split_partner = partner_pct
            self.config.esop_pool = esop
        
        # Aktualizuj founderów
        for founder in self.game_state.company.founders:
            if founder.name == self.config.player_name:
                founder.equity_percentage = self.config.proposed_equity_split_player
            else:
                founder.equity_percentage = self.config.proposed_equity_split_partner
        
        self.game_state.company.esop_pool_percentage = self.config.esop_pool
    
    def _setup_legal_form(self):
        """Konfiguracja formy prawnej"""
        print(colored("\n── ETAP 5: Forma prawna ──\n", Colors.YELLOW))
        
        # Oblicz rekomendację
        engine = get_scenario_engine()
        recommendation = engine.get_legal_form_recommendation(
            has_capital=self.config.partner_brings_capital > 5000,
            plans_vc=True,  # zakładamy ambitny scenariusz
            needs_work_contribution=self.config.has_mvp,
            needs_easy_esop=True
        )
        
        print(colored(f"📊 REKOMENDACJA: {recommendation['recommended']}", Colors.GREEN))
        
        print(colored("\n   Prosta Spółka Akcyjna (PSA):", Colors.CYAN))
        for reason in recommendation['psa_reasons']:
            print(f"   ✓ {reason}")
        print(f"   Koszty: założenie 1 PLN, rocznie ~{recommendation['cost_comparison']['psa_yearly']} PLN (rejestr)")
        
        print(colored("\n   Sp. z o.o.:", Colors.CYAN))
        for reason in recommendation['zoo_reasons']:
            print(f"   ✓ {reason}")
        print(f"   Koszty: założenie {recommendation['cost_comparison']['zoo_startup']} PLN, rocznie ~0 PLN")
        
        print("\nWybierz formę prawną:")
        print("  1. PSA (Prosta Spółka Akcyjna)")
        print("  2. Sp. z o.o.")
        print("  3. Nie zakładamy jeszcze spółki")
        
        choice = self._ask("Wybór (1/2/3)", default="1")
        
        if choice == "1":
            self.config.preferred_legal_form = "psa"
            self.game_state.company.legal_form = LegalForm.PSA
        elif choice == "2":
            self.config.preferred_legal_form = "sp_zoo"
            self.game_state.company.legal_form = LegalForm.SP_ZOO
        else:
            self.config.preferred_legal_form = "none"
            self.game_state.company.legal_form = LegalForm.NONE
    
    def _setup_protections(self):
        """Konfiguracja zabezpieczeń prawnych"""
        print(colored("\n── ETAP 6: Zabezpieczenia prawne ──\n", Colors.YELLOW))
        
        print(colored("⚠️  Te klauzule w umowie wspólników mogą uratować Ci firmę!", Colors.RED))
        print()
        
        # Vesting
        print(colored("📋 VESTING:", Colors.CYAN))
        print("   Mechanizm stopniowego nabywania udziałów przez czas.")
        print("   Standard: 4 lata z 1-rocznym cliff.")
        
        vesting = self._ask_int("Okres vestingu (miesięcy):", default=48)
        self.config.vesting_months = vesting
        
        cliff = self._ask_int("Cliff (miesięcy):", default=12)
        self.config.cliff_months = cliff
        
        # Tag-along
        print(colored("\n📋 TAG-ALONG:", Colors.CYAN))
        print("   Prawo przyłączenia - możesz sprzedać swoje udziały")
        print("   na tych samych warunkach co większościowy wspólnik.")
        
        tag_along = self._ask("Czy chcesz tag-along? (tak/nie)", default="tak")
        self.config.wants_tag_along = tag_along.lower() in ['tak', 't']
        
        # Good/Bad leaver
        print(colored("\n📋 GOOD/BAD LEAVER:", Colors.CYAN))
        print("   Definiuje co się dzieje z udziałami przy odejściu wspólnika.")
        print("   Good leaver: zachowujesz vested equity")
        print("   Bad leaver: możesz stracić wszystko")
        
        leaver = self._ask("Czy chcesz klauzule good/bad leaver? (tak/nie)", default="tak")
        self.config.wants_good_bad_leaver = leaver.lower() in ['tak', 't']
        
        # IP
        print(colored("\n📋 OCHRONA IP:", Colors.CYAN))
        print("   Jasne określenie komu należy kod i własność intelektualna.")
        
        ip = self._ask("Czy chcesz klauzulę IP assignment? (tak/nie)", default="tak")
        self.config.wants_ip_protection = ip.lower() in ['tak', 't']
        
        # Non-compete
        print(colored("\n📋 ZAKAZ KONKURENCJI:", Colors.CYAN))
        print("   Ochrona przed partnerem zakładającym konkurencyjną firmę.")
        
        non_compete = self._ask("Czy chcesz zakaz konkurencji? (tak/nie)", default="tak")
        self.config.wants_non_compete = non_compete.lower() in ['tak', 't']
        
        if self.config.wants_non_compete:
            months = self._ask_int("Na ile miesięcy (max 24)?", default=12)
            self.config.non_compete_months = min(24, months)
        
        # Aktualizuj umowę w stanie gry
        agreement = self.game_state.founders_agreement
        agreement.vesting_schedule = VestingSchedule(
            total_months=self.config.vesting_months,
            cliff_months=self.config.cliff_months
        )
        agreement.has_tag_along = self.config.wants_tag_along
        agreement.has_good_bad_leaver = self.config.wants_good_bad_leaver
        agreement.has_ip_assignment = self.config.wants_ip_protection
        agreement.has_non_compete = self.config.wants_non_compete
        agreement.non_compete_months = self.config.non_compete_months
    
    def _setup_goals(self):
        """Konfiguracja celów biznesowych"""
        print(colored("\n── ETAP 7: Cele biznesowe ──\n", Colors.YELLOW))
        
        print("Ustal cele dla swojego startupu:")
        
        mrr_6 = self._ask_float("Cel MRR po 6 miesiącach (PLN):", default=10000)
        self.config.target_mrr_6_months = mrr_6
        
        customers_6 = self._ask_int("Cel klientów po 6 miesiącach:", default=50)
        self.config.target_customers_6_months = customers_6
        
        mrr_12 = self._ask_float("Cel MRR po 12 miesiącach (PLN):", default=30000)
        self.config.target_mrr_12_months = mrr_12
        
        customers_12 = self._ask_int("Cel klientów po 12 miesiącach:", default=150)
        self.config.target_customers_12_months = customers_12
        
        # Zasoby
        print(colored("\n💰 Twoje zasoby:", Colors.CYAN))
        
        runway = self._ask_int("Ile miesięcy możesz pracować bez przychodów?", default=6)
        self.config.personal_runway_months = runway
        
        savings = self._ask_float("Oszczędności na projekt (PLN):", default=0)
        self.config.personal_savings = savings
        
        no_salary = self._ask("Czy możesz pracować bez wynagrodzenia na start? (tak/nie)", default="nie")
        self.config.willing_to_work_without_salary = no_salary.lower() in ['tak', 't']
        
        if self.config.willing_to_work_without_salary:
            max_months = self._ask_int("Maksymalnie ile miesięcy bez wynagrodzenia?", default=6)
            self.config.max_months_without_salary = max_months
        
        # Inicjalizuj finanse spółki
        self.game_state.company.cash_on_hand = savings + self.config.partner_brings_capital
    
    def _setup_simulation(self):
        """Konfiguracja symulacji"""
        print(colored("\n── ETAP 8: Ustawienia symulacji ──\n", Colors.YELLOW))
        
        print("Poziom trudności:")
        print("  1. Łatwy (więcej pozytywnych zdarzeń)")
        print("  2. Normalny (realistyczny)")
        print("  3. Trudny (więcej wyzwań)")
        
        difficulty = self._ask("Wybór (1/2/3):", default="2")
        self.config.difficulty = {
            "1": "easy", "2": "normal", "3": "hard"
        }.get(difficulty, "normal")
        
        random_events = self._ask("Czy włączyć losowe zdarzenia? (tak/nie)", default="tak")
        self.config.enable_random_events = random_events.lower() in ['tak', 't']
        
        detailed = self._ask("Czy chcesz szczegółowe wyjaśnienia? (tak/nie)", default="tak")
        self.config.detailed_explanations = detailed.lower() in ['tak', 't']
        
        self.game_state.random_events_enabled = self.config.enable_random_events
        self.game_state.difficulty = self.config.difficulty
    
    def _show_setup_summary(self):
        """Podsumowanie konfiguracji"""
        print(colored("\n" + "="*60, Colors.CYAN))
        print(colored("  PODSUMOWANIE KONFIGURACJI", Colors.BOLD))
        print(colored("="*60, Colors.CYAN))
        
        summary = [
            f"Gracz: {self.config.player_name} ({self.config.player_role})",
            f"Partner: {self.config.partner_name}",
            "",
            f"Forma prawna: {self.config.preferred_legal_form.upper()}",
            f"Equity: Ty {self.config.proposed_equity_split_player:.1f}% / Partner {self.config.proposed_equity_split_partner:.1f}% / ESOP {self.config.esop_pool:.1f}%",
            f"Vesting: {self.config.vesting_months} mies. z {self.config.cliff_months} mies. cliff",
            "",
            f"Kapitał startowy: {self.game_state.company.cash_on_hand:,.0f} PLN",
            f"MVP: {'Tak' if self.config.has_mvp else 'Nie'}",
            "",
            f"Trudność: {self.config.difficulty}",
            f"Zdarzenia losowe: {'Włączone' if self.config.enable_random_events else 'Wyłączone'}"
        ]
        
        print_box("TWOJA GRA", summary, Colors.GREEN)
        
        # Pokaż brakujące zabezpieczenia
        missing = self.game_state.founders_agreement.get_missing_protections()
        if missing:
            print(colored("\n⚠️  BRAKUJĄCE ZABEZPIECZENIA:", Colors.YELLOW))
            for m in missing:
                print(f"   • {m}")
    
    # =========================================================================
    # KOMENDY GRY
    # =========================================================================
    
    def do_status(self, arg):
        """Pokazuje aktualny stan firmy"""
        if not self.game_state:
            print(colored("Najpierw rozpocznij grę komendą 'start'", Colors.RED))
            return
            
        company = self.game_state.company
        
        status = [
            f"Miesiąc: {self.game_state.current_month}",
            f"Etap: {company.stage.value if company.stage else 'IDEA'}",
            "",
            f"MRR: {company.mrr:,.0f} PLN",
            f"Klienci: {company.total_customers}",
            f"Gotówka: {company.cash_on_hand:,.0f} PLN",
            f"Burn rate: {company.monthly_burn_rate:,.0f} PLN/mies.",
            f"Runway: {company.runway_months()} miesięcy",
            "",
            f"Wycena: {company.current_valuation:,.0f} PLN" if company.current_valuation > 0 else "Wycena: N/A",
            f"Zebrane: {company.total_raised:,.0f} PLN" if company.total_raised > 0 else "",
            "",
            f"Umowa wspólników: {'✓ Podpisana' if self.game_state.founders_agreement.signed else '✗ Niepodpisana'}",
            f"Spółka zarejestrowana: {'✓ Tak' if company.registered else '✗ Nie'}"
        ]
        
        print_box(f"STATUS - {company.name or 'Startup'}", [s for s in status if s], Colors.CYAN)
    
    def do_ryzyko(self, arg):
        """Analiza ryzyka"""
        if not self.game_state:
            print(colored("Najpierw rozpocznij grę komendą 'start'", Colors.RED))
            return
        
        risk_analysis = self.scenario_engine.calculate_risk_score(self.game_state)
        
        print(colored(f"\n📊 ANALIZA RYZYKA", Colors.YELLOW))
        print(f"   Wynik ogólny: {risk_analysis['total_score']}/100")
        print(f"   Poziom: {colored(risk_analysis['level'], Colors.RED if risk_analysis['total_score'] > 50 else Colors.GREEN)}")
        print()
        
        print(colored("   Zidentyfikowane ryzyka:", Colors.CYAN))
        for level, message in risk_analysis['risks']:
            print_risk(level, message)
        
        print(colored(f"\n   💡 Rekomendacja: {risk_analysis['recommendation']}", Colors.GREEN))
    
    def do_finanse(self, arg):
        """Szczegóły finansowe"""
        if not self.game_state:
            print(colored("Najpierw rozpocznij grę komendą 'start'", Colors.RED))
            return
        
        company = self.game_state.company
        
        finances = [
            f"Gotówka: {company.cash_on_hand:,.0f} PLN",
            f"MRR (Monthly Recurring Revenue): {company.mrr:,.0f} PLN",
            f"ARR (Annual Recurring Revenue): {company.mrr * 12:,.0f} PLN",
            "",
            f"Burn rate: {company.monthly_burn_rate:,.0f} PLN/miesiąc",
            f"Net burn: {max(0, company.monthly_burn_rate - company.mrr):,.0f} PLN/miesiąc",
            f"Runway: {company.runway_months()} miesięcy",
            "",
            f"Zebrane od inwestorów: {company.total_raised:,.0f} PLN",
            f"Aktualna wycena: {company.current_valuation:,.0f} PLN" if company.current_valuation > 0 else "Wycena: Brak"
        ]
        
        print_box("FINANSE", finances, Colors.CYAN)
        
        if company.runway_months() < 6:
            print(colored("\n⚠️  UWAGA: Runway poniżej 6 miesięcy!", Colors.RED))
            print("   Rozważ: redukcję kosztów, pozyskanie inwestora, lub przyspieszenie sprzedaży.")
    
    def do_equity(self, arg):
        """Pokazuje podział udziałów"""
        if not self.game_state:
            print(colored("Najpierw rozpocznij grę komendą 'start'", Colors.RED))
            return
        
        print(colored("\n📊 PODZIAŁ EQUITY (Cap Table)\n", Colors.CYAN))
        
        print(f"{'Wspólnik':<20} {'Equity':<10} {'Vested':<10} {'Status':<15}")
        print("-" * 55)
        
        for founder in self.game_state.company.founders:
            vesting = self.game_state.founders_agreement.vesting_schedule
            vested = vesting.calculate_vested(founder.months_in_company)
            vested_equity = founder.equity_percentage * vested / 100
            
            status = "Aktywny"
            if founder.left_company:
                status = "Good leaver" if founder.is_good_leaver else "Bad leaver"
            elif founder.months_in_company < vesting.cliff_months:
                status = f"Cliff ({founder.months_in_company}/{vesting.cliff_months} mies.)"
            
            print(f"{founder.name:<20} {founder.equity_percentage:>7.1f}%  {vested_equity:>7.1f}%  {status:<15}")
        
        print(f"\n{'ESOP Pool':<20} {self.game_state.company.esop_pool_percentage:>7.1f}%")
        print("-" * 55)
        total = sum(f.equity_percentage for f in self.game_state.company.founders) + self.game_state.company.esop_pool_percentage
        print(f"{'RAZEM':<20} {total:>7.1f}%")
    
    def do_umowa(self, arg):
        """Pokazuje status umowy wspólników"""
        if not self.game_state:
            print(colored("Najpierw rozpocznij grę komendą 'start'", Colors.RED))
            return
        
        agreement = self.game_state.founders_agreement
        vesting = agreement.vesting_schedule
        
        status = [
            f"Status: {'✓ PODPISANA' if agreement.signed else '✗ NIEPODPISANA'}",
            "",
            "VESTING:",
            f"  • Okres: {vesting.total_months} miesięcy",
            f"  • Cliff: {vesting.cliff_months} miesięcy ({vesting.cliff_percentage}%)",
            f"  • Po cliff: {vesting.monthly_percentage_after_cliff:.2f}%/miesiąc",
            "",
            "KLAUZULE OCHRONNE:",
            f"  • Tag-along: {'✓' if agreement.has_tag_along else '✗'}",
            f"  • Drag-along: {'✓' if agreement.has_drag_along else '✗'}",
            f"  • Good/Bad leaver: {'✓' if agreement.has_good_bad_leaver else '✗'}",
            f"  • Przypisanie IP: {'✓' if agreement.has_ip_assignment else '✗'}",
            f"  • Zakaz konkurencji: {'✓' if agreement.has_non_compete else '✗'}" + (f" ({agreement.non_compete_months} mies.)" if agreement.has_non_compete else ""),
            f"  • NDA: {'✓' if agreement.has_nda else '✗'}",
            f"  • Deadlock resolution: {'✓' if agreement.has_deadlock_resolution else '✗'}"
        ]
        
        print_box("UMOWA WSPÓLNIKÓW", status, Colors.CYAN)
        
        missing = agreement.get_missing_protections()
        if missing:
            print(colored("\n⚠️  BRAKUJĄCE ZABEZPIECZENIA:", Colors.RED))
            for m in missing:
                print(f"   • {m}")
            print(colored("\n   Rekomendacja: Uzupełnij umowę u prawnika (koszt: 3-8k PLN)", Colors.YELLOW))
    
    def do_miesiac(self, arg):
        """Przechodzi do następnego miesiąca"""
        if not self.game_state:
            print(colored("Najpierw rozpocznij grę komendą 'start'", Colors.RED))
            return
        
        self.game_state.advance_month()
        month = self.game_state.current_month
        
        print(colored(f"\n{'='*40}", Colors.CYAN))
        print(colored(f"  MIESIĄC {month}", Colors.BOLD))
        print(colored(f"{'='*40}\n", Colors.CYAN))
        
        # Symuluj wzrost (podstawowy)
        self._simulate_month()
        
        # Losowe zdarzenie
        if self.game_state.random_events_enabled and self.scenario_engine:
            event = self.scenario_engine.generate_random_event(self.game_state)
            if event:
                self._handle_event(event)
        
        # Pokaż podsumowanie miesiąca
        self._show_month_summary()
        
        # Sprawdź warunki gry
        self._check_game_conditions()
    
    def _simulate_month(self):
        """Symuluje typowy miesiąc działalności"""
        company = self.game_state.company
        
        # Podstawowy wzrost klientów i MRR
        if company.total_customers > 0:
            # Organiczny wzrost 5-15%
            growth_rate = random.uniform(0.05, 0.15)
            new_customers = int(company.total_customers * growth_rate)
            company.total_customers += new_customers
            
            # MRR per customer (uproszczone)
            avg_mrr_per_customer = company.mrr / max(1, company.paying_customers) if company.paying_customers > 0 else 200
            company.mrr += new_customers * avg_mrr_per_customer
            company.paying_customers += new_customers
        
        # Burn gotówki
        net_burn = company.monthly_burn_rate - company.mrr
        company.cash_on_hand -= max(0, net_burn)
        
        # Aktualizuj wycenę (uproszczone: 5x ARR)
        if company.mrr > 0:
            company.current_valuation = company.mrr * 12 * 5
    
    def _handle_event(self, event):
        """Obsługuje losowe zdarzenie"""
        color = Colors.GREEN if event.event_type.value == "positive" else Colors.RED
        
        print(colored(f"\n🎲 ZDARZENIE: {event.name}", color))
        print(f"   {event.description}")
        
        # Zastosuj efekty
        changes = event.apply_to_company(self.game_state.company)
        
        if changes:
            print(colored("\n   Efekty:", Colors.CYAN))
            for key, value in changes.items():
                print(f"   • {key}: {value}")
        
        # Zapisz w historii
        self.game_state.events_history.append(event)
        
        # Jeśli wymaga decyzji
        if event.requires_decision:
            print(colored("\n   ⚠️  To zdarzenie wymaga Twojej decyzji!", Colors.YELLOW))
            print("   Wpisz 'decyzja' aby zobaczyć opcje.")
    
    def _show_month_summary(self):
        """Pokazuje podsumowanie miesiąca"""
        company = self.game_state.company
        
        print(colored("\n📊 PODSUMOWANIE MIESIĄCA:", Colors.CYAN))
        print(f"   MRR: {company.mrr:,.0f} PLN")
        print(f"   Klienci: {company.total_customers}")
        print(f"   Gotówka: {company.cash_on_hand:,.0f} PLN")
        print(f"   Runway: {company.runway_months()} miesięcy")
    
    def _check_game_conditions(self):
        """Sprawdza warunki końca gry"""
        company = self.game_state.company
        
        # Bankructwo
        if company.cash_on_hand < 0:
            print(colored("\n💀 GAME OVER: Skończyła się gotówka!", Colors.RED))
            print("   Twoja firma zbankrutowała.")
            self._show_lessons_learned()
            return
        
        # Sukces - osiągnięcie celów
        if company.mrr >= self.config.target_mrr_12_months and company.total_customers >= self.config.target_customers_12_months:
            print(colored("\n🎉 SUKCES! Osiągnąłeś cele biznesowe!", Colors.GREEN))
            self._show_final_summary()
    
    def do_nauka(self, arg):
        """Materiały edukacyjne"""
        topics = [
            "1. Formy prawne (PSA vs Sp. z o.o.)",
            "2. Vesting i cliff",
            "3. Good/bad leaver",
            "4. Tag-along i drag-along",
            "5. Ochrona IP",
            "6. Walidacja partnera",
            "7. Wycena MVP",
            "8. Podział equity"
        ]
        
        print_box("MATERIAŁY EDUKACYJNE", topics, Colors.CYAN)
        
        choice = self._ask("Wybierz temat (1-8) lub 'wróć':", default="wróć")
        
        if choice == "1":
            self._learn_legal_forms()
        elif choice == "2":
            self._learn_vesting()
        elif choice == "3":
            self._learn_leaver()
        elif choice == "4":
            self._learn_tag_drag()
        elif choice == "5":
            self._learn_ip()
        elif choice == "6":
            self._learn_partner_validation()
        elif choice == "7":
            self._learn_mvp_valuation()
        elif choice == "8":
            self._learn_equity()
    
    def _learn_legal_forms(self):
        """Edukacja o formach prawnych"""
        content = """
    PROSTA SPÓŁKA AKCYJNA (PSA)
    ════════════════════════════
    Wprowadzona w 2021, idealna dla startupów.
    
    ✓ Kapitał minimalny: 1 PLN
    ✓ Praca może być wkładem
    ✓ Zbycie akcji e-mailem
    ✓ Łatwy vesting i ESOP
    ✓ Akcje założycielskie chronią głosy
    
    ✗ Koszt rejestru akcjonariuszy: 1500-3000 PLN/rok
    ✗ Mniej orzecznictwa sądowego
    
    SPÓŁKA Z O.O.
    ════════════════════════════
    Klasyczna forma, bardzo popularna.
    
    ✓ Ugruntowane orzecznictwo
    ✓ Rozpoznawalność
    ✓ Brak dodatkowych kosztów rocznych
    
    ✗ Kapitał minimalny: 5000 PLN
    ✗ Praca NIE może być wkładem
    ✗ Zbycie wymaga notariusza
    ✗ Skomplikowany ESOP
    
    REKOMENDACJA:
    → Startup z VC/equity: PSA
    → Bootstrapping bez equity: Sp. z o.o.
        """
        print(colored(content, Colors.CYAN))
    
    def _learn_vesting(self):
        """Edukacja o vestingu"""
        content = """
    VESTING - Stopniowe nabywanie udziałów
    ════════════════════════════════════════
    
    CZYM JEST VESTING?
    Mechanizm, który powoduje, że udziały są nabywane
    stopniowo przez określony czas pracy w firmie.
    
    STANDARD RYNKOWY:
    • Okres: 48 miesięcy (4 lata)
    • Cliff: 12 miesięcy (1 rok)
    • Po cliff: równomierne miesięczne nabywanie
    
    PRZYKŁAD (35% udziałów, 4 lata, 1 rok cliff):
    ┌─────────────┬─────────────────────────────┐
    │ Miesiąc 1-11│ 0% vested (okres cliff)     │
    │ Miesiąc 12  │ 8.75% (25% × 35%)           │
    │ Miesiąc 13+ │ +0.73%/miesiąc              │
    │ Miesiąc 48  │ 100% = 35% udziałów         │
    └─────────────┴─────────────────────────────┘
    
    REVERSE VESTING (w Polsce):
    W sp. z o.o. founder od razu ma udziały, ale
    zobowiązuje się do ich "zwrotu" jeśli odejdzie
    przed końcem vestingu.
    
    DLACZEGO TO WAŻNE?
    Chroni przed sytuacją, gdy współzałożyciel
    odchodzi po 2 miesiącach z 30% firmy.
        """
        print(colored(content, Colors.CYAN))
    
    def _learn_leaver(self):
        """Edukacja o good/bad leaver"""
        content = """
    GOOD LEAVER / BAD LEAVER
    ════════════════════════════════════════
    
    GOOD LEAVER - odejście "bez winy":
    • Śmierć lub trwała niezdolność
    • Odejście za zgodą zarządu/rady
    • Choroba uniemożliwiająca pracę
    • Redukcja z przyczyn firmy
    
    → KONSEKWENCJE: Zachowujesz vested equity
    → Sprzedaż po cenie rynkowej
    
    BAD LEAVER - odejście "z winą":
    • Naruszenie zakazu konkurencji
    • Rażące naruszenie obowiązków
    • Działanie na szkodę spółki
    • Dobrowolne odejście przed cliffem
    • Zwolnienie dyscyplinarne
    
    → KONSEKWENCJE: 
    → Utrata wszystkich udziałów, LUB
    → Wykup po 10-50% wartości nominalnej
    
    CO NEGOCJOWAĆ?
    1. Precyzyjne, zamknięte definicje
    2. "Voluntary good leaver" po pełnym vestingu
    3. Grace period na naprawę naruszeń
    4. Minimalną cenę nawet dla bad leaver
        """
        print(colored(content, Colors.CYAN))
    
    def _learn_tag_drag(self):
        """Edukacja o tag-along i drag-along"""
        content = """
    TAG-ALONG I DRAG-ALONG
    ════════════════════════════════════════
    
    TAG-ALONG (Prawo przyłączenia)
    ─────────────────────────────
    Mniejszościowy wspólnik może DOŁĄCZYĆ do
    transakcji sprzedaży większościowego.
    
    PRZYKŁAD:
    Partner (40%) sprzedaje swoje udziały za 1M PLN.
    Ty (35%) możesz zażądać, żeby kupiec kupił
    też TWOJE udziały po tej samej cenie za udział.
    
    → KLUCZOWE dla technical co-foundara!
    → Chroni przed byciem "uwięzionym" w firmie
    
    DRAG-ALONG (Prawo pociągnięcia)
    ───────────────────────────────
    Większościowy wspólnik może ZMUSIĆ
    mniejszościowych do sprzedaży.
    
    PRZYKŁAD:
    Ty + partner łącznie macie 75%.
    Kupiec chce 100% firmy.
    Możecie zmusić pozostałych wspólników
    do sprzedaży na tych samych warunkach.
    
    → Ułatwia exit dla całej spółki
    → Zapobiega blokowaniu przez mniejszość
        """
        print(colored(content, Colors.CYAN))
    
    def _learn_ip(self):
        """Edukacja o ochronie IP"""
        content = """
    OCHRONA WŁASNOŚCI INTELEKTUALNEJ (IP)
    ════════════════════════════════════════
    
    BACKGROUND IP vs FOREGROUND IP
    ─────────────────────────────────
    Background IP: To co stworzyłeś PRZED współpracą
                  (biblioteki, frameworki, MVP)
                  → Pozostaje TWOJE
                  → Licencjonuj, nie przenoś!
    
    Foreground IP: To co tworzysz W TRAKCIE współpracy
                  → Powinno należeć do spółki
    
    KLUCZOWE ZASADY:
    1. Przy B2B kod domyślnie należy do CIEBIE
       (wymaga wyraźnego przeniesienia)
    
    2. Przy UoP kod automatycznie należy do pracodawcy
       (art. 74 prawa autorskiego)
    
    3. Wszystkie pola eksploatacji muszą być wymienione
    
    4. Moment przeniesienia = moment zapłaty/objęcia udziałów
    
    LICENCJA WARUNKOWA (dla MVP):
    ───────────────────────────────
    Jeśli wnosisz gotowe MVP:
    1. NIE przenoś praw od razu
    2. Udziel licencji pod warunkiem założenia spółki
    3. Licencja wygasa jeśli warunki nie są spełnione
    
    → Art. 89-94 KC pozwala na warunek zawieszający
        """
        print(colored(content, Colors.CYAN))
    
    def _learn_partner_validation(self):
        """Edukacja o walidacji partnera"""
        content = """
    WERYFIKACJA PARTNERA BIZNESOWEGO
    ════════════════════════════════════════
    
    GDZIE SPRAWDZIĆ?
    ────────────────
    1. KRS: ekrs.ms.gov.pl
       → Historia spółek, upadłości, zarządy
    
    2. CEIDG: aplikacja.ceidg.gov.pl
       → Działalność gospodarcza
    
    3. Rejestry dłużników (30-50 PLN):
       → BIG InfoMonitor
       → Krajowy Rejestr Długów
       → ERIF BIG
    
    4. LinkedIn / Google
       → Spójność z deklaracjami
       → Referencje
    
    RED FLAGS 🚩
    ────────────
    • "Mam genialny pomysł, potrzebuję tylko kodera"
    • "Ustalimy procent udziałów później"
    • Partner nie wkłada żadnego kapitału
    • Wiele upadłych spółek w historii
    • Partner chce wynagrodzenie, ty nie
    • "Inwestor już czeka" bez term sheet
    • Brak wywiadów z klientami
    
    PYTANIA DO ZADANIA:
    ─────────────────────
    • Ile własnych pieniędzy zainwestowałeś?
    • Jaki masz runway?
    • Ile wywiadów z klientami przeprowadziłeś?
    • Czy masz pre-ordery/płacących klientów?
    • Jakie startupy zakładałeś wcześniej?
        """
        print(colored(content, Colors.CYAN))
    
    def _learn_mvp_valuation(self):
        """Edukacja o wycenie MVP"""
        content = """
    WYCENA MVP METODĄ KOSZTOWĄ
    ════════════════════════════════════════
    
    FORMUŁA:
    ────────
    Wartość = (Godziny × Stawka) + Koszty zewnętrzne
    
    STAWKI RYNKOWE (2024-2025):
    ───────────────────────────
    • Junior:  60-80 PLN/h
    • Mid:     80-120 PLN/h
    • Senior:  120-200 PLN/h
    • Lead:    180-300 PLN/h
    
    PRZYKŁAD:
    ─────────
    400h pracy senior (150 PLN/h) = 60 000 PLN
    UI/UX 80h (120 PLN/h)         =  9 600 PLN
    Serwery 12 mies.              = 10 000 PLN
    ────────────────────────────────────────
    RAZEM                         = 79 600 PLN
    
    CO TO OZNACZA DLA EQUITY?
    ─────────────────────────
    Jeśli wnosisz MVP warte 80 000 PLN,
    a partner wnosi 20 000 PLN kapitału,
    to fair podział to ~80/20 (przed ESOP).
    
    UWAGA: Pomysł BEZ WALIDACJI to max 5-10% wartości!
    Sam pomysł nie jest wart połowy firmy.
        """
        print(colored(content, Colors.CYAN))
    
    def _learn_equity(self):
        """Edukacja o podziale equity"""
        content = """
    PODZIAŁ EQUITY MIĘDZY FOUNDERAMI
    ════════════════════════════════════════
    
    KIEDY 50/50?
    ────────────
    TYLKO gdy obaj wnoszą równy wkład od początku.
    Częsty błąd → "bo jesteśmy przyjaciółmi"
    
    TYPOWE SCENARIUSZE:
    ────────────────────
    │ Sytuacja                    │ Tech │ Biz │
    ├─────────────────────────────┼──────┼─────┤
    │ Programista z gotowym MVP   │ 55-70│30-45│
    │ Wspólny start od zera       │ 50-60│40-50│
    │ Programista za equity only  │ 30-40│60-70│
    └─────────────────────────────┴──────┴─────┘
    
    ESOP POOL (5-15%):
    ──────────────────
    Rezerwa na przyszłych pracowników.
    Pobierana proporcjonalnie od wszystkich founderów.
    Bez niej → konflikt przy zatrudnianiu.
    
    ROZWODNIENIE:
    ─────────────
    Przy każdej rundzie inwestycyjnej Twój % spada.
    ALE wartość może ROSNĄĆ!
    
    Przykład:
    Start: 50% przy wycenie 500k = 250k PLN
    Po rundzie: 35% przy wycenie 5M = 1.75M PLN
    
    → Mniejszy kawałek WIĘKSZEGO tortu
        """
        print(colored(content, Colors.CYAN))
    
    def do_slownik(self, arg):
        """Słownik pojęć"""
        terms = {
            "MRR": "Monthly Recurring Revenue - miesięczny przychód cykliczny",
            "ARR": "Annual Recurring Revenue - roczny przychód cykliczny (MRR × 12)",
            "Runway": "Ile miesięcy firma może działać przy obecnym burn rate",
            "Burn rate": "Miesięczne wydatki przewyższające przychody",
            "Vesting": "Stopniowe nabywanie udziałów w czasie",
            "Cliff": "Minimalny okres przed nabyciem jakichkolwiek udziałów",
            "ESOP": "Employee Stock Option Pool - pula udziałów dla pracowników",
            "Cap table": "Tabela kapitalizacji - podział udziałów w firmie",
            "Dilution": "Rozwodnienie - spadek % udziałów przy nowej emisji",
            "Term sheet": "Wstępne warunki inwestycji (niewiążący)",
            "Due diligence": "Weryfikacja firmy/osoby przed transakcją",
            "PMF": "Product-Market Fit - dopasowanie produktu do rynku",
            "PSA": "Prosta Spółka Akcyjna",
            "SHA": "Shareholders Agreement - umowa wspólników",
            "LOI": "Letter of Intent - list intencyjny",
            "IP": "Intellectual Property - własność intelektualna",
            "Background IP": "IP stworzone przed współpracą",
            "Foreground IP": "IP stworzone w trakcie współpracy"
        }
        
        print(colored("\n📚 SŁOWNIK POJĘĆ\n", Colors.CYAN))
        for term, definition in sorted(terms.items()):
            print(f"  {colored(term, Colors.GREEN)}: {definition}")
    
    # =========================================================================
    # ZAPIS I WCZYTYWANIE
    # =========================================================================
    
    def do_zapisz(self, arg):
        """Zapisuje grę"""
        if not self.game_state or not self.config:
            print(colored("Brak gry do zapisania.", Colors.RED))
            return
        
        filename = arg or f"save_{self.game_state.id}.yaml"
        filepath = self.save_dir / filename
        
        save_data = {
            'config': self.config.to_dict(),
            'game_state': self.game_state.get_summary(),
            'saved_at': datetime.now().isoformat()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(save_data, f, allow_unicode=True, default_flow_style=False)
        
        print(colored(f"✓ Gra zapisana: {filepath}", Colors.GREEN))
    
    def do_eksport(self, arg):
        """Eksportuje konfigurację do YAML"""
        if not self.config:
            print(colored("Brak konfiguracji do eksportu.", Colors.RED))
            return
        
        filename = arg or f"config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
        filepath = self.save_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(self.config.to_dict(), f, allow_unicode=True, default_flow_style=False)
        
        print(colored(f"✓ Konfiguracja wyeksportowana: {filepath}", Colors.GREEN))
        print("\nMożesz użyć tego pliku do:")
        print("  • Dokumentacji założeń")
        print("  • Dyskusji z prawnikiem")
        print("  • Negocjacji z partnerem")
    
    def do_wczytaj(self, arg):
        """Wczytuje zapisaną grę"""
        saves = list(self.save_dir.glob("save_*.yaml"))
        
        if not saves:
            print(colored("Brak zapisanych gier.", Colors.YELLOW))
            return
        
        print(colored("\n📂 ZAPISANE GRY:\n", Colors.CYAN))
        for i, save in enumerate(saves, 1):
            print(f"  {i}. {save.name}")
        
        choice = self._ask("Wybierz numer lub 'wróć':", default="wróć")
        
        if choice.isdigit() and 1 <= int(choice) <= len(saves):
            filepath = saves[int(choice) - 1]
            # TODO: Implementacja pełnego wczytywania stanu
            print(colored(f"✓ Wczytano: {filepath}", Colors.GREEN))
    
    # =========================================================================
    # POMOCNICZE
    # =========================================================================
    
    def _ask(self, prompt: str, default: str = "") -> str:
        """Zadaje pytanie z domyślną wartością"""
        if default:
            response = input(f"{prompt} [{default}]: ").strip()
            return response if response else default
        return input(f"{prompt}: ").strip()
    
    def _ask_int(self, prompt: str, default: int = 0) -> int:
        """Zadaje pytanie o liczbę całkowitą"""
        while True:
            response = self._ask(prompt, str(default))
            try:
                return int(response)
            except ValueError:
                print(colored("Podaj liczbę całkowitą.", Colors.RED))
    
    def _ask_float(self, prompt: str, default: float = 0.0) -> float:
        """Zadaje pytanie o liczbę zmiennoprzecinkową"""
        while True:
            response = self._ask(prompt, str(default))
            try:
                return float(response)
            except ValueError:
                print(colored("Podaj liczbę.", Colors.RED))
    
    def _show_lessons_learned(self):
        """Pokazuje wnioski po zakończeniu gry"""
        print(colored("\n📚 WNIOSKI Z GRY:", Colors.YELLOW))
        
        # Analiza błędów
        if not self.game_state.founders_agreement.signed:
            print("  • Brak umowy wspólników → Nie masz żadnych zabezpieczeń")
        
        if self.game_state.company.runway_months() < 3:
            print("  • Za krótki runway → Planuj finansowanie z wyprzedzeniem")
        
        if not self.game_state.partner_verified:
            print("  • Niezweryfikowany partner → Zawsze sprawdzaj w KRS i rejestrach")
    
    def _show_final_summary(self):
        """Podsumowanie końcowe"""
        print(colored("\n🏆 PODSUMOWANIE KOŃCOWE:", Colors.GREEN))
        summary = self.game_state.get_summary()
        
        print(f"  Miesięcy działalności: {summary['month']}")
        print(f"  Końcowe MRR: {summary['mrr']:,.0f} PLN")
        print(f"  Końcowa liczba klientów: {summary['customers']}")
        print(f"  Końcowa wycena: {summary['valuation']:,.0f} PLN")
        print(f"  Zdarzenia: {summary['events_count']}")
        print(f"  Podjęte decyzje: {summary['decisions_count']}")
    
    def default(self, line):
        """Obsługa nieznanych komend"""
        print(colored(f"Nieznana komenda: {line}", Colors.RED))
        print("Wpisz 'pomoc' aby zobaczyć dostępne komendy.")
    
    def emptyline(self):
        """Nie powtarzaj ostatniej komendy"""
        pass


def main():
    """Punkt wejścia"""
    try:
        shell = BiznesShell()
        shell.cmdloop()
    except KeyboardInterrupt:
        print(colored("\n\nDo zobaczenia!", Colors.CYAN))
        sys.exit(0)


if __name__ == "__main__":
    main()
