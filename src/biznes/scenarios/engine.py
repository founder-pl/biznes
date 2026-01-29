"""
Biznes - Generator scenariuszy i zdarzeń losowych
Zawiera wszystkie możliwe scenariusze, zdarzenia i decyzje
"""

import random
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ..core.models import (
    GameEvent, EventType, Decision, DecisionCategory, 
    RiskLevel, Company, Founder, StartupStage, GameState
)


class ScenarioEngine:
    """Silnik scenariuszy i zdarzeń"""
    
    def __init__(self, difficulty: str = "normal"):
        self.difficulty = difficulty
        self.difficulty_multipliers = {
            "easy": {"positive_prob": 1.3, "negative_prob": 0.7},
            "normal": {"positive_prob": 1.0, "negative_prob": 1.0},
            "hard": {"positive_prob": 0.7, "negative_prob": 1.3}
        }
        
    # =========================================================================
    # ZDARZENIA LOSOWE
    # =========================================================================
    
    POSITIVE_EVENTS = [
        {
            "name": "Viral marketing",
            "description": "Twój produkt stał się viralowy na LinkedIn! Użytkownicy masowo się dzielą.",
            "probability": 0.05,
            "customers_multiplier": 2.0,
            "mrr_multiplier": 1.5,
            "credibility_change": 20,
            "min_stage": StartupStage.SEED
        },
        {
            "name": "Strategiczny partner",
            "description": "Duża firma chce zostać partnerem integracyjnym.",
            "probability": 0.08,
            "credibility_change": 30,
            "mrr_change": 3000,
            "customers_change": 20,
            "min_stage": StartupStage.SEED
        },
        {
            "name": "Nagroda branżowa",
            "description": "Wygrałeś konkurs dla startupów! Media piszą o Twoim produkcie.",
            "probability": 0.03,
            "credibility_change": 25,
            "valuation_multiplier": 1.2,
            "min_stage": StartupStage.PRE_SEED
        },
        {
            "name": "Enterprise klient",
            "description": "Duża korporacja chce wdrożyć Twój produkt na szeroką skalę.",
            "probability": 0.07,
            "mrr_change": 8000,
            "credibility_change": 30,
            "min_stage": StartupStage.SEED
        },
        {
            "name": "Inwestor sam się zgłosił",
            "description": "Znany VC skontaktował się po artykule o Twojej firmie.",
            "probability": 0.04,
            "credibility_change": 15,
            "requires_decision": True,
            "decision_type": "investment_offer",
            "min_stage": StartupStage.SEED
        },
        {
            "name": "Kluczowy talent dołączył",
            "description": "Świetny specjalista chce dołączyć do zespołu za mniejsze pieniądze + equity.",
            "probability": 0.06,
            "morale_change": 20,
            "burn_rate_change": 5000,  # dodatkowa pensja
            "min_stage": StartupStage.PRE_SEED
        },
        {
            "name": "Pozytywna recenzja w mediach",
            "description": "Popularny blog branżowy napisał pochlebną recenzję produktu.",
            "probability": 0.10,
            "customers_change": 15,
            "credibility_change": 10,
            "min_stage": StartupStage.SEED
        },
        {
            "name": "Klient poleca klientowi",
            "description": "Zadowoleni klienci zaczęli polecać produkt znajomym.",
            "probability": 0.15,
            "customers_change": 10,
            "mrr_change": 1500,
            "min_stage": StartupStage.SEED
        }
    ]
    
    NEGATIVE_EVENTS = [
        {
            "name": "Konkurent z dużym funding",
            "description": "Konkurent właśnie ogłosił rundę 10M USD i agresywną ekspansję.",
            "probability": 0.10,
            "mrr_multiplier": 0.85,
            "customers_multiplier": 0.9,
            "morale_change": -15,
            "min_stage": StartupStage.SEED
        },
        {
            "name": "Kluczowy pracownik odchodzi",
            "description": "Jeden z kluczowych członków zespołu dostał ofertę od FAANG.",
            "probability": 0.12,
            "morale_change": -25,
            "requires_decision": True,
            "decision_type": "employee_leaving",
            "min_stage": StartupStage.SEED
        },
        {
            "name": "Zmiana regulacji RODO/KSeF",
            "description": "Nowe regulacje wymagają istotnych zmian w produkcie.",
            "probability": 0.05,
            "cash_change": -20000,
            "requires_decision": True,
            "decision_type": "compliance",
            "min_stage": StartupStage.PRE_SEED
        },
        {
            "name": "Wyciek danych",
            "description": "Odkryto lukę bezpieczeństwa. Musisz poinformować użytkowników.",
            "probability": 0.03,
            "credibility_change": -40,
            "cash_change": -30000,
            "customers_multiplier": 0.8,
            "min_stage": StartupStage.SEED
        },
        {
            "name": "Problemy z płynnością",
            "description": "Kluczowy klient opóźnia płatność o 3 miesiące.",
            "probability": 0.15,
            "cash_change": -15000,
            "morale_change": -10,
            "min_stage": StartupStage.SEED
        },
        {
            "name": "Konflikt między founderami",
            "description": "Różnice wizji prowadzą do napięć w zespole założycielskim.",
            "probability": 0.12,
            "morale_change": -30,
            "requires_decision": True,
            "decision_type": "founder_conflict",
            "min_stage": StartupStage.PRE_SEED
        },
        {
            "name": "MVP nie spełnia oczekiwań",
            "description": "Feedback od użytkowników wskazuje, że produkt nie rozwiązuje ich problemu.",
            "probability": 0.20,
            "customers_multiplier": 0.7,
            "morale_change": -20,
            "requires_decision": True,
            "decision_type": "pivot_decision",
            "min_stage": StartupStage.PRE_SEED
        },
        {
            "name": "Partner odchodzi z kontaktami",
            "description": "Partner biznesowy chce odejść i zabrać ze sobą kontakty.",
            "probability": 0.08,
            "customers_multiplier": 0.85,
            "requires_decision": True,
            "decision_type": "partner_leaving",
            "min_stage": StartupStage.PRE_SEED
        },
        {
            "name": "Awaria serwera w krytycznym momencie",
            "description": "System padł podczas ważnej prezentacji dla inwestora.",
            "probability": 0.08,
            "credibility_change": -15,
            "morale_change": -10,
            "min_stage": StartupStage.PRE_SEED
        },
        {
            "name": "Duży klient rezygnuje",
            "description": "Twój największy klient przechodzi do konkurencji.",
            "probability": 0.10,
            "mrr_change": -5000,
            "morale_change": -15,
            "min_stage": StartupStage.SEED
        },
        {
            "name": "Opóźnienie w developmencie",
            "description": "Kluczowa funkcjonalność zajmie 2x więcej czasu niż planowano.",
            "probability": 0.25,
            "burn_rate_change": 5000,
            "morale_change": -10,
            "min_stage": StartupStage.PRE_SEED
        },
        {
            "name": "Problem prawny z IP",
            "description": "Ktoś twierdzi, że naruszasz ich patent.",
            "probability": 0.04,
            "cash_change": -25000,
            "requires_decision": True,
            "decision_type": "ip_dispute",
            "min_stage": StartupStage.SEED
        }
    ]
    
    # =========================================================================
    # DECYZJE I SCENARIUSZE
    # =========================================================================
    
    DECISIONS = {
        "investment_offer": {
            "title": "Oferta inwestycyjna",
            "description": "Fundusz VC oferuje {amount} PLN za {equity}% firmy. Co robisz?",
            "category": DecisionCategory.FINANCIAL,
            "risk_level": RiskLevel.HIGH,
            "options": [
                {
                    "text": "Akceptuj ofertę",
                    "consequences": {
                        "cash_change": "amount",
                        "equity_dilution": "equity",
                        "valuation_set": True,
                        "board_seat_given": True
                    },
                    "risks": ["Utrata kontroli", "Presja na szybki wzrost", "Rozwodnienie"],
                    "opportunities": ["Kapitał na rozwój", "Networking", "Mentoring"]
                },
                {
                    "text": "Negocjuj lepsze warunki",
                    "success_probability": 0.6,
                    "consequences_success": {
                        "better_terms": True,
                        "equity_reduction": 0.8
                    },
                    "consequences_fail": {
                        "offer_withdrawn": 0.3,
                        "relationship_damaged": True
                    },
                    "risks": ["Fundusz może się wycofać"],
                    "opportunities": ["Lepsze warunki", "Pokazanie siły negocjacyjnej"]
                },
                {
                    "text": "Odrzuć i szukaj dalej",
                    "consequences": {
                        "no_investment": True,
                        "time_lost_months": 2
                    },
                    "risks": ["Brak kapitału", "Utrata momentum"],
                    "opportunities": ["Zachowanie kontroli", "Lepszy deal później"]
                }
            ]
        },
        
        "employee_leaving": {
            "title": "Kluczowy pracownik odchodzi",
            "description": "{employee_name} dostał ofertę 2x większej pensji. Chce odejść.",
            "category": DecisionCategory.TEAM,
            "risk_level": RiskLevel.MEDIUM,
            "options": [
                {
                    "text": "Dopasuj ofertę płacową",
                    "consequences": {
                        "burn_rate_change": 8000,
                        "employee_stays": True,
                        "morale_change": 10
                    },
                    "risks": ["Wyższe koszty", "Inni mogą też negocjować"],
                    "opportunities": ["Zachowanie wiedzy", "Stabilność zespołu"]
                },
                {
                    "text": "Zaproponuj więcej equity zamiast kasy",
                    "success_probability": 0.5,
                    "consequences_success": {
                        "esop_used": 2.0,
                        "employee_stays": True
                    },
                    "consequences_fail": {
                        "employee_leaves": True,
                        "morale_change": -15
                    },
                    "risks": ["Rozwodnienie equity", "Może nie zadziałać"],
                    "opportunities": ["Niższe koszty miesięczne", "Większe zaangażowanie"]
                },
                {
                    "text": "Pozwól odejść, szukaj zastępstwa",
                    "consequences": {
                        "employee_leaves": True,
                        "hiring_time_months": 2,
                        "productivity_loss": 0.3,
                        "morale_change": -10
                    },
                    "risks": ["Utrata wiedzy", "Opóźnienia"],
                    "opportunities": ["Świeża krew", "Potencjalnie lepszy kandydat"]
                }
            ]
        },
        
        "founder_conflict": {
            "title": "Konflikt między founderami",
            "description": "Ty i {partner_name} macie różne wizje rozwoju firmy.",
            "category": DecisionCategory.PARTNERSHIP,
            "risk_level": RiskLevel.CRITICAL,
            "options": [
                {
                    "text": "Mediacja z zewnętrznym mentorem",
                    "success_probability": 0.7,
                    "consequences_success": {
                        "conflict_resolved": True,
                        "morale_change": 15,
                        "cash_change": -5000
                    },
                    "consequences_fail": {
                        "conflict_escalates": True,
                        "morale_change": -20
                    },
                    "risks": ["Koszt", "Może nie zadziałać"],
                    "opportunities": ["Profesjonalne rozwiązanie", "Lepsza komunikacja"]
                },
                {
                    "text": "Wykup udziały partnera (jeśli good leaver)",
                    "consequences": {
                        "partner_buyout": True,
                        "cash_change": "negative_partner_value",
                        "full_control": True,
                        "morale_change": -10
                    },
                    "risks": ["Wysokie koszty", "Utrata kompetencji"],
                    "opportunities": ["Pełna kontrola", "Jasna wizja"]
                },
                {
                    "text": "Pozwól partnerowi odejść (trigger klauzuli)",
                    "consequences": {
                        "check_leaver_clause": True,
                        "partner_leaves": True
                    },
                    "risks": ["Zależy od umowy", "Potencjalny konflikt prawny"],
                    "opportunities": ["Czysta sytuacja", "Możliwość restartu"]
                },
                {
                    "text": "Kontynuuj mimo konfliktu",
                    "consequences": {
                        "ongoing_conflict": True,
                        "productivity_loss": 0.2,
                        "morale_change": -5
                    },
                    "risks": ["Eskalacja", "Paraliż decyzyjny"],
                    "opportunities": ["Czas na przemyślenie"]
                }
            ]
        },
        
        "pivot_decision": {
            "title": "Pivot produktu",
            "description": "Użytkownicy mówią, że produkt nie rozwiązuje ich problemu. Co robisz?",
            "category": DecisionCategory.PRODUCT,
            "risk_level": RiskLevel.HIGH,
            "options": [
                {
                    "text": "Pełny pivot - zmień value proposition",
                    "consequences": {
                        "development_months": 4,
                        "cash_change": -40000,
                        "customers_reset": True,
                        "potential_pmf": 0.6
                    },
                    "risks": ["Utrata dotychczasowych klientów", "Wysokie koszty"],
                    "opportunities": ["Lepszy product-market fit", "Nowy rynek"]
                },
                {
                    "text": "Iteracyjne poprawki na bazie feedbacku",
                    "consequences": {
                        "development_months": 2,
                        "cash_change": -15000,
                        "customer_retention": 0.7,
                        "potential_pmf": 0.4
                    },
                    "risks": ["Może nie wystarczyć", "Opóźnia decyzję"],
                    "opportunities": ["Niższe koszty", "Zachowanie części klientów"]
                },
                {
                    "text": "Zmień target market, nie produkt",
                    "consequences": {
                        "sales_refocus": True,
                        "cash_change": -10000,
                        "potential_pmf": 0.5
                    },
                    "risks": ["Nowy rynek może nie zadziałać"],
                    "opportunities": ["Szybsze niż pełny pivot"]
                },
                {
                    "text": "Kontynuuj bez zmian i szukaj więcej klientów",
                    "consequences": {
                        "stubbornness": True,
                        "potential_failure": 0.6,
                        "cash_burn_continues": True
                    },
                    "risks": ["Ignorowanie rynku", "Spalenie runway"],
                    "opportunities": ["Może się uda", "Nie tracisz obecnych klientów"]
                }
            ]
        },
        
        "partner_leaving": {
            "title": "Partner chce odejść",
            "description": "{partner_name} chce odejść i zabrać kontakty/klientów.",
            "category": DecisionCategory.PARTNERSHIP,
            "risk_level": RiskLevel.CRITICAL,
            "options": [
                {
                    "text": "Powołaj się na non-solicitation w umowie",
                    "precondition": "has_non_solicitation",
                    "consequences": {
                        "clients_protected": True,
                        "legal_warning": True
                    },
                    "risks": ["Zła atmosfera", "Potencjalny spór"],
                    "opportunities": ["Ochrona klientów", "Działanie umowy"]
                },
                {
                    "text": "Negocjuj polubowny rozstanie",
                    "consequences": {
                        "buyout_discussion": True,
                        "partial_client_loss": 0.3
                    },
                    "risks": ["Utrata części klientów", "Koszty buyout"],
                    "opportunities": ["Czyste rozstanie", "Brak sporu"]
                },
                {
                    "text": "Pozwól odejść bez warunków",
                    "consequences": {
                        "partner_free": True,
                        "clients_at_risk": 0.5,
                        "morale_change": -20
                    },
                    "risks": ["Utrata klientów", "Utrata wiedzy"],
                    "opportunities": ["Szybkie rozstanie"]
                }
            ]
        },
        
        "ip_dispute": {
            "title": "Spór o własność intelektualną",
            "description": "Firma X twierdzi, że naruszasz ich patent.",
            "category": DecisionCategory.LEGAL,
            "risk_level": RiskLevel.CRITICAL,
            "options": [
                {
                    "text": "Zatrudnij prawnika patentowego i walcz",
                    "consequences": {
                        "cash_change": -50000,
                        "time_months": 6,
                        "win_probability": 0.5
                    },
                    "risks": ["Wysokie koszty", "Długi proces"],
                    "opportunities": ["Może wygrasz", "Precedens"]
                },
                {
                    "text": "Negocjuj ugodę/licencję",
                    "consequences": {
                        "cash_change": -30000,
                        "ongoing_royalty": True,
                        "time_months": 1
                    },
                    "risks": ["Stały koszt licencji"],
                    "opportunities": ["Szybkie rozwiązanie", "Pewność prawna"]
                },
                {
                    "text": "Przeprojektuj funkcjonalność",
                    "consequences": {
                        "development_months": 3,
                        "cash_change": -25000,
                        "feature_change": True
                    },
                    "risks": ["Opóźnienia", "Zmiana produktu"],
                    "opportunities": ["Uniknięcie sporu", "Może lepsze rozwiązanie"]
                }
            ]
        },
        
        "compliance": {
            "title": "Nowe wymogi compliance",
            "description": "Nowe regulacje wymagają zmian w produkcie i procesach.",
            "category": DecisionCategory.LEGAL,
            "risk_level": RiskLevel.HIGH,
            "options": [
                {
                    "text": "Natychmiastowa pełna zgodność",
                    "consequences": {
                        "cash_change": -35000,
                        "development_months": 2,
                        "full_compliance": True,
                        "credibility_change": 10
                    },
                    "risks": ["Wysokie koszty natychmiast"],
                    "opportunities": ["Pełna zgodność", "Marketing advantage"]
                },
                {
                    "text": "Minimalna zgodność teraz, reszta później",
                    "consequences": {
                        "cash_change": -15000,
                        "development_months": 1,
                        "partial_compliance": True,
                        "future_risk": 0.3
                    },
                    "risks": ["Może nie wystarczyć", "Ryzyko kar"],
                    "opportunities": ["Niższe koszty teraz"]
                },
                {
                    "text": "Poczekaj na wyjaśnienia interpretacji",
                    "consequences": {
                        "cash_change": 0,
                        "risk_of_penalty": 0.2,
                        "wait_months": 3
                    },
                    "risks": ["Kary", "Utrata klientów dbających o compliance"],
                    "opportunities": ["Oszczędności", "Lepsze zrozumienie wymogów"]
                }
            ]
        }
    }
    
    # =========================================================================
    # METODY GENEROWANIA
    # =========================================================================
    
    def generate_random_event(self, game_state: GameState) -> Optional[GameEvent]:
        """Generuje losowe zdarzenie odpowiednie dla etapu gry"""
        
        multipliers = self.difficulty_multipliers[self.difficulty]
        stage = game_state.company.stage
        
        # Wybierz pulę zdarzeń
        all_events = []
        
        for event_data in self.POSITIVE_EVENTS:
            if self._stage_allows_event(stage, event_data.get('min_stage')):
                adjusted_prob = event_data['probability'] * multipliers['positive_prob']
                all_events.append(('positive', event_data, adjusted_prob))
                
        for event_data in self.NEGATIVE_EVENTS:
            if self._stage_allows_event(stage, event_data.get('min_stage')):
                adjusted_prob = event_data['probability'] * multipliers['negative_prob']
                all_events.append(('negative', event_data, adjusted_prob))
        
        # Losuj czy zdarzenie wystąpi
        for event_type, event_data, probability in all_events:
            if random.random() < probability:
                return self._create_event(event_type, event_data, game_state.current_month)
        
        return None
    
    def _stage_allows_event(self, current: StartupStage, minimum: Optional[StartupStage]) -> bool:
        """Sprawdza czy etap pozwala na zdarzenie"""
        if minimum is None:
            return True
        
        stage_order = [
            StartupStage.IDEA,
            StartupStage.PRE_SEED,
            StartupStage.SEED,
            StartupStage.SERIES_A,
            StartupStage.GROWTH,
            StartupStage.EXIT
        ]
        
        try:
            current_idx = stage_order.index(current)
            min_idx = stage_order.index(minimum)
            return current_idx >= min_idx
        except ValueError:
            return True
    
    def _create_event(self, event_type: str, data: Dict, month: int) -> GameEvent:
        """Tworzy obiekt GameEvent z danych"""
        return GameEvent(
            name=data['name'],
            description=data['description'],
            event_type=EventType.POSITIVE if event_type == 'positive' else EventType.NEGATIVE,
            month=month,
            mrr_change=data.get('mrr_change', 0),
            mrr_multiplier=data.get('mrr_multiplier', 1.0),
            customers_change=data.get('customers_change', 0),
            customers_multiplier=data.get('customers_multiplier', 1.0),
            cash_change=data.get('cash_change', 0),
            burn_rate_change=data.get('burn_rate_change', 0),
            valuation_multiplier=data.get('valuation_multiplier', 1.0),
            morale_change=data.get('morale_change', 0),
            credibility_change=data.get('credibility_change', 0),
            requires_decision=data.get('requires_decision', False),
            triggers_pivot=data.get('triggers_pivot', False),
            triggers_conflict=data.get('triggers_conflict', False)
        )
    
    def get_decision(self, decision_type: str, context: Dict = None) -> Optional[Decision]:
        """Pobiera decyzję z kontekstem"""
        if decision_type not in self.DECISIONS:
            return None
            
        data = self.DECISIONS[decision_type]
        context = context or {}
        
        # Interpoluj zmienne w opisie
        description = data['description']
        for key, value in context.items():
            description = description.replace(f"{{{key}}}", str(value))
        
        return Decision(
            category=data['category'],
            title=data['title'],
            description=description,
            risk_level=data['risk_level'],
            options=data['options']
        )
    
    # =========================================================================
    # OBLICZENIA RYZYKA
    # =========================================================================
    
    def calculate_risk_score(self, game_state: GameState) -> Dict[str, Any]:
        """Oblicza kompleksowy wskaźnik ryzyka"""
        
        risks = []
        score = 0
        
        # Ryzyko finansowe
        runway = game_state.company.runway_months()
        if runway < 3:
            risks.append(("KRYTYCZNE", "Runway poniżej 3 miesięcy!"))
            score += 40
        elif runway < 6:
            risks.append(("WYSOKIE", f"Runway tylko {runway} miesięcy"))
            score += 25
        elif runway < 12:
            risks.append(("ŚREDNIE", f"Runway {runway} miesięcy"))
            score += 10
            
        # Ryzyko prawne
        if not game_state.founders_agreement.signed:
            risks.append(("KRYTYCZNE", "Brak podpisanej umowy wspólników!"))
            score += 35
        else:
            missing = game_state.founders_agreement.get_missing_protections()
            if missing:
                risks.append(("WYSOKIE", f"Brakujące zabezpieczenia: {', '.join(missing[:2])}..."))
                score += 5 * len(missing)
                
        # Ryzyko produktowe
        if not game_state.company.product_market_fit:
            if game_state.current_month > 12:
                risks.append(("WYSOKIE", "Brak product-market fit po 12 miesiącach"))
                score += 20
            elif game_state.current_month > 6:
                risks.append(("ŚREDNIE", "Wciąż szukasz product-market fit"))
                score += 10
                
        # Ryzyko partnerskie
        founders = game_state.company.founders
        unverified = [f for f in founders if not f.krs_verified]
        if unverified:
            risks.append(("ŚREDNIE", f"{len(unverified)} niezweryfikowanych wspólników"))
            score += 10 * len(unverified)
            
        # Ryzyko koncentracji klientów
        if game_state.company.paying_customers < 5 and game_state.company.mrr > 0:
            risks.append(("ŚREDNIE", "Wysoka zależność od nielicznych klientów"))
            score += 15
            
        return {
            'total_score': min(100, score),
            'level': self._score_to_level(score),
            'risks': risks,
            'recommendation': self._get_risk_recommendation(score, risks)
        }
    
    def _score_to_level(self, score: int) -> str:
        if score >= 70:
            return "KRYTYCZNY"
        elif score >= 50:
            return "WYSOKI"
        elif score >= 30:
            return "ŚREDNI"
        else:
            return "NISKI"
    
    def _get_risk_recommendation(self, score: int, risks: List) -> str:
        if score >= 70:
            return "PILNE DZIAŁANIE WYMAGANE! Skup się na najważniejszych ryzykach."
        elif score >= 50:
            return "Musisz podjąć działania naprawcze w ciągu najbliższych tygodni."
        elif score >= 30:
            return "Masz czas, ale zaplanuj działania mitygujące."
        else:
            return "Dobra sytuacja. Monitoruj ryzyka."
    
    # =========================================================================
    # REKOMENDACJE
    # =========================================================================
    
    def get_equity_recommendation(
        self,
        player_brings_mvp: bool,
        mvp_value: float,
        partner_brings_capital: float,
        partner_has_industry_exp: bool,
        partner_has_customers: bool
    ) -> Dict[str, Any]:
        """Oblicza rekomendowany podział equity"""
        
        player_score = 0
        partner_score = 0
        
        # MVP
        if player_brings_mvp:
            player_score += 40
            player_score += min(20, mvp_value / 10000)  # bonus za wartość MVP
            
        # Kapitał partnera
        if partner_brings_capital > 0:
            partner_score += min(30, partner_brings_capital / 5000)
            
        # Doświadczenie branżowe
        if partner_has_industry_exp:
            partner_score += 15
            
        # Istniejący klienci
        if partner_has_customers:
            partner_score += 20
            
        # Bazowy wkład pracy (zakładamy równy commitment)
        player_score += 30
        partner_score += 30
        
        total = player_score + partner_score
        player_pct = round((player_score / total) * 100)
        partner_pct = 100 - player_pct
        
        # ESOP
        esop = 10
        player_final = round(player_pct * (100 - esop) / 100)
        partner_final = round(partner_pct * (100 - esop) / 100)
        
        return {
            'player_percentage': player_final,
            'partner_percentage': partner_final,
            'esop_pool': esop,
            'reasoning': self._build_equity_reasoning(
                player_brings_mvp, mvp_value, partner_brings_capital,
                partner_has_industry_exp, partner_has_customers
            ),
            'warning': self._equity_warning(player_final, partner_final)
        }
    
    def _build_equity_reasoning(self, mvp, mvp_val, capital, exp, customers) -> List[str]:
        reasons = []
        if mvp:
            reasons.append(f"MVP o wartości {mvp_val:,.0f} PLN redukuje ryzyko techniczne")
        if capital > 0:
            reasons.append(f"Kapitał {capital:,.0f} PLN zapewnia runway")
        if exp:
            reasons.append("Doświadczenie branżowe przyspiesza walidację")
        if customers:
            reasons.append("Istniejący klienci = natychmiastowe przychody")
        return reasons
    
    def _equity_warning(self, player: int, partner: int) -> Optional[str]:
        if player < 30:
            return "UWAGA: Twój udział < 30% może oznaczać utratę kontroli!"
        if abs(player - partner) < 5:
            return "Podział 50/50 może prowadzić do impasów decyzyjnych."
        return None
    
    def get_legal_form_recommendation(
        self,
        has_capital: bool,
        plans_vc: bool,
        needs_work_contribution: bool,
        needs_easy_esop: bool
    ) -> Dict[str, Any]:
        """Rekomenduje formę prawną"""
        
        psa_score = 0
        zoo_score = 0
        
        if not has_capital:
            psa_score += 30
        else:
            zoo_score += 10
            
        if plans_vc:
            psa_score += 25
        else:
            zoo_score += 15
            
        if needs_work_contribution:
            psa_score += 35
            
        if needs_easy_esop:
            psa_score += 20
        
        recommended = "PSA" if psa_score > zoo_score else "Sp. z o.o."
        
        return {
            'recommended': recommended,
            'psa_score': psa_score,
            'zoo_score': zoo_score,
            'psa_reasons': self._get_psa_reasons(has_capital, plans_vc, needs_work_contribution),
            'zoo_reasons': self._get_zoo_reasons(has_capital, plans_vc),
            'cost_comparison': {
                'psa_startup': 1,
                'psa_yearly': 2250,
                'zoo_startup': 5000,
                'zoo_yearly': 0
            }
        }
    
    def _get_psa_reasons(self, no_capital, vc, work) -> List[str]:
        reasons = []
        if no_capital:
            reasons.append("Brak wymaganego kapitału - praca może być wkładem")
        if vc:
            reasons.append("Łatwiejsze pozyskanie VC dzięki elastycznemu equity")
        if work:
            reasons.append("Możesz wnieść pracę jako wkład bez kapitału")
        return reasons
    
    def _get_zoo_reasons(self, capital, vc) -> List[str]:
        reasons = []
        if capital:
            reasons.append("Masz kapitał - sp. z o.o. ma niższe koszty roczne")
        if not vc:
            reasons.append("Bez planów VC - prostsza i bardziej znana forma")
        reasons.append("Ugruntowane orzecznictwo - większa przewidywalność")
        return reasons


# Singleton dla łatwego dostępu
_scenario_engine: Optional[ScenarioEngine] = None

def get_scenario_engine(difficulty: str = "normal") -> ScenarioEngine:
    global _scenario_engine
    if _scenario_engine is None or _scenario_engine.difficulty != difficulty:
        _scenario_engine = ScenarioEngine(difficulty)
    return _scenario_engine
