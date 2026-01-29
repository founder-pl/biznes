"""
Konfiguracja pytest dla projektu Biznes.
"""
import pytest
import sys
import os

# Dodaj src do ścieżki
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture
def sample_founder():
    """Przykładowy founder do testów."""
    from biznes.core.models import Founder
    return Founder(
        name="Test Founder",
        equity_percentage=55.0,
        is_player=True,
        role="technical"
    )


@pytest.fixture
def sample_company():
    """Przykładowa firma do testów."""
    from biznes.core.models import Company
    company = Company(name="Test Startup")
    company.cash_on_hand = 100000
    company.monthly_burn_rate = 15000
    company.mrr = 5000
    return company


@pytest.fixture
def sample_agreement():
    """Przykładowa umowa wspólników do testów."""
    from biznes.core.models import FoundersAgreement
    agreement = FoundersAgreement()
    agreement.has_vesting = True
    agreement.has_tag_along = True
    agreement.has_good_bad_leaver = True
    agreement.has_ip_assignment = True
    agreement.has_non_compete = True
    agreement.has_nda = True
    return agreement


@pytest.fixture
def scenario_engine():
    """Silnik scenariuszy do testów."""
    from biznes.scenarios.engine import ScenarioEngine
    return ScenarioEngine(difficulty="normal")


@pytest.fixture
def game_state(sample_company, sample_agreement, sample_founder):
    """Kompletny stan gry do testów."""
    from biznes.core.models import GameState
    state = GameState(player_name="Tester", player_role="technical")
    state.company = sample_company
    state.founders_agreement = sample_agreement
    state.company.founders.append(sample_founder)
    return state
