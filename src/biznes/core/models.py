"""
Biznes - Modele danych dla gry
Wszystkie struktury reprezentujące stan gry, founderów, spółkę i zdarzenia
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Dict, List, Any
from datetime import datetime
import uuid


class LegalForm(Enum):
    """Formy prawne działalności"""
    PSA = "psa"
    SP_ZOO = "sp_zoo"
    JDG = "jdg"
    NONE = "none"


class EmploymentForm(Enum):
    """Formy zatrudnienia/współpracy"""
    B2B = "b2b"
    UOP = "uop"
    SHAREHOLDER_ONLY = "shareholder_only"


class StartupStage(Enum):
    """Etapy rozwoju startupu"""
    IDEA = "idea"
    PRE_SEED = "pre_seed"
    SEED = "seed"
    SERIES_A = "series_a"
    GROWTH = "growth"
    EXIT = "exit"


class EventType(Enum):
    """Typy zdarzeń losowych"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class DecisionCategory(Enum):
    """Kategorie decyzji"""
    LEGAL = "legal"
    FINANCIAL = "financial"
    PARTNERSHIP = "partnership"
    PRODUCT = "product"
    TEAM = "team"
    STRATEGIC = "strategic"


class RiskLevel(Enum):
    """Poziomy ryzyka"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ActionMode:
    name: str
    cost: int = 0
    time_cost: int = 1
    success_rate: float = 1.0
    quality_modifier: float = 1.0
    requires_skill: Optional[str] = None


@dataclass
class Founder:
    """Reprezentacja założyciela"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    role: str = ""  # "technical" lub "business"
    equity_percentage: float = 0.0
    vested_percentage: float = 0.0
    cliff_completed: bool = False
    months_in_company: int = 0
    initial_investment: float = 0.0
    monthly_salary: float = 0.0
    employment_form: EmploymentForm = EmploymentForm.B2B
    skills: List[str] = field(default_factory=list)
    experience_years: int = 0
    runway_months: int = 0
    commitment_hours_weekly: int = 0
    has_other_job: bool = False
    # Portfel osobisty foundera
    personal_cash: float = 0.0  # Gotówka osobista
    personal_invested: float = 0.0  # Ile zainwestował w firmę
    total_received: float = 0.0  # Ile otrzymał z firmy (wypłaty)
    contacts_count: int = 0  # Ile kontaktów wniósł
    mvp_value: float = 0.0  # Wartość wniesionego MVP
    brought_mvp: bool = False
    background_ip: List[str] = field(default_factory=list)
    
    # Flagi weryfikacji
    krs_verified: bool = False
    debtor_registry_verified: bool = False
    references_verified: bool = False
    
    # Status
    is_player: bool = False  # Czy to gracz
    is_good_leaver: Optional[bool] = None
    left_company: bool = False
    left_month: Optional[int] = None


@dataclass
class VestingSchedule:
    """Harmonogram vestingu"""
    total_months: int = 48
    cliff_months: int = 12
    cliff_percentage: float = 25.0
    monthly_percentage_after_cliff: float = 2.083
    accelerated_vesting_on_acquisition: bool = False
    
    def calculate_vested(self, months: int) -> float:
        """Oblicza procent zvested po X miesiącach"""
        if months < self.cliff_months:
            return 0.0
        
        cliff_vested = self.cliff_percentage
        months_after_cliff = months - self.cliff_months
        remaining_to_vest = 100.0 - self.cliff_percentage
        months_for_remaining = self.total_months - self.cliff_months
        
        if months_after_cliff >= months_for_remaining:
            return 100.0
        
        additional = (months_after_cliff / months_for_remaining) * remaining_to_vest
        return min(100.0, cliff_vested + additional)


@dataclass
class FoundersAgreement:
    """Umowa wspólników"""
    signed: bool = False
    date_signed: Optional[datetime] = None
    
    # Klauzule
    vesting_schedule: VestingSchedule = field(default_factory=VestingSchedule)
    has_tag_along: bool = False
    has_drag_along: bool = False
    has_good_bad_leaver: bool = False
    has_ip_assignment: bool = False
    has_non_compete: bool = False
    non_compete_months: int = 0
    has_nda: bool = False
    nda_penalty: float = 0.0
    has_deadlock_resolution: bool = False
    has_sunset_clause: bool = False
    sunset_months: int = 12
    
    # Licencja warunkowa (dla MVP)
    conditional_license: bool = False
    license_conditions: List[str] = field(default_factory=list)
    license_expiry_months: int = 6
    
    # Milestone-based IP transfer
    milestone_based_ip: bool = False
    ip_milestones: List[Dict] = field(default_factory=list)
    
    def get_missing_protections(self) -> List[str]:
        """Zwraca listę brakujących zabezpieczeń"""
        missing = []
        if not self.has_tag_along:
            missing.append("Tag-along (prawo przyłączenia)")
        if not self.has_good_bad_leaver:
            missing.append("Klauzule good/bad leaver")
        if not self.has_ip_assignment:
            missing.append("Przypisanie własności intelektualnej")
        if not self.has_non_compete:
            missing.append("Zakaz konkurencji")
        if not self.has_nda:
            missing.append("Klauzula poufności (NDA)")
        if not self.has_deadlock_resolution:
            missing.append("Procedura rozwiązywania impasów")
        return missing


@dataclass
class Company:
    """Reprezentacja spółki"""
    name: str = ""
    legal_form: LegalForm = LegalForm.NONE
    registered: bool = False
    registration_date: Optional[datetime] = None
    
    # Kapitał
    share_capital: float = 0.0
    esop_pool_percentage: float = 0.0
    
    # Finanse
    cash_on_hand: float = 0.0
    monthly_burn_rate: float = 0.0
    mrr: float = 0.0
    arr: float = 0.0

    cost_multiplier: float = 1.0
    extra_monthly_costs: float = 0.0
    
    # Klienci
    total_customers: int = 0
    paying_customers: int = 0
    monthly_churn_rate: float = 0.0
    
    # Produkt
    mvp_completed: bool = False
    product_market_fit: bool = False
    
    # Zespół
    founders: List[Founder] = field(default_factory=list)
    employees: int = 0
    
    # Inwestycje
    total_raised: float = 0.0
    current_valuation: float = 0.0
    investors: List[Dict] = field(default_factory=list)
    
    # Status
    stage: StartupStage = StartupStage.IDEA
    months_active: int = 0
    
    def runway_months(self) -> int:
        """Oblicza ile miesięcy firma może działać"""
        if self.monthly_burn_rate <= 0:
            return 999
        net_burn = self.monthly_burn_rate - self.mrr
        if net_burn <= 0:
            return 999
        return int(self.cash_on_hand / net_burn)
    
    def get_founder_by_role(self, role: str) -> Optional[Founder]:
        """Znajduje foundera po roli"""
        for f in self.founders:
            if f.role == role:
                return f
        return None


@dataclass
class GameEvent:
    """Zdarzenie w grze"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""
    event_type: EventType = EventType.NEUTRAL
    month: int = 0
    
    # Efekty
    mrr_change: float = 0.0
    mrr_multiplier: float = 1.0
    customers_change: int = 0
    customers_multiplier: float = 1.0
    cash_change: float = 0.0
    burn_rate_change: float = 0.0
    valuation_multiplier: float = 1.0
    morale_change: int = 0
    credibility_change: int = 0
    
    # Wymagane akcje
    requires_decision: bool = False
    decision_options: List[Dict] = field(default_factory=list)
    
    # Flagi
    triggers_pivot: bool = False
    triggers_conflict: bool = False
    
    def apply_to_company(self, company: Company) -> Dict[str, Any]:
        """Aplikuje efekty zdarzenia na spółkę"""
        changes = {}
        
        if self.mrr_change != 0:
            company.mrr += self.mrr_change
            changes['mrr'] = self.mrr_change
            
        if self.mrr_multiplier != 1.0:
            old_mrr = company.mrr
            company.mrr *= self.mrr_multiplier
            changes['mrr_multiplier'] = f"{old_mrr} -> {company.mrr}"
            
        if self.customers_change != 0:
            company.total_customers += self.customers_change
            changes['customers'] = self.customers_change
            
        if self.customers_multiplier != 1.0:
            old_customers = company.total_customers
            company.total_customers = int(company.total_customers * self.customers_multiplier)
            changes['customers_multiplier'] = f"{old_customers} -> {company.total_customers}"
            
        if self.cash_change != 0:
            company.cash_on_hand += self.cash_change
            changes['cash'] = self.cash_change
            
        if self.burn_rate_change != 0:
            company.extra_monthly_costs += self.burn_rate_change
            changes['burn_rate'] = self.burn_rate_change
            
        if self.valuation_multiplier != 1.0:
            old_val = company.current_valuation
            company.current_valuation *= self.valuation_multiplier
            changes['valuation'] = f"{old_val} -> {company.current_valuation}"
            
        return changes


@dataclass
class ActionPointSystem:
    base_points: int = 4

    def get_monthly_points(self, state: "GameState") -> int:
        c = state.company

        points = self.base_points
        points += min(2, c.employees)

        if any((not f.is_player) and (not f.left_company) for f in c.founders):
            points += 2

        if c.runway_months() < 3:
            points -= 1

        return max(1, points)


class CostCalculator:
    def calculate_monthly_burn(self, state: "GameState") -> Dict[str, int]:
        c = state.company
        costs: Dict[str, int] = {}

        costs['founder_living'] = 3000

        if c.registered:
            costs['accounting'] = 1000
            costs['krs_registry'] = 200
            if c.legal_form == LegalForm.PSA:
                costs['shareholder_registry'] = 150

        if state.agreement_signed:
            costs['legal_retainer'] = 500

        if c.mvp_completed or state.mvp_progress > 0:
            costs['hosting'] = int(300 + (c.paying_customers * 10))
            costs['tools'] = 200

        costs['employees'] = int(c.employees * 12000)

        if c.paying_customers > 10:
            costs['support'] = int(c.mrr * 0.05)
        if c.paying_customers > 50:
            costs['infrastructure'] = int(c.mrr * 0.10)

        costs = {k: int(v) for k, v in costs.items() if int(v) != 0}
        return costs

    def total_burn(self, state: "GameState") -> int:
        c = state.company
        base = sum(self.calculate_monthly_burn(state).values())
        total = (base * c.cost_multiplier) + c.extra_monthly_costs
        return int(max(0, total))


@dataclass
class Decision:
    """Decyzja gracza"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    category: DecisionCategory = DecisionCategory.STRATEGIC
    title: str = ""
    description: str = ""
    month: int = 0
    
    # Opcje
    options: List[Dict] = field(default_factory=list)
    selected_option: Optional[int] = None
    
    # Analiza ryzyka
    risk_level: RiskLevel = RiskLevel.MEDIUM
    risk_description: str = ""
    opportunity_description: str = ""
    
    # Rekomendacja
    recommended_option: Optional[int] = None
    recommendation_reason: str = ""


@dataclass
class GameState:
    """Pełny stan gry"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    created_at: datetime = field(default_factory=datetime.now)
    last_saved: datetime = field(default_factory=datetime.now)
    
    # Stan gracza
    player_name: str = ""
    player_role: str = "technical"  # "technical" lub "business"
    
    # Główne obiekty
    company: Company = field(default_factory=Company)
    founders_agreement: FoundersAgreement = field(default_factory=FoundersAgreement)
    
    # Historia
    current_month: int = 0
    events_history: List[GameEvent] = field(default_factory=list)
    decisions_history: List[Decision] = field(default_factory=list)
    
    # Metryki gracza
    knowledge_points: int = 0
    risk_awareness_score: int = 0
    legal_understanding_score: int = 0
    
    # Flagi postępu
    partner_met: bool = False
    partner_verified: bool = False
    agreement_negotiated: bool = False
    agreement_signed: bool = False  # Czy SHA podpisana
    company_founded: bool = False
    first_customer: bool = False
    product_market_fit_achieved: bool = False
    
    # Postęp MVP
    mvp_progress: int = 0  # 0-100%
    
    # Oczekujące decyzje
    pending_investment: Optional[Dict] = None
    adding_partner: bool = False

    revenue_advance_months: int = 0
    revenue_advance_mrr: float = 0.0
    
    # Parametry symulacji
    simulation_speed: str = "normal"  # "fast", "normal", "detailed"
    random_events_enabled: bool = True
    difficulty: str = "normal"  # "easy", "normal", "hard"
    
    def advance_month(self):
        """Przesuwa grę o miesiąc"""
        self.current_month += 1
        self.company.months_active += 1
        
        # Aktualizuj vesting dla founderów
        for founder in self.company.founders:
            if not founder.left_company:
                founder.months_in_company += 1
                
        self.last_saved = datetime.now()
    
    def get_summary(self) -> Dict[str, Any]:
        """Zwraca podsumowanie stanu gry"""
        return {
            'month': self.current_month,
            'stage': self.company.stage.value if self.company.stage else 'idea',
            'mrr': self.company.mrr,
            'customers': self.company.total_customers,
            'runway': self.company.runway_months(),
            'cash': self.company.cash_on_hand,
            'valuation': self.company.current_valuation,
            'founders': len(self.company.founders),
            'agreement_signed': self.founders_agreement.signed,
            'company_registered': self.company.registered,
            'events_count': len(self.events_history),
            'decisions_count': len(self.decisions_history)
        }


@dataclass
class PlayerConfig:
    """Konfiguracja zapisywana do YAML"""
    # Dane gracza
    player_name: str = ""
    player_role: str = "technical"
    
    # Parametry wejściowe - sytuacja startowa
    has_mvp: bool = False
    player_has_mvp: bool = False  # Alias dla has_mvp
    mvp_hours_invested: int = 0
    mvp_hours: int = 0  # Alias
    mvp_hourly_rate: float = 150.0
    mvp_external_costs: float = 0.0
    mvp_calculated_value: float = 0.0
    
    # Parametry partnera
    has_partner: bool = False
    partner_name: str = ""
    partner_brings_capital: float = 0.0
    partner_capital: float = 0.0  # Alias
    partner_brings_customers: int = 0
    partner_has_customers: bool = False
    partner_industry_experience_years: int = 0
    partner_experience_years: int = 0  # Alias
    partner_startup_experience: int = 0
    partner_has_contacts: bool = False
    partner_verified_krs: bool = False
    partner_krs_verified: bool = False  # Alias
    partner_verified_debts: bool = False
    partner_debts_verified: bool = False  # Alias
    
    # Preferencje equity
    proposed_equity_split_player: float = 50.0
    player_equity: float = 50.0  # Alias
    proposed_equity_split_partner: float = 50.0
    partner_equity: float = 50.0  # Alias
    esop_pool: float = 10.0
    
    # Preferencje prawne
    preferred_legal_form: str = "psa"
    legal_form: str = "psa"  # Alias
    vesting_months: int = 48
    cliff_months: int = 12
    wants_tag_along: bool = True
    wants_good_bad_leaver: bool = True
    wants_ip_protection: bool = True
    wants_non_compete: bool = True
    non_compete_months: int = 12
    
    # Cele biznesowe
    target_mrr_6_months: float = 10000.0
    target_customers_6_months: int = 50
    target_mrr_12_months: float = 30000.0
    target_customers_12_months: int = 150
    
    # Zasoby
    personal_runway_months: int = 6
    personal_savings: float = 0.0
    initial_cash: float = 10000.0
    monthly_burn: float = 5000.0
    willing_to_work_without_salary: bool = False
    max_months_without_salary: int = 0
    
    # Preferencje symulacji
    enable_random_events: bool = True
    difficulty: str = "normal"
    detailed_explanations: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje do słownika dla YAML"""
        return {
            'player': {
                'name': self.player_name,
                'role': self.player_role,
            },
            'mvp': {
                'has_mvp': self.has_mvp,
                'hours_invested': self.mvp_hours_invested,
                'hourly_rate': self.mvp_hourly_rate,
                'external_costs': self.mvp_external_costs,
                'calculated_value': self.mvp_hours_invested * self.mvp_hourly_rate + self.mvp_external_costs
            },
            'partner': {
                'name': self.partner_name,
                'capital': self.partner_brings_capital,
                'customers': self.partner_brings_customers,
                'industry_experience_years': self.partner_industry_experience_years,
                'startup_experience': self.partner_startup_experience,
                'has_contacts': self.partner_has_contacts,
                'verified': {
                    'krs': self.partner_verified_krs,
                    'debts': self.partner_verified_debts
                }
            },
            'equity': {
                'player_percentage': self.proposed_equity_split_player,
                'partner_percentage': self.proposed_equity_split_partner,
                'esop_pool': self.esop_pool
            },
            'legal': {
                'preferred_form': self.preferred_legal_form,
                'vesting_months': self.vesting_months,
                'cliff_months': self.cliff_months,
                'protections': {
                    'tag_along': self.wants_tag_along,
                    'good_bad_leaver': self.wants_good_bad_leaver,
                    'ip_protection': self.wants_ip_protection,
                    'non_compete': self.wants_non_compete,
                    'non_compete_months': self.non_compete_months
                }
            },
            'targets': {
                '6_months': {
                    'mrr': self.target_mrr_6_months,
                    'customers': self.target_customers_6_months
                },
                '12_months': {
                    'mrr': self.target_mrr_12_months,
                    'customers': self.target_customers_12_months
                }
            },
            'resources': {
                'runway_months': self.personal_runway_months,
                'savings': self.personal_savings,
                'work_without_salary': self.willing_to_work_without_salary,
                'max_months_no_salary': self.max_months_without_salary
            },
            'simulation': {
                'random_events': self.enable_random_events,
                'difficulty': self.difficulty,
                'detailed_explanations': self.detailed_explanations
            }
        }
