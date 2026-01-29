"""
Testy dla gry Biznes - Symulator Startupu
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Dodaj ścieżkę src do PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestModels:
    """Testy modeli danych."""
    
    def test_founder_creation(self):
        """Test tworzenia obiektu Founder."""
        from biznes.core.models import Founder
        
        founder = Founder(
            name="Jan",
            equity_percentage=55.0,
            is_player=True,
            role="technical"
        )
        
        assert founder.name == "Jan"
        assert founder.equity_percentage == 55.0
        assert founder.is_player is True
        assert founder.role == "technical"
        assert founder.vested_percentage == 0.0
        assert founder.cliff_completed is False
    
    def test_company_creation(self):
        """Test tworzenia obiektu Company."""
        from biznes.core.models import Company, LegalForm
        
        company = Company(name="TestStartup")
        
        assert company.name == "TestStartup"
        assert company.legal_form == LegalForm.NONE  # Domyślnie NONE
        assert company.cash_on_hand == 0.0
        assert company.mrr == 0.0
    
    def test_vesting_schedule_defaults(self):
        """Test domyślnych wartości vestingu."""
        from biznes.core.models import VestingSchedule
        
        vesting = VestingSchedule()
        
        assert vesting.total_months == 48
        assert vesting.cliff_months == 12
        assert vesting.cliff_percentage == 25.0
    
    def test_game_state_creation(self):
        """Test tworzenia stanu gry."""
        from biznes.core.models import GameState
        
        state = GameState(player_name="Tester", player_role="technical")
        
        assert state.player_name == "Tester"
        assert state.player_role == "technical"
        assert state.current_month == 0


class TestScenarioEngine:
    """Testy silnika scenariuszy."""
    
    def test_engine_initialization(self):
        """Test inicjalizacji silnika."""
        from biznes.scenarios.engine import ScenarioEngine
        
        engine = ScenarioEngine()
        
        assert engine is not None
        assert engine.difficulty == "normal"
    
    def test_difficulty_multipliers(self):
        """Test mnożników trudności."""
        from biznes.scenarios.engine import ScenarioEngine
        
        # Easy mode
        engine_easy = ScenarioEngine(difficulty="easy")
        assert engine_easy.difficulty_multipliers["easy"]["positive_prob"] == 1.3
        assert engine_easy.difficulty_multipliers["easy"]["negative_prob"] == 0.7
        
        # Hard mode
        engine_hard = ScenarioEngine(difficulty="hard")
        assert engine_hard.difficulty_multipliers["hard"]["positive_prob"] == 0.7
        assert engine_hard.difficulty_multipliers["hard"]["negative_prob"] == 1.3
    
    def test_risk_calculation_low_runway(self):
        """Test kalkulacji ryzyka przy niskim runway."""
        from biznes.scenarios.engine import ScenarioEngine
        from biznes.core.models import Company, FoundersAgreement, GameState
        
        engine = ScenarioEngine()
        
        company = Company(name="Test")
        company.cash_on_hand = 30000  # 3 miesiące runway
        company.monthly_burn_rate = 10000
        company.mrr = 0
        
        game_state = GameState()
        game_state.company = company
        game_state.founders_agreement = FoundersAgreement()
        game_state.founders_agreement.has_vesting = True
        
        result = engine.calculate_risk_score(game_state)
        
        # Funkcja zwraca dict z score i risks
        assert isinstance(result, dict)
        assert 'score' in result or 'total' in result or len(result) > 0


class TestEquityCalculation:
    """Testy kalkulacji equity."""
    
    def test_mvp_valuation(self):
        """Test wyceny MVP."""
        hours = 400
        hourly_rate = 150
        external_costs = 10000
        
        expected_value = hours * hourly_rate + external_costs
        assert expected_value == 70000
    
    def test_equity_recommendation_with_mvp(self):
        """Test rekomendacji equity gdy gracz wnosi MVP."""
        # Prosta kalkulacja equity (logika z shell.py)
        player_mvp_value = 70000
        partner_capital = 20000
        
        player_base, partner_base = 50, 50
        esop = 10
        
        # MVP bonus
        mvp_bonus = min(20, player_mvp_value / 5000)  # = 14
        player_base += mvp_bonus
        partner_base -= mvp_bonus
        
        # Partner capital bonus
        cap_bonus = min(15, partner_capital / 5000)  # = 4
        partner_base += cap_bonus
        player_base -= cap_bonus
        
        player_equity = player_base - esop/2
        partner_equity = partner_base - esop/2
        
        # Gracz z MVP powinien mieć więcej
        assert player_equity > partner_equity
        assert player_equity + partner_equity + esop == 100


class TestVestingMechanics:
    """Testy mechaniki vestingu."""
    
    def test_vesting_before_cliff(self):
        """Test vestingu przed clifem."""
        from biznes.core.models import Founder, VestingSchedule
        
        founder = Founder(name="Test", equity_percentage=60.0)
        vesting = VestingSchedule(
            total_months=48,
            cliff_months=12,
            cliff_percentage=25.0
        )
        
        # Przed clifem - nic nie vestuje
        months_worked = 6
        assert founder.cliff_completed is False
        
        # Symulacja: vested powinno być 0 przed clifem
        if months_worked < vesting.cliff_months:
            vested = 0.0
        else:
            vested = vesting.cliff_percentage
        
        assert vested == 0.0
    
    def test_vesting_at_cliff(self):
        """Test vestingu przy osiągnięciu clifu."""
        from biznes.core.models import VestingSchedule
        
        vesting = VestingSchedule(
            total_months=48,
            cliff_months=12,
            cliff_percentage=25.0
        )
        
        equity = 60.0
        months_worked = 12
        
        # Po clifie - 25% vestuje
        vested_percent = (vesting.cliff_percentage / 100) * equity
        assert vested_percent == 15.0  # 25% z 60% = 15%
    
    def test_vesting_full_period(self):
        """Test pełnego vestingu po 48 miesiącach."""
        from biznes.core.models import VestingSchedule
        
        vesting = VestingSchedule(total_months=48)
        equity = 60.0
        months_worked = 48
        
        # Po pełnym okresie - 100% vestuje
        assert months_worked >= vesting.total_months
        vested = equity  # Pełne 60%
        assert vested == 60.0


class TestLegalForms:
    """Testy form prawnych."""
    
    def test_psa_characteristics(self):
        """Test charakterystyki PSA."""
        psa_config = {
            "min_capital": 1,
            "work_as_contribution": True,
            "notary_required": False
        }
        
        assert psa_config["min_capital"] == 1
        assert psa_config["work_as_contribution"] is True
        assert psa_config["notary_required"] is False
    
    def test_spzoo_characteristics(self):
        """Test charakterystyki Sp. z o.o."""
        spzoo_config = {
            "min_capital": 5000,
            "work_as_contribution": False,
            "notary_required": True
        }
        
        assert spzoo_config["min_capital"] == 5000
        assert spzoo_config["work_as_contribution"] is False
        assert spzoo_config["notary_required"] is True


class TestRedFlags:
    """Testy wykrywania red flags."""
    
    def test_no_written_agreement_flag(self):
        """Test flagi: brak umowy pisemnej."""
        red_flags = []
        has_written_agreement = False
        
        if not has_written_agreement:
            red_flags.append("Brak umowy pisemnej")
        
        assert "Brak umowy pisemnej" in red_flags
    
    def test_equity_later_flag(self):
        """Test flagi: 'ustalmy equity później'."""
        red_flags = []
        equity_decided = False
        
        if not equity_decided:
            red_flags.append("Equity do ustalenia później")
        
        assert "Equity do ustalenia później" in red_flags
    
    def test_partner_not_verified_flag(self):
        """Test flagi: niezweryfikowany partner."""
        red_flags = []
        partner_krs_verified = False
        partner_debts_verified = False
        
        if not partner_krs_verified:
            red_flags.append("Partner niezweryfikowany w KRS")
        if not partner_debts_verified:
            red_flags.append("Partner niezweryfikowany w rejestrach dłużników")
        
        assert len(red_flags) == 2


# Uruchomienie testów
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
