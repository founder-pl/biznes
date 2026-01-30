from __future__ import annotations

from typing import Optional, Tuple

from ..core.models import GameState, PlayerConfig


def pluralize_months(n: int) -> str:
    if n == 1:
        return "1 miesiąc"
    if 2 <= n <= 4:
        return f"{n} miesiące"
    return f"{n} miesięcy"


def has_partner(game_state: GameState, config: Optional[PlayerConfig] = None) -> bool:
    company = getattr(game_state, "company", None)
    founders = getattr(company, "founders", None) if company else None
    if founders:
        return any((not f.is_player) and (not getattr(f, "left_company", False)) for f in founders)
    return bool(getattr(config, "has_partner", False))


def get_risk_indicators(game_state: GameState, config: Optional[PlayerConfig] = None) -> str:
    c = game_state.company
    risks = []

    runway = c.runway_months()
    if runway < 3:
        risks.append("🔴 RUNWAY: KRYTYCZNY!")
    elif runway < 6:
        risks.append("🟡 RUNWAY: NISKI")

    if has_partner(game_state, config) and not game_state.agreement_signed:
        risks.append("🔴 SHA: BRAK UMOWY!")

    if not c.registered and game_state.current_month > 3:
        risks.append("🟡 SPÓŁKA: NIEZAREJESTROWANA")

    if game_state.current_month > 6 and c.paying_customers < 5:
        risks.append("🟠 PMF: BRAK TRAKCJI")

    if not c.mvp_completed and game_state.current_month > 4:
        risks.append("🟡 MVP: NIEUKOŃCZONE")

    return " | ".join(risks) if risks else "✅ Brak krytycznych ryzyk"


def get_priority_action(
    game_state: GameState,
    config: Optional[PlayerConfig] = None,
) -> Tuple[str, str, str]:
    c = game_state.company
    month = game_state.current_month

    runway = c.runway_months()
    if runway < 3:
        return (
            "🚨 SZUKAJ FINANSOWANIA LUB KLIENTÓW",
            f"Masz mniej niż 3 miesiące runway ({runway} mies)",
            f"Bez działania: BANKRUCTWO w ~{runway} mies",
        )

    if has_partner(game_state, config) and not game_state.agreement_signed:
        return (
            "📝 PODPISZ SHA",
            "Bez umowy partner może odejść z kodem/klientami",
            "Bez SHA rośnie ryzyko konfliktu i blokady spółki",
        )

    if not c.registered and month > 2:
        return (
            "🏢 ZAREJESTRUJ SPÓŁKĘ",
            "Bez spółki nie możesz legalnie pozyskać inwestora",
            "Bez rejestracji odpowiadasz osobiście",
        )

    if not c.mvp_completed:
        return (
            "🔧 DOKOŃCZ MVP",
            "Bez produktu nie zdobędziesz klientów",
            "Bez MVP spalasz gotówkę bez walidacji",
        )

    if c.mvp_completed and c.paying_customers < 10:
        return (
            "🎯 ZDOBĄDŹ KLIENTÓW",
            "Klienci = walidacja + MRR",
            "Bez klientów brak dowodu PMF",
        )

    if runway < 6:
        return (
            "💰 WYDŁUŻ RUNWAY",
            f"Masz tylko {pluralize_months(runway)} runway",
            "Zalecane minimum to 6 miesięcy",
        )

    return ("📈 ROZWIJAJ BIZNES", "Masz podstawy, teraz skaluj", "")
