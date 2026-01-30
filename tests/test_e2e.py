"""
Testy E2E dla gry Biznes - Symulator Startupu
Kompleksowe testy całego przepływu gry.
"""
import pytest
import random
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from biznes.core.models import (
    GameState, PlayerConfig, Company, Founder,
    LegalForm, FoundersAgreement, VestingSchedule,
    ActionMode, ActionPointSystem, CostCalculator,
    BusinessModel, MarketAnalysis, BUSINESS_MODELS, MARKET_CONFIGS,
    calculate_customer_acquisition_chance
)


class TestGameInitialization:
    """Testy inicjalizacji gry."""

    def test_create_game_state_with_defaults(self):
        """Test tworzenia stanu gry z domyślnymi wartościami."""
        state = GameState(player_name="Tester", player_role="technical")
        
        assert state.player_name == "Tester"
        assert state.player_role == "technical"
        assert state.current_month == 0
        assert state.company is not None
        assert state.founders_agreement is not None

    def test_create_company_with_founder(self):
        """Test tworzenia firmy z founderem."""
        company = Company(name="TestStartup")
        player = Founder(
            name="Jan Kowalski",
            role="technical",
            equity_percentage=60.0,
            is_player=True,
            personal_cash=20000.0
        )
        company.founders.append(player)
        
        assert len(company.founders) == 1
        assert company.founders[0].is_player is True
        assert company.founders[0].personal_cash == 20000.0

    def test_initialize_with_partner(self):
        """Test inicjalizacji z partnerem."""
        company = Company(name="TestStartup")
        player = Founder(name="Gracz", equity_percentage=55.0, is_player=True)
        partner = Founder(name="Partner", equity_percentage=35.0, is_player=False)
        company.founders.extend([player, partner])
        company.esop_pool_percentage = 10.0
        
        total_equity = sum(f.equity_percentage for f in company.founders) + company.esop_pool_percentage
        assert total_equity == 100.0
        assert len([f for f in company.founders if not f.is_player]) == 1

    def test_initialize_business_model(self):
        """Test inicjalizacji modelu biznesowego."""
        state = GameState()
        state.business_model = BUSINESS_MODELS.get("saas")
        
        assert state.business_model is not None
        assert state.business_model.model_type == "saas"
        assert state.business_model.vc_attractiveness == 5

    def test_initialize_market_analysis(self):
        """Test inicjalizacji analizy rynku."""
        state = GameState()
        state.market_analysis = MARKET_CONFIGS.get("growing")
        
        assert state.market_analysis is not None
        assert state.market_analysis.market_type == "growing"
        assert state.market_analysis.market_growth_rate == 0.15


class TestVestingMechanicsE2E:
    """Testy E2E mechaniki vestingu."""

    def test_vesting_progression_over_months(self):
        """Test progresji vestingu przez wiele miesięcy."""
        state = GameState()
        company = Company(name="Test")
        
        player = Founder(name="Gracz", equity_percentage=55.0, is_player=True)
        partner = Founder(name="Partner", equity_percentage=35.0, is_player=False)
        company.founders.extend([player, partner])
        
        state.company = company
        state.founders_agreement = FoundersAgreement(signed=True)
        
        vesting = state.founders_agreement.vesting_schedule
        
        # Symuluj 24 miesiące
        for month in range(24):
            state.advance_month()
        
        # Partner powinien mieć ukończony cliff (12 mies) i dodatkowe miesiące vestingu
        assert partner.months_in_company == 24
        assert partner.cliff_completed is True
        assert partner.vested_percentage > 0

    def test_vesting_before_cliff(self):
        """Test że przed clifem nic nie vestuje."""
        state = GameState()
        company = Company(name="Test")
        partner = Founder(name="Partner", equity_percentage=40.0, is_player=False)
        company.founders.append(partner)
        
        state.company = company
        state.founders_agreement = FoundersAgreement(signed=True)
        
        # 6 miesięcy - przed clifem
        for _ in range(6):
            state.advance_month()
        
        assert partner.months_in_company == 6
        assert partner.cliff_completed is False
        assert partner.vested_percentage == 0.0

    def test_vesting_at_cliff(self):
        """Test vestingu przy osiągnięciu clifu."""
        state = GameState()
        company = Company(name="Test")
        partner = Founder(name="Partner", equity_percentage=40.0, is_player=False)
        company.founders.append(partner)
        
        state.company = company
        state.founders_agreement = FoundersAgreement(signed=True)
        vesting = state.founders_agreement.vesting_schedule
        
        # Dokładnie cliff_months
        for _ in range(vesting.cliff_months):
            state.advance_month()
        
        assert partner.cliff_completed is True
        assert partner.vested_percentage == vesting.cliff_percentage

    def test_full_vesting_after_48_months(self):
        """Test pełnego vestingu po 48 miesiącach."""
        state = GameState()
        company = Company(name="Test")
        partner = Founder(name="Partner", equity_percentage=40.0, is_player=False)
        company.founders.append(partner)
        
        state.company = company
        state.founders_agreement = FoundersAgreement(signed=True)
        
        # 48 miesięcy
        for _ in range(48):
            state.advance_month()
        
        assert partner.vested_percentage == 100.0


class TestGoodBadLeaverE2E:
    """Testy E2E mechaniki good/bad leaver."""

    def test_good_leaver_keeps_vested_equity(self):
        """Test że good leaver zachowuje vested equity."""
        state = GameState()
        company = Company(name="Test")
        
        player = Founder(name="Gracz", equity_percentage=55.0, is_player=True)
        partner = Founder(name="Partner", equity_percentage=35.0, is_player=False)
        company.founders.extend([player, partner])
        
        state.company = company
        state.founders_agreement = FoundersAgreement(
            signed=True,
            has_good_bad_leaver=True
        )
        
        # 18 miesięcy - po clifie
        for _ in range(18):
            state.advance_month()
        
        vested_before = partner.vested_percentage
        equity_before = partner.equity_percentage
        
        result = state.process_founder_leaving(partner, is_good_leaver=True)
        
        assert partner.left_company is True
        assert partner.is_good_leaver is True
        expected_kept = (vested_before / 100.0) * equity_before
        assert abs(result['equity_kept'] - expected_kept) < 0.1

    def test_bad_leaver_before_cliff_loses_all(self):
        """Test że bad leaver przed clifem traci wszystko."""
        state = GameState()
        company = Company(name="Test")
        
        player = Founder(name="Gracz", equity_percentage=55.0, is_player=True)
        partner = Founder(name="Partner", equity_percentage=35.0, is_player=False)
        company.founders.extend([player, partner])
        
        state.company = company
        state.founders_agreement = FoundersAgreement(
            signed=True,
            has_good_bad_leaver=True
        )
        
        # 6 miesięcy - przed clifem
        for _ in range(6):
            state.advance_month()
        
        result = state.process_founder_leaving(partner, is_good_leaver=False)
        
        assert partner.left_company is True
        assert partner.is_good_leaver is False
        assert result['equity_kept'] == 0.0
        assert result['equity_returned'] == 35.0

    def test_bad_leaver_after_cliff_gets_discounted(self):
        """Test że bad leaver po clifie dostaje 50% vested."""
        state = GameState()
        company = Company(name="Test")
        
        player = Founder(name="Gracz", equity_percentage=55.0, is_player=True)
        partner = Founder(name="Partner", equity_percentage=35.0, is_player=False)
        company.founders.extend([player, partner])
        
        state.company = company
        state.founders_agreement = FoundersAgreement(
            signed=True,
            has_good_bad_leaver=True
        )
        
        # 18 miesięcy - po clifie
        for _ in range(18):
            state.advance_month()
        
        vested_before = partner.vested_percentage
        equity_before = partner.equity_percentage
        
        result = state.process_founder_leaving(partner, is_good_leaver=False)
        
        # Bad leaver po clifie: 50% vested
        expected_kept = (vested_before / 100.0) * equity_before * 0.5
        assert abs(result['equity_kept'] - expected_kept) < 0.1

    def test_no_sha_partner_keeps_all_equity(self):
        """Test że bez SHA partner zachowuje całe equity."""
        state = GameState()
        company = Company(name="Test")
        
        player = Founder(name="Gracz", equity_percentage=55.0, is_player=True)
        partner = Founder(name="Partner", equity_percentage=35.0, is_player=False)
        company.founders.extend([player, partner])
        
        state.company = company
        state.founders_agreement = FoundersAgreement(signed=False)  # Brak SHA!
        
        for _ in range(6):
            state.advance_month()
        
        result = state.process_founder_leaving(partner, is_good_leaver=False)
        
        assert 'warning' in result
        assert result['equity_kept'] == 35.0
        assert result['equity_returned'] == 0.0

    def test_equity_redistribution_after_leaving(self):
        """Test redystrybucji equity po odejściu partnera."""
        state = GameState()
        company = Company(name="Test")
        
        player = Founder(name="Gracz", equity_percentage=55.0, is_player=True)
        partner = Founder(name="Partner", equity_percentage=35.0, is_player=False)
        company.founders.extend([player, partner])
        
        state.company = company
        state.founders_agreement = FoundersAgreement(
            signed=True,
            has_good_bad_leaver=True
        )
        
        # 6 miesięcy - przed clifem, bad leaver traci wszystko
        for _ in range(6):
            state.advance_month()
        
        player_equity_before = player.equity_percentage
        
        result = state.process_founder_leaving(partner, is_good_leaver=False)
        
        # Zwrócone equity powinno trafić do gracza
        assert result['equity_returned'] == 35.0
        assert player.equity_percentage == player_equity_before + 35.0


class TestFounderPersonalFinanceE2E:
    """Testy E2E akcji portfela osobistego."""

    def test_founder_loan_to_company(self):
        """Test pożyczki od foundera do firmy."""
        company = Company(name="Test", cash_on_hand=10000)
        player = Founder(name="Gracz", is_player=True, personal_cash=25000)
        company.founders.append(player)
        
        loan_amount = 10000
        player.personal_cash -= loan_amount
        player.personal_invested += loan_amount
        company.cash_on_hand += loan_amount
        
        assert player.personal_cash == 15000
        assert player.personal_invested == 10000
        assert company.cash_on_hand == 20000

    def test_founder_salary_withdrawal(self):
        """Test wypłaty pensji."""
        company = Company(name="Test", cash_on_hand=50000, registered=True)
        player = Founder(name="Gracz", is_player=True, personal_cash=5000)
        company.founders.append(player)
        
        salary = 8000
        company.cash_on_hand -= salary
        player.personal_cash += salary
        player.total_received += salary
        
        assert player.personal_cash == 13000
        assert player.total_received == 8000
        assert company.cash_on_hand == 42000

    def test_founder_invest_in_company(self):
        """Test formalnej inwestycji w firmę."""
        company = Company(name="Test", cash_on_hand=10000, registered=True)
        player = Founder(name="Gracz", is_player=True, personal_cash=30000)
        company.founders.append(player)
        
        invest = 15000
        player.personal_cash -= invest
        player.personal_invested += invest
        company.cash_on_hand += invest
        company.total_raised += invest
        
        assert player.personal_cash == 15000
        assert player.personal_invested == 15000
        assert company.cash_on_hand == 25000
        assert company.total_raised == 15000

    def test_net_balance_calculation(self):
        """Test obliczania bilansu netto foundera."""
        player = Founder(name="Gracz", is_player=True)
        player.personal_invested = 20000  # Włożył 20k
        player.total_received = 15000     # Wyjął 15k
        
        net_balance = player.total_received - player.personal_invested
        assert net_balance == -5000  # Jeszcze -5k pod kreską


class TestBusinessModelE2E:
    """Testy E2E modelu biznesowego."""

    def test_saas_model_characteristics(self):
        """Test charakterystyk modelu SaaS."""
        model = BUSINESS_MODELS["saas"]
        
        assert model.model_type == "saas"
        assert model.expected_churn_rate == 0.05
        assert model.vc_attractiveness == 5

    def test_enterprise_model_longer_sales_cycle(self):
        """Test że model enterprise ma dłuższy cykl sprzedaży."""
        saas = BUSINESS_MODELS["saas"]
        enterprise = BUSINESS_MODELS["enterprise"]
        
        assert enterprise.sales_cycle_months > saas.sales_cycle_months
        assert enterprise.sales_cycle_months == 6.0

    def test_freemium_conversion_rate(self):
        """Test współczynnika konwersji freemium."""
        freemium = BUSINESS_MODELS["freemium"]
        
        assert freemium.free_to_paid_conversion == 0.03
        assert freemium.customer_acquisition_difficulty < 1.0  # Łatwiejsze

    def test_ltv_calculation(self):
        """Test obliczania LTV."""
        model = BusinessModel(
            average_revenue_per_user=200,
            expected_churn_rate=0.05
        )
        
        # LTV = ARPU / churn = 200 / 0.05 = 4000
        ltv = model.calculate_ltv()
        assert ltv == 4000.0

    def test_monthly_churn_calculation(self):
        """Test obliczania miesięcznego churnu."""
        model = BusinessModel(expected_churn_rate=0.05)
        
        churn = model.get_monthly_churn(100)
        assert churn == 5  # 5% z 100


class TestMarketAnalysisE2E:
    """Testy E2E analizy rynku."""

    def test_growing_market_characteristics(self):
        """Test charakterystyk rosnącego rynku."""
        market = MARKET_CONFIGS["growing"]
        
        assert market.market_growth_rate == 0.15
        assert market.risk_of_competitor_funding == 0.25

    def test_greenfield_market_education_cost(self):
        """Test kosztów edukacji na rynku greenfield."""
        market = MARKET_CONFIGS["greenfield"]
        
        assert market.education_cost_multiplier == 2.0
        assert market.customer_acquisition_multiplier == 2.0

    def test_mature_market_switching_barrier(self):
        """Test bariery przejścia na dojrzałym rynku."""
        market = MARKET_CONFIGS["mature"]
        
        assert market.switching_cost_barrier == 0.3
        assert market.price_flexibility < 1.0

    def test_customer_acquisition_chance_calculation(self):
        """Test obliczania szansy pozyskania klienta."""
        state = GameState()
        state.company = Company(name="Test")
        state.business_model = BUSINESS_MODELS["saas"]
        state.market_analysis = MARKET_CONFIGS["growing"]
        
        chance = calculate_customer_acquisition_chance(state)
        
        assert 0.1 <= chance <= 0.95


class TestActionPointSystemE2E:
    """Testy E2E systemu punktów akcji."""

    def test_base_action_points(self):
        """Test bazowej liczby punktów akcji."""
        system = ActionPointSystem()
        state = GameState()
        state.company = Company(name="Test", cash_on_hand=50000, monthly_burn_rate=5000)
        
        points = system.get_monthly_points(state)
        
        assert points >= 1

    def test_partner_adds_action_points(self):
        """Test że partner dodaje punkty akcji."""
        system = ActionPointSystem()
        
        # Bez partnera
        state_solo = GameState()
        state_solo.company = Company(name="Test", cash_on_hand=50000, monthly_burn_rate=5000)
        points_solo = system.get_monthly_points(state_solo)
        
        # Z partnerem
        state_partner = GameState()
        state_partner.company = Company(name="Test", cash_on_hand=50000, monthly_burn_rate=5000)
        partner = Founder(name="Partner", is_player=False)
        state_partner.company.founders.append(partner)
        points_partner = system.get_monthly_points(state_partner)
        
        assert points_partner > points_solo

    def test_low_runway_reduces_points(self):
        """Test że niski runway zmniejsza punkty."""
        system = ActionPointSystem()
        
        # Wysoki runway
        state_high = GameState()
        state_high.company = Company(name="Test", cash_on_hand=100000, monthly_burn_rate=5000)
        points_high = system.get_monthly_points(state_high)
        
        # Niski runway (<3 mies)
        state_low = GameState()
        state_low.company = Company(name="Test", cash_on_hand=10000, monthly_burn_rate=5000)
        points_low = system.get_monthly_points(state_low)
        
        assert points_low < points_high

    def test_calculate_alias_works(self):
        """Test że alias calculate() działa."""
        system = ActionPointSystem()
        state = GameState()
        state.company = Company(name="Test", cash_on_hand=50000, monthly_burn_rate=5000)
        
        points1 = system.get_monthly_points(state)
        points2 = system.calculate(state)
        
        assert points1 == points2


class TestCostCalculatorE2E:
    """Testy E2E kalkulatora kosztów."""

    def test_basic_burn_calculation(self):
        """Test podstawowego obliczania burn rate."""
        calc = CostCalculator()
        state = GameState()
        state.company = Company(name="Test")
        state.company.founder_living_cost = 5000
        
        breakdown = calc.calculate_monthly_burn(state)
        
        assert 'founder_living' in breakdown
        assert breakdown['founder_living'] == 5000

    def test_registered_company_adds_accounting(self):
        """Test że zarejestrowana firma dodaje koszty księgowości."""
        calc = CostCalculator()
        state = GameState()
        state.company = Company(name="Test", registered=True)
        state.company.founder_living_cost = 5000
        
        breakdown = calc.calculate_monthly_burn(state)
        
        assert 'accounting' in breakdown

    def test_total_burn_calculation(self):
        """Test obliczania całkowitego burn."""
        calc = CostCalculator()
        state = GameState()
        state.company = Company(name="Test", registered=True)
        state.company.founder_living_cost = 5000
        state.company.extra_monthly_costs = 2000
        
        total = calc.total_burn(state)
        
        assert total > 5000  # Powinno być więcej niż samo founder_living


class TestGameFlowE2E:
    """Testy E2E całego przepływu gry."""

    def test_complete_game_scenario_success(self):
        """Test kompletnego scenariusza sukcesu."""
        state = GameState(player_name="Tester", player_role="technical")
        company = Company(name="TestStartup", cash_on_hand=50000)
        company.monthly_burn_rate = 5000
        
        player = Founder(name="Tester", equity_percentage=60.0, is_player=True)
        company.founders.append(player)
        
        state.company = company
        state.founders_agreement = FoundersAgreement()
        state.business_model = BUSINESS_MODELS["saas"]
        state.market_analysis = MARKET_CONFIGS["growing"]
        
        # Symuluj 12 miesięcy z akwizycją klientów
        for month in range(12):
            state.advance_month()
            
            # Symuluj pozyskanie klientów
            if random.random() < 0.7:
                new_customers = random.randint(1, 3)
                company.paying_customers += new_customers
                company.mrr += new_customers * 200
            
            # Symuluj burn
            company.cash_on_hand -= company.monthly_burn_rate
            company.cash_on_hand += company.mrr
        
        # Sprawdź stan końcowy
        assert state.current_month == 12
        assert company.paying_customers > 0
        assert company.mrr > 0

    def test_game_over_bankruptcy(self):
        """Test końca gry przez bankructwo."""
        state = GameState()
        company = Company(name="Test", cash_on_hand=10000, monthly_burn_rate=5000)
        state.company = company
        
        # Symuluj 3 miesiące bez przychodów
        for _ in range(3):
            state.advance_month()
            company.cash_on_hand -= company.monthly_burn_rate
        
        # Firma powinna być na minusie
        assert company.cash_on_hand < 0

    def test_runway_calculation(self):
        """Test obliczania runway."""
        company = Company(
            name="Test",
            cash_on_hand=30000,
            monthly_burn_rate=5000,
            mrr=2000
        )
        
        runway = company.runway_months()
        
        # (30000 + 2000*n) / 5000 = n  -> iteracyjnie lub przybliżenie
        assert runway > 0

    def test_complete_game_with_partner_and_vesting(self):
        """Test kompletnej gry z partnerem i vestingiem."""
        state = GameState(player_name="Tester", player_role="technical")
        company = Company(name="TestStartup", cash_on_hand=80000)
        company.monthly_burn_rate = 8000
        
        player = Founder(name="Tester", equity_percentage=55.0, is_player=True)
        partner = Founder(name="Partner", equity_percentage=35.0, is_player=False)
        company.founders.extend([player, partner])
        company.esop_pool_percentage = 10.0
        
        state.company = company
        state.founders_agreement = FoundersAgreement(
            signed=True,
            has_good_bad_leaver=True
        )
        
        # Symuluj 15 miesięcy
        for month in range(15):
            state.advance_month()
            
            # Symuluj przychody
            if month > 3:
                company.mrr += random.randint(100, 500)
            
            company.cash_on_hand -= company.monthly_burn_rate
            company.cash_on_hand += company.mrr
        
        # Weryfikuj vesting
        assert partner.months_in_company == 15
        assert partner.cliff_completed is True
        assert partner.vested_percentage > 25.0  # Więcej niż cliff


class TestActionModesE2E:
    """Testy E2E systemu trybów akcji."""

    def test_action_mode_creation(self):
        """Test tworzenia trybu akcji."""
        mode = ActionMode(
            name="DIY",
            cost=0,
            time_cost=2,
            success_rate=0.7,
            quality_modifier=1.0
        )
        
        assert mode.name == "DIY"
        assert mode.cost == 0
        assert mode.time_cost == 2
        assert mode.success_rate == 0.7

    def test_action_mode_with_skill_requirement(self):
        """Test trybu akcji wymagającego umiejętności."""
        mode = ActionMode(
            name="Legal DIY",
            cost=500,
            time_cost=2,
            success_rate=0.5,
            requires_skill="legal"
        )
        
        assert mode.requires_skill == "legal"

    def test_premium_mode_higher_success(self):
        """Test że tryb premium ma wyższą szansę sukcesu."""
        diy_mode = ActionMode(name="DIY", cost=0, time_cost=2, success_rate=0.5)
        premium_mode = ActionMode(name="Premium", cost=10000, time_cost=1, success_rate=0.95)
        
        assert premium_mode.success_rate > diy_mode.success_rate
        assert premium_mode.cost > diy_mode.cost
        assert premium_mode.time_cost <= diy_mode.time_cost


class TestFoundersAgreementE2E:
    """Testy E2E umowy wspólników."""

    def test_fa_vs_sha_distinction(self):
        """Test rozróżnienia FA i SHA."""
        agreement = FoundersAgreement()
        
        # Przed spółką - FA
        agreement.fa_signed = True
        agreement.fa_signed_month = 1
        agreement.trial_period_months = 6
        
        assert agreement.fa_signed is True
        assert agreement.sha_signed is False
        
        # Po spółce - SHA
        agreement.sha_signed = True
        agreement.sha_signed_month = 7
        agreement.signed = True
        
        assert agreement.sha_signed is True

    def test_vesting_schedule_in_agreement(self):
        """Test harmonogramu vestingu w umowie."""
        agreement = FoundersAgreement()
        vesting = agreement.vesting_schedule
        
        assert vesting.total_months == 48
        assert vesting.cliff_months == 12
        assert vesting.cliff_percentage == 25.0

    def test_good_bad_leaver_clause(self):
        """Test klauzuli good/bad leaver."""
        agreement = FoundersAgreement()
        agreement.has_good_bad_leaver = True
        
        assert agreement.has_good_bad_leaver is True


# Uruchomienie testów
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
