"""
Biznes - Interaktywny interfejs TUI (Textual)
Wersja z nawigacją strzałkami i minimalnym pisaniem
"""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header, Footer, Static, Button, Label, 
    ListItem, ListView, ProgressBar, Rule, Tree
)
from textual.widgets.tree import TreeNode
from textual.screen import Screen, ModalScreen
from textual.message import Message
from typing import Optional, List, Dict, Tuple
import random
from pathlib import Path
from datetime import datetime

try:
    import yaml
except ImportError:
    yaml = None

from .core.models import (
    GameState, PlayerConfig, Company, Founder,
    LegalForm, FoundersAgreement,
    ActionMode, ActionPointSystem, CostCalculator,
)
from .utils.guidance import (
    get_priority_action as _get_priority_action_shared,
    get_risk_indicators as _get_risk_indicators_shared,
    has_partner as _has_partner_shared,
    pluralize_months as _pluralize_months_shared,
)


def _shorten_text(text: str, max_len: int) -> str:
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


def _pluralize_months(n: int) -> str:
    return _pluralize_months_shared(n)


def get_risk_indicators(game_state: GameState, config: Optional[PlayerConfig]) -> str:
    return _get_risk_indicators_shared(game_state, config)


def set_game_subtitle(app: App, game_state: Optional[GameState], config: Optional[PlayerConfig]) -> None:
    if not game_state or not config:
        return
    risk_bar = get_risk_indicators(game_state, config)
    app.sub_title = f"Mies. {game_state.current_month} | {risk_bar}"


EDUCATIONAL_CONTENT = {
    "register": {
        "educational_why": "Rejestracja spółki chroni majątek osobisty i ułatwia sprzedaż/inwestycje.",
        "statistics": "73% inwestorów odmawia rozmów bez zarejestrowanej spółki.",
        "common_mistake": "Błąd: \"Zarejestruję jak znajdę inwestora\". Dobrze: rejestracja w mies. 1-2.",
    },
    "sha": {
        "educational_why": "SHA ustala zasady współpracy founderów i zmniejsza ryzyko konfliktów.",
        "statistics": "67% konfliktów founderów wynika z braku SHA.",
        "common_mistake": "Błąd: odkładanie SHA. Dobrze: podpis przed wspólną pracą.",
    },
    "mvp": {
        "educational_why": "MVP to najszybsza droga do walidacji i feedbacku od rynku.",
        "statistics": "42% startupów upada bo buduje produkt którego nikt nie chce.",
        "common_mistake": "Błąd: perfekcjonizm. Dobrze: wypuść szybko i iteruj.",
    },
    "customers": {
        "educational_why": "Płacący klienci to walidacja (PMF) i MRR.",
        "statistics": "Startup z 10+ płacącymi klientami ma większą szansę na finansowanie.",
        "common_mistake": "Błąd: \"najpierw produkt, potem sprzedaż\". Dobrze: sprzedaż od dnia 1.",
    },
}


# ============================================================================
# EKRANY GRY
# ============================================================================

class WelcomeScreen(Screen):
    """Ekran powitalny"""
    
    BINDINGS = [
        Binding("enter", "start", "Nowa gra"),
        Binding("q", "quit", "Wyjście"),
    ]
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("🚀 BIZNES", classes="title"),
            Static("Symulator Startupu v2.0", classes="subtitle"),
            Rule(),
            Static("Edukacyjna gra o zakładaniu firmy w Polsce", classes="desc"),
            Static(""),
            Static("Naucz się:", classes="learn-header"),
            Static("  • Vestingu i umów wspólników"),
            Static("  • Form prawnych (PSA vs Sp. z o.o.)"),
            Static("  • Finansów startupowych"),
            Static(""),
            Button("▶ Rozpocznij grę", id="start", variant="primary"),
            Button("❓ Pomoc", id="help", variant="default"),
            Button("✕ Wyjście", id="quit", variant="error"),
            classes="welcome-box"
        )
        yield Footer()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start":
            self.app.push_screen(SetupScreen())
        elif event.button.id == "help":
            self.app.push_screen(HelpScreen())
        elif event.button.id == "quit":
            self.app.exit()
    
    def action_start(self) -> None:
        self.app.push_screen(SetupScreen())
    
    def action_quit(self) -> None:
        self.app.exit()


class SetupScreen(Screen):
    """Ekran konfiguracji gry"""
    
    BINDINGS = [
        Binding("escape", "back", "Wróć"),
    ]
    
    def __init__(self):
        super().__init__()
        self.config = PlayerConfig()
        self.step = 0
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("⚙️ KONFIGURACJA GRY", classes="screen-title"),
            Rule(),
            Container(id="setup-content"),
            classes="setup-box"
        )
        yield Footer()
    
    def on_mount(self) -> None:
        self._show_step()
    
    def _show_step(self) -> None:
        content = self.query_one("#setup-content")
        content.remove_children()
        
        if self.step == 0:
            # Rola gracza
            content.mount(
                Static("ETAP 1/4: Twoja rola", classes="step-title"),
                Static(""),
                ListView(
                    ListItem(Label("💻 Technical (programista)"), id="technical"),
                    ListItem(Label("📊 Business (sprzedaż)"), id="business"),
                    id="role-list"
                )
            )
        elif self.step == 1:
            # MVP
            content.mount(
                Static("ETAP 2/4: Masz MVP?", classes="step-title"),
                Static(""),
                ListView(
                    ListItem(Label("✓ Tak, mam prototyp"), id="mvp-yes"),
                    ListItem(Label("✗ Nie, zaczynam od zera"), id="mvp-no"),
                    id="mvp-list"
                )
            )
        elif self.step == 2:
            # Partner
            content.mount(
                Static("ETAP 3/4: Masz partnera?", classes="step-title"),
                Static(""),
                ListView(
                    ListItem(Label("👥 Tak, mam co-foundera"), id="partner-yes"),
                    ListItem(Label("🧑 Nie, działam solo"), id="partner-no"),
                    id="partner-list"
                )
            )
        elif self.step == 3:
            # Forma prawna
            content.mount(
                Static("ETAP 4/4: Forma prawna", classes="step-title"),
                Static(""),
                ListView(
                    ListItem(Label("🏢 PSA - Prosta Spółka Akcyjna [ZALECANE]"), id="psa"),
                    ListItem(Label("🏛️ Sp. z o.o. - Spółka z o.o."), id="sp_zoo"),
                    id="legal-list"
                ),
                Static(""),
                Static("PSA: kapitał 1 PLN, praca jako wkład", classes="hint"),
                Static("Sp. z o.o.: kapitał min 5000 PLN", classes="hint")
            )
        else:
            # Rozpocznij grę
            self._start_game()
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item_id = event.item.id
        
        if self.step == 0:
            self.config.player_role = "technical" if item_id == "technical" else "business"
            self.config.player_name = "Founder"
        elif self.step == 1:
            self.config.player_has_mvp = (item_id == "mvp-yes")
            if self.config.player_has_mvp:
                self.config.mvp_calculated_value = 24000  # Default
        elif self.step == 2:
            self.config.has_partner = (item_id == "partner-yes")
            if self.config.has_partner:
                self.config.partner_name = "Partner"
                self.config.player_equity = 45
                self.config.partner_equity = 45
            else:
                self.config.player_equity = 90
                self.config.partner_equity = 0
            self.config.esop_pool = 10
        elif self.step == 3:
            self.config.legal_form = "psa" if item_id == "psa" else "sp_zoo"
        
        self.step += 1
        self._show_step()
    
    def _start_game(self) -> None:
        # Default values
        self.config.initial_cash = 10000
        self.config.monthly_burn = 5000
        self.config.target_mrr_12_months = 10000
        self.config.target_customers_12_months = 50
        
        self.app.config = self.config
        self.app.pop_screen()
        self.app.push_screen(GameScreen())
    
    def action_back(self) -> None:
        if self.step > 0:
            self.step -= 1
            self._show_step()
        else:
            self.app.pop_screen()


class EventModal(ModalScreen):
    """Modal dla losowych zdarzeń"""
    
    BINDINGS = [Binding("enter", "dismiss", "OK"), Binding("escape", "dismiss", "OK")]
    
    def __init__(self, event_type: str, name: str, desc: str, effect: str):
        super().__init__()
        self.event_type = event_type
        self.event_name = name
        self.event_desc = desc
        self.event_effect = effect
    
    def compose(self) -> ComposeResult:
        color_class = "event-positive" if self.event_type == "positive" else "event-negative"
        yield Container(
            Static(f"⚡ ZDARZENIE", classes="modal-title"),
            Rule(),
            Static(self.event_name, classes=color_class),
            Static(self.event_desc, classes="event-desc"),
            Static(""),
            Static(f"Efekt: {self.event_effect}", classes="event-effect"),
            Rule(),
            Static("[Enter] OK", classes="modal-hint"),
            classes="event-modal"
        )
    
    def action_dismiss(self) -> None:
        self.app.pop_screen()


class WarningsModal(ModalScreen):
    """Modal ostrzeżeń przed przejściem do następnego miesiąca"""

    BINDINGS = [
        Binding("enter", "confirm", "Kontynuuj"),
        Binding("escape", "cancel", "Anuluj"),
    ]

    def __init__(self, warnings: List[Dict]):
        super().__init__()
        self.warnings = warnings

    def compose(self) -> ComposeResult:
        items: List[Static] = []
        for w in self.warnings:
            if w.get("level") == "CRITICAL":
                icon = "🔴"
                color = "red"
            elif w.get("level") == "HIGH":
                icon = "🟡"
                color = "yellow"
            else:
                icon = "🟠"
                color = "cyan"

            title = w.get("title", "")
            message = w.get("message", "")
            action = w.get("action", "")

            items.append(Static(f"[bold {color}]{icon} {title}[/bold {color}]"))
            if message:
                items.append(Static(message))
            if action:
                items.append(Static(f"[cyan]→ {action}[/cyan]"))
            items.append(Static(""))

        yield Container(
            Static("⚠️ OSTRZEŻENIA", classes="modal-title"),
            Rule(),
            *items,
            Rule(),
            Horizontal(
                Button("Kontynuuj", id="confirm", variant="primary"),
                Button("Anuluj", id="cancel", variant="error"),
                classes="warnings-actions",
            ),
            Static("[Enter] Kontynuuj  |  [Esc] Anuluj", classes="modal-hint"),
            classes="warnings-modal",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm":
            self.dismiss(True)
        else:
            self.dismiss(False)

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)


class ActionResultModal(ModalScreen):
    """Modal z wynikiem i interpretacją wykonanej akcji"""

    BINDINGS = [
        Binding("enter", "dismiss", "OK"),
        Binding("escape", "dismiss", "OK"),
    ]

    def __init__(
        self,
        title: str,
        message: str,
        changes: List[str],
        meaning: List[str],
        next_priority: str,
    ):
        super().__init__()
        self.title = title
        self.message = message
        self.changes = changes
        self.meaning = meaning
        self.next_priority = next_priority

    def compose(self) -> ComposeResult:
        yield Container(
            Static("✅ REZULTAT AKCJI", classes="modal-title"),
            Rule(),
            Static(f"[bold]{self.title}[/bold]", classes="action-title"),
            Static(self.message or "", classes="action-message"),
            Rule(),
            Static("📊 ZMIANY", classes="section-title"),
            *[Static(line, classes="change-line") for line in (self.changes or ["Brak bezpośrednich zmian"])],
            Static(""),
            Static("💡 CO TO OZNACZA", classes="section-title"),
            *[Static(line, classes="meaning-line") for line in (self.meaning or [])],
            Static(""),
            Static(f"👉 NASTĘPNY PRIORYTET: {self.next_priority}", classes="next-priority"),
            Rule(),
            Button("OK", id="ok", variant="primary"),
            Static("[Enter] OK", classes="modal-hint"),
            classes="action-result-modal",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(True)

    def action_dismiss(self) -> None:
        self.dismiss(True)


class ModeSelectionModal(ModalScreen):
    """Modal wyboru trybu wykonania akcji (DIY vs outsource)"""

    BINDINGS = [Binding("escape", "cancel", "Anuluj")]

    def __init__(self, action_name: str, modes: List[ActionMode], remaining_points: int, cash: float):
        super().__init__()
        self.action_name = action_name
        self.modes = modes
        self.remaining_points = remaining_points
        self.cash = cash

    def compose(self) -> ComposeResult:
        items = []
        for i, m in enumerate(self.modes):
            can_afford = self.cash >= m.cost
            has_points = self.remaining_points >= m.time_cost
            available = can_afford and has_points

            cost_str = f"{m.cost:,.0f} PLN" if m.cost else "0 PLN"
            time_str = f"{m.time_cost} pkt"
            success_str = f"{m.success_rate * 100:.0f}%"

            if available:
                label = f"✓ {m.name}  |  💰 {cost_str}  |  ⚡ {time_str}  |  🎯 {success_str}"
            else:
                reason = "brak gotówki" if not can_afford else "brak punktów"
                label = f"✗ {m.name}  ({reason})"

            item = ListItem(Label(label), id=f"mode-{i}")
            if not available:
                item.disabled = True
            items.append(item)

        yield Container(
            Static(f"⚙️ WYBIERZ TRYB: {self.action_name}", classes="modal-title"),
            Rule(),
            Static(f"Pozostało punktów: {self.remaining_points}  |  Gotówka: {self.cash:,.0f} PLN", classes="mode-info"),
            Static(""),
            ListView(*items, id="mode-list"),
            Rule(),
            Static("[Enter] Wybierz  |  [Esc] Anuluj", classes="modal-hint"),
            classes="mode-selection-modal",
        )

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if not event.item.id or not event.item.id.startswith("mode-"):
            return
        idx = int(event.item.id.split("-")[1])
        if idx < len(self.modes):
            self.dismiss(self.modes[idx])

    def action_cancel(self) -> None:
        self.dismiss(None)


class RiskModal(ModalScreen):
    """Modal dla analizy ryzyka"""
    
    BINDINGS = [Binding("escape", "dismiss", "Zamknij")]
    
    def __init__(self, game_state: GameState, config):
        super().__init__()
        self.game_state = game_state
        self.config = config
    
    def compose(self) -> ComposeResult:
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
        
        if _has_partner_shared(self.game_state, self.config) and not self.game_state.agreement_signed:
            risks.append(("KRYTYCZNE", "Brak umowy wspólników!"))
            score += 30
        
        if not c.registered and self.game_state.current_month > 3:
            risks.append(("WYSOKIE", "Spółka niezarejestrowana"))
            score += 15
        
        if not c.mvp_completed and self.game_state.current_month > 6:
            risks.append(("ŚREDNIE", "MVP nieukończone po 6 mies"))
            score += 10
        
        risk_color = "risk-low" if score < 30 else "risk-medium" if score < 60 else "risk-high"
        
        yield Container(
            Static("📊 ANALIZA RYZYKA", classes="modal-title"),
            Rule(),
            Static(f"Poziom ryzyka: {score}/100", classes=risk_color),
            Static(""),
            *[Static(f"{'🔴' if r[0] == 'KRYTYCZNE' else '🟡' if r[0] == 'WYSOKIE' else '🟠'} {r[0]}: {r[1]}") for r in risks] if risks else [Static("✅ Brak krytycznych ryzyk")],
            Rule(),
            Button("← Zamknij", id="close"),
            classes="risk-modal"
        )
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.app.pop_screen()
    
    def action_dismiss(self) -> None:
        self.app.pop_screen()


class GameScreen(Screen):
    """Główny ekran gry"""
    
    BINDINGS = [
        Binding("m", "next_month", "Następny miesiąc"),
        Binding("t", "progress", "Postęp"),
        Binding("r", "show_risk", "Ryzyko"),
        Binding("k", "mentor", "Mentor"),
        Binding("o", "report", "Raport"),
        Binding("g", "glossary", "Słownik"),
        Binding("f", "finanse", "Finanse"),
        Binding("p", "portfele", "Portfele"),
        Binding("e", "equity", "Equity"),
        Binding("h", "historia", "Historia"),
        Binding("s", "save_game", "Zapisz"),
        Binding("l", "load_game", "Wczytaj"),
        Binding("q", "quit_game", "Wyjście"),
    ]
    
    def __init__(self):
        super().__init__()
        self.game_state: Optional[GameState] = None
        self.action_history: List[Dict] = []
        self.actions_this_month = 0  # zużyte punkty akcji
        self.max_action_points = 4   # dynamicznie przeliczane
        self.actions_taken_this_month = 0
        self.max_actions_taken_per_month = 6
        self.current_actions: List[Dict] = []
        self._actions_render_counter: int = 0
        self._action_point_system = ActionPointSystem()
        self._cost_calculator = CostCalculator()
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Horizontal(
            # Lewa kolumna - nawigacja drzewem + status
            Vertical(
                Static("🧭 NAWIGACJA", classes="panel-title"),
                Tree("Menu", id="nav-tree"),
                Rule(),
                Static("📊 STATUS", classes="panel-title"),
                Static(id="status-panel", classes="status-content"),
                classes="left-panel"
            ),
            # Środkowa kolumna - akcje
            Vertical(
                Static("⚡ AKCJE", classes="panel-title"),
                ScrollableContainer(
                    ListView(id="actions-list"),
                    id="actions-container"
                ),
                Static(id="actions-remaining", classes="actions-info"),
                classes="center-panel"
            ),
            # Prawa kolumna - podgląd akcji
            Vertical(
                Static("🔍 PODGLĄD", classes="panel-title"),
                ScrollableContainer(
                    Static(id="action-preview", classes="preview-content"),
                    id="preview-container"
                ),
                classes="right-panel"
            ),
            classes="game-layout"
        )
        yield Footer()
    
    def on_mount(self) -> None:
        self._initialize_game()
        self._setup_nav_tree()
        self._update_display()
    
    def _setup_nav_tree(self) -> None:
        """Konfiguruje drzewo nawigacji"""
        tree = self.query_one("#nav-tree", Tree)
        tree.root.expand()
        
        info = tree.root.add("📋 Informacje")
        info.add_leaf("💰 Finanse", data="finanse")
        info.add_leaf("🎯 Postęp vs cele", data="progress")
        info.add_leaf("💼 Portfele", data="portfele")
        info.add_leaf("📊 Equity", data="equity")
        info.add_leaf("📜 Historia", data="historia")
        info.expand()
        
        tools = tree.root.add("🛠️ Narzędzia")
        tools.add_leaf("⚠️ Ryzyko", data="risk")
        tools.add_leaf("💡 Mentor", data="mentor")
        tools.add_leaf("📋 Raport miesięczny", data="report")
        tools.add_leaf("📚 Słownik", data="glossary")
        tools.add_leaf("❓ Pomoc", data="help")
        tools.expand()
    
    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Obsługa nawigacji drzewem"""
        data = event.node.data
        if data == "finanse":
            self.action_finanse()
        elif data == "progress":
            self.action_progress()
        elif data == "portfele":
            self.action_portfele()
        elif data == "equity":
            self.action_equity()
        elif data == "historia":
            self.action_historia()
        elif data == "risk":
            self.action_show_risk()
        elif data == "mentor":
            self.action_mentor()
        elif data == "report":
            self.action_report()
        elif data == "glossary":
            self.action_glossary()
        elif data == "help":
            self.app.push_screen(HelpScreen())
    
    def _initialize_game(self) -> None:
        config = self.app.config
        
        self.game_state = GameState(
            player_name=config.player_name,
            player_role=config.player_role
        )
        
        company = Company(name=f"{config.player_name}'s Startup")
        company.legal_form = LegalForm.PSA if config.legal_form == "psa" else LegalForm.SP_ZOO
        company.cash_on_hand = config.initial_cash
        company.monthly_burn_rate = config.monthly_burn
        company.esop_pool_percentage = config.esop_pool
        company.mvp_completed = config.player_has_mvp
        
        player = Founder(
            name=config.player_name,
            role=config.player_role,
            equity_percentage=config.player_equity,
            brought_mvp=config.player_has_mvp,
            is_player=True,
            personal_cash=getattr(config, 'personal_savings', 20000.0),
        )
        company.founders.append(player)
        
        if config.has_partner:
            partner = Founder(
                name=config.partner_name,
                role="business" if config.player_role == "technical" else "technical",
                equity_percentage=config.partner_equity,
                is_player=False
            )
            company.founders.append(partner)
        
        self.game_state.company = company
        self.game_state.founders_agreement = FoundersAgreement()
        self.game_state.mvp_progress = 100 if config.player_has_mvp else 0

        # Inicjalizuj dynamiczny burn
        company.founder_living_cost = config.monthly_burn
        company.cost_multiplier = 1.0
        company.extra_monthly_costs = 0.0
        self._recalculate_company_burn()
        self._recalculate_action_points()

    def _recalculate_company_burn(self) -> None:
        """Przelicz dynamiczny burn na podstawie stanu gry"""
        if not self.game_state:
            return
        self.game_state.company.monthly_burn_rate = float(
            self._cost_calculator.total_burn(self.game_state)
        )

    def _recalculate_action_points(self) -> None:
        """Przelicz dostępne punkty akcji na podstawie stanu gry"""
        if not self.game_state:
            return
        self.max_action_points = self._action_point_system.calculate(self.game_state)

    def _get_risk_indicators(self) -> str:
        if not self.game_state:
            return ""
        return get_risk_indicators(self.game_state, self.app.config)

    def _get_priority_action(self) -> Tuple[str, str, str]:
        if not self.game_state:
            return ("", "", "")
        return _get_priority_action_shared(self.game_state, self.app.config)

    def _check_warnings_before_month(self) -> List[Dict]:
        if not self.game_state:
            return []

        warnings: List[Dict] = []
        c = self.game_state.company
        month = self.game_state.current_month

        effective_mrr = c.mrr
        if getattr(self.game_state, "revenue_advance_months", 0) > 0:
            effective_mrr = max(0.0, c.mrr - getattr(self.game_state, "revenue_advance_mrr", 0.0))

        net_burn = c.monthly_burn_rate - effective_mrr
        projected_cash = c.cash_on_hand - net_burn

        if projected_cash < 0:
            warnings.append({
                "level": "CRITICAL",
                "title": "BANKRUCTWO ZA 1 MIESIĄC",
                "message": f"Po tym miesiącu: {projected_cash:,.0f} PLN",
                "action": "Natychmiast szukaj finansowania lub obetnij koszty",
            })
        elif c.runway_months() <= 3:
            warnings.append({
                "level": "HIGH",
                "title": "NISKI RUNWAY",
                "message": f"Pozostało tylko {_pluralize_months(c.runway_months())}",
                "action": "Zacznij szukać inwestora lub klientów",
            })

        if _has_partner_shared(self.game_state, self.app.config) and not self.game_state.agreement_signed and month >= 3:
            warnings.append({
                "level": "HIGH",
                "title": "RYZYKO KONFLIKTU",
                "message": f"{month}+ miesiące bez SHA = rosnące ryzyko sporów",
                "action": "Podpisz SHA ASAP",
            })

        if month >= 6 and c.paying_customers < 5:
            warnings.append({
                "level": "MEDIUM",
                "title": "BRAK PRODUCT-MARKET FIT",
                "message": f"Po {month} mies. masz tylko {c.paying_customers} klientów",
                "action": "Rozważ pivot lub intensywną sprzedaż",
            })

        if not c.mvp_completed and month >= 4:
            warnings.append({
                "level": "MEDIUM",
                "title": "MVP OPÓŹNIONE",
                "message": f"Po {month} miesiącach MVP wciąż w {self.game_state.mvp_progress}%",
                "action": "Skup się na ukończeniu MVP",
            })

        return warnings

    def _on_month_warnings_result(self, result: bool) -> None:
        if result:
            self._advance_month()

    def _advance_month(self) -> None:
        if not self.game_state:
            return

        self.game_state.current_month += 1
        self.actions_this_month = 0
        self.actions_taken_this_month = 0
        self._recalculate_company_burn()
        self._recalculate_action_points()

        c = self.game_state.company

        effective_mrr = c.mrr
        if getattr(self.game_state, "revenue_advance_months", 0) > 0:
            effective_mrr = max(0.0, c.mrr - getattr(self.game_state, "revenue_advance_mrr", 0.0))

        net_burn = c.monthly_burn_rate - effective_mrr
        c.cash_on_hand -= net_burn

        if getattr(self.game_state, "revenue_advance_months", 0) > 0:
            self.game_state.revenue_advance_months -= 1
            if self.game_state.revenue_advance_months <= 0:
                self.game_state.revenue_advance_months = 0
                self.game_state.revenue_advance_mrr = 0.0

        if c.paying_customers > 0:
            growth = random.uniform(0.02, 0.08)
            new_cust = max(1, int(c.paying_customers * growth))
            avg_rev = c.mrr / c.paying_customers if c.paying_customers else 200
            c.total_customers += new_cust
            c.paying_customers += new_cust
            c.mrr += new_cust * avg_rev

        if random.random() < 0.4:
            self._random_event()

        if c.cash_on_hand < 0:
            self.app.push_screen(GameOverScreen(success=False))
        elif c.mrr >= self.app.config.target_mrr_12_months:
            self.app.push_screen(GameOverScreen(success=True))

        self._update_display()
    
    def _update_display(self) -> None:
        self._update_status()
        self._update_actions()
    
    def _update_status(self) -> None:
        if not self.game_state:
            return
        
        c = self.game_state.company
        month = self.game_state.current_month
        runway = c.runway_months()

        risk_bar = self._get_risk_indicators()
        risk_style = "red" if "🔴" in risk_bar else "yellow" if ("🟡" in risk_bar or "🟠" in risk_bar) else "green"

        if hasattr(self.app, "sub_title"):
            set_game_subtitle(self.app, self.game_state, self.app.config)

        prio_action, prio_why, prio_consequence = self._get_priority_action()
        
        status_text = f"""
[bold]Miesiąc {month}[/bold]

💰 Gotówka: {c.cash_on_hand:,.0f} PLN
📈 MRR: {c.mrr:,.0f} PLN
👥 Klienci: {c.paying_customers}
⏱️ Runway: {runway} mies

🏢 Spółka: {'✓' if c.registered else '✗'}
📝 SHA: {'✓' if self.game_state.agreement_signed else '✗'}
🔧 MVP: {'✓' if c.mvp_completed else f'{self.game_state.mvp_progress}%'}

[{risk_style}]⚠️ {risk_bar}[/{risk_style}]

[bold yellow]🎯 PRIORYTET TERAZ[/bold yellow]
[bold]{prio_action}[/bold]
[dim]{prio_why}[/dim]
{f'[red]{prio_consequence}[/red]' if prio_consequence else ''}
"""
        self.query_one("#status-panel", Static).update(status_text)
    
    def _update_actions(self) -> None:
        actions_list = self.query_one("#actions-list", ListView)
        actions_list.clear()

        self._actions_render_counter += 1
        render_counter = self._actions_render_counter
        
        self.current_actions = self._get_available_actions()
        
        for i, action in enumerate(self.current_actions):
            if action['available']:
                rec = "⭐ " if action.get('recommended') else ""
                item = ListItem(Label(f"✓ {rec}{action['name']}"), id=f"action-{i}-{render_counter}")
            else:
                item = ListItem(Label(f"✗ {action['name']}"), id=f"action-{i}-{render_counter}")
                item.disabled = True
            actions_list.append(item)
        
        remaining = max(0, self.max_action_points - self.actions_this_month)
        self.query_one("#actions-remaining", Static).update(
            f"⚡ Punkty akcji: {remaining}/{self.max_action_points}  |  [M] nowy miesiąc"
        )
        
        # Wyczyść podgląd
        self.query_one("#action-preview", Static).update("Wybierz akcję aby zobaczyć szczegóły...")
    
    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Pokazuje podgląd akcji przy nawigacji strzałkami"""
        if not event.item or not event.item.id:
            return
        
        if not event.item.id.startswith("action-"):
            return
        
        idx = int(event.item.id.split("-")[1])
        if idx < len(self.current_actions):
            action = self.current_actions[idx]
            self._show_action_preview(action)
    
    def _show_action_preview(self, action: Dict) -> None:
        """Wyświetla podgląd akcji z ryzykami i korzyściami"""
        preview = self.query_one("#action-preview", Static)
        
        lines = [f"[bold]{action['name']}[/bold]\n"]
        
        if action.get('description'):
            lines.append(f"{action['description']}\n")
        
        if action.get('cost'):
            lines.append(f"💰 Koszt: {action['cost']:,} PLN\n")
        
        if action.get('consequences'):
            lines.append("[yellow]📋 KONSEKWENCJE:[/yellow]")
            for c in action['consequences']:
                lines.append(f"  • {c}")
            lines.append("")
        
        if action.get('benefits'):
            lines.append("[green]✓ KORZYŚCI:[/green]")
            for b in action['benefits']:
                lines.append(f"  • {b}")
            lines.append("")
        
        if action.get('risks'):
            lines.append("[red]⚠️ RYZYKA:[/red]")
            for r in action['risks']:
                lines.append(f"  • {r}")
            lines.append("")
        
        if action.get('warning'):
            lines.append(f"[bold red]{action['warning']}[/bold red]")

        if getattr(self.app, "mentor_mode", False):
            edu = EDUCATIONAL_CONTENT.get(action.get("id", ""), {})
            if edu:
                lines.append("")
                lines.append("[bold cyan]💡 MENTOR[/bold cyan]")
                if edu.get("educational_why"):
                    lines.append(f"[cyan]{edu['educational_why']}[/cyan]")
                if edu.get("statistics"):
                    lines.append(f"[yellow]📊 {edu['statistics']}[/yellow]")
                if edu.get("common_mistake"):
                    lines.append(f"[red]⚠️ {edu['common_mistake']}[/red]")
        
        if not action['available']:
            lines.append(f"\n[dim]❌ {action.get('blocked', 'Niedostępne')}[/dim]")
        elif action.get('recommended'):
            lines.append("\n[bold green]⭐ ZALECANE[/bold green]")
        
        preview.update("\n".join(lines))
    
    def _get_available_actions(self) -> List[Dict]:
        c = self.game_state.company
        month = self.game_state.current_month
        actions = []
        
        # PRAWNE
        if not c.registered:
            cost = 2000 if c.legal_form == LegalForm.PSA else 2500
            actions.append({
                'id': 'register', 'name': '🏢 Załóż spółkę',
                'description': f"Zarejestruj {c.legal_form.value.upper()} w KRS",
                'available': c.cash_on_hand >= cost,
                'blocked': f'Potrzebujesz {cost} PLN' if c.cash_on_hand < cost else '',
                'recommended': month >= 1,
                'cost': cost,
                'consequences': [f"Koszt: {cost} PLN", "Czas: 1-2 tygodnie"],
                'benefits': ["Ochrona prawna", "Możliwość pozyskania inwestora", "Profesjonalny wizerunek"],
                'risks': ["Koszty księgowości (~500-1500 PLN/mies)"]
            })
        
        has_partner = len([f for f in c.founders if not f.is_player]) > 0
        if not self.game_state.agreement_signed:
            sha_modes = [
                ActionMode(name="📝 DIY (szablon)", cost=500, time_cost=2, success_rate=0.5, quality_modifier=0.7),
                ActionMode(name="⚖️ Prawnik (standard)", cost=5000, time_cost=1, success_rate=0.95, quality_modifier=1.0),
                ActionMode(name="🏆 Kancelaria premium", cost=12000, time_cost=1, success_rate=0.99, quality_modifier=1.2),
            ]
            min_cost = min(m.cost for m in sha_modes if c.cash_on_hand >= m.cost) if any(c.cash_on_hand >= m.cost for m in sha_modes) else 5000
            actions.append({
                'id': 'sha', 'name': '📝 Podpisz SHA',
                'description': "Shareholders Agreement - umowa wspólników",
                'available': has_partner and any(c.cash_on_hand >= m.cost for m in sha_modes),
                'blocked': 'Brak partnera' if not has_partner else f'Potrzebujesz min {min_cost} PLN' if not any(c.cash_on_hand >= m.cost for m in sha_modes) else '',
                'recommended': has_partner,
                'cost': min_cost,
                'modes': sha_modes,
                'consequences': ["Koszt: 500-12000 PLN zależnie od trybu"],
                'benefits': ["Jasne zasady vestingu", "Ochrona przed bad leaver", "Procedury rozwiązywania sporów"],
                'risks': ["Bez umowy: KRYTYCZNE RYZYKO sporów!"],
                'warning': "⚠️ BEZ UMOWY RYZYKUJESZ WSZYSTKO!" if has_partner else ""
            })

        # PARTNER
        if not has_partner:
            actions.append({
                'id': 'invite_partner', 'name': '👥 Zaproś wspólnika',
                'description': "Dodaj co-foundera do spółki",
                'available': True,
                'recommended': not self.game_state.agreement_signed,
                'consequences': ["Partner otrzyma 20% equity", "Twoje equity spadnie"],
                'benefits': ["Podział obowiązków", "Więcej kompetencji", "Mniejsze ryzyko wypalenia"],
                'risks': ["Rozwodnienie", "Potencjalne konflikty (podpisz SHA!)"]
            })
        else:
            partner = next((f for f in c.founders if not f.is_player and not f.left_company), None)
            if partner:
                vesting_info = f"Vested: {partner.vested_percentage:.0f}%" if self.game_state.agreement_signed else "Brak SHA"
                actions.append({
                    'id': 'partner_leaves', 'name': '⚖️ Rozstanie z partnerem',
                    'description': f"Partner odchodzi ({vesting_info})",
                    'available': True,
                    'consequences': ["Zmiana struktury equity"],
                    'benefits': ["Pełna kontrola"],
                    'risks': ["Bez SHA: partner zachowuje equity!"],
                    'warning': "⚠️ Sprawdź klauzulę leaver!" if self.game_state.agreement_signed else "⚠️ BRAK SHA!"
                })
        
        # PRODUKT
        if not c.mvp_completed:
            mvp_modes = [
                ActionMode(name="🔧 Zrób sam (DIY)", cost=0, time_cost=1, success_rate=0.7, quality_modifier=1.0),
                ActionMode(name="💻 Freelancer", cost=3000, time_cost=1, success_rate=0.85, quality_modifier=1.2),
                ActionMode(name="🏢 Agencja dev", cost=8000, time_cost=1, success_rate=0.95, quality_modifier=1.4),
            ]
            actions.append({
                'id': 'mvp', 'name': '🔧 Rozwijaj MVP',
                'description': "Kontynuuj prace nad produktem",
                'available': True,
                'recommended': True,
                'modes': mvp_modes,
                'consequences': ["Postęp: +20-40% zależnie od trybu"],
                'benefits': ["Przybliża do klientów", "Walidacja pomysłu"],
                'risks': ["DIY: 70% sukces", "Freelancer: 85%", "Agencja: 95%"]
            })
        
        if c.mvp_completed or self.game_state.mvp_progress >= 100:
            actions.append({
                'id': 'customers', 'name': '🎯 Szukaj klientów',
                'description': "Aktywna sprzedaż i akwizycja",
                'available': True,
                'recommended': c.paying_customers < 10,
                'consequences': ["Potencjał: 1-5 nowych klientów"],
                'benefits': ["Walidacja produktu", "Wzrost MRR", "Feedback od użytkowników"],
                'risks': ["Możliwe odrzucenia"]
            })
        
        # FINANSOWE
        if c.registered and c.mrr > 0:
            actions.append({
                'id': 'investor', 'name': '💰 Szukaj inwestora',
                'description': "Rozmowy z VC/aniołami biznesu",
                'available': c.registered and self.game_state.agreement_signed,
                'blocked': 'Najpierw SHA' if not self.game_state.agreement_signed else 'Zarejestruj spółkę' if not c.registered else '',
                'consequences': ["Czas: 3-6 miesięcy", "Rozwodnienie 15-25%"],
                'benefits': ["Kapitał na rozwój", "Kontakty i mentoring", "Walidacja przez smart money"],
                'risks': ["Utrata kontroli", "Presja na szybki wzrost", "Due diligence"]
            })
        
        if c.registered and c.cash_on_hand > 20000:
            actions.append({
                'id': 'hire', 'name': '👥 Zatrudnij pracownika',
                'description': "Dodaj osobę do zespołu",
                'available': True,
                'consequences': ["Koszt: ~12000 PLN/mies"],
                'benefits': ["Szybszy rozwój", "Nowe kompetencje"],
                'risks': ["Zwiększony burn rate", "Zobowiązania prawne"]
            })
        
        # SPECJALNE
        if month > 6 and not c.product_market_fit and c.paying_customers < 5:
            actions.append({
                'id': 'pivot', 'name': '🔄 Rozważ pivot',
                'description': "Zmień kierunek produktu",
                'available': True,
                'consequences': ["Reset części pracy", "Strata 40% postępu MVP"],
                'benefits': ["Szansa na lepszy PMF", "Nowa perspektywa"],
                'risks': ["Strata trakcji", "Strata klientów"],
                'warning': "⚠️ 6+ mies bez PMF - rozważ zmianę kierunku"
            })

        if c.runway_months() < 2:
            actions.append({
                'id': 'cut_costs', 'name': '🔻 Obetnij koszty',
                'description': "Zmniejsz burn rate o 30-50%",
                'available': True,
                'recommended': True,
                'consequences': ["Burn -30-50%", "Możliwe zwolnienia"],
                'benefits': ["Wydłużony runway"],
                'risks': ["Wolniejszy rozwój"],
                'warning': "⚠️ TRYB PRZETRWANIA"
            })

            actions.append({
                'id': 'emergency_funding', 'name': '💸 Pożyczka ratunkowa',
                'description': "Szybka pożyczka na przetrwanie",
                'available': True,
                'consequences': ["Dług: 10-20k PLN", "Oprocentowanie 15-20%"],
                'benefits': ["Natychmiastowa gotówka"],
                'risks': ["Obciążenie finansowe"],
                'warning': "⚠️ OSTATECZNOŚĆ"
            })

            if c.mrr > 0:
                active = getattr(self.game_state, 'revenue_advance_months', 0) > 0
                actions.append({
                    'id': 'revenue_advance', 'name': '💰 Zaliczka na przychody',
                    'description': "Sprzedaj przyszłe przychody za gotówkę teraz",
                    'available': (c.mrr >= 1000) and (not active),
                    'blocked': 'Masz już aktywną zaliczkę lub MRR < 1000' if ((c.mrr < 1000) or active) else '',
                    'consequences': [f"Otrzymasz ~{c.mrr * 3:,.0f} PLN", "Stracisz 3 mies. MRR"],
                    'benefits': ["Szybka gotówka bez długu"],
                    'risks': ["Mniejszy cashflow przez 3 mies."]
                })
        
        # AKCJE PORTFELA OSOBISTEGO
        player = next((f for f in c.founders if f.is_player), None)
        if player:
            if player.personal_cash >= 5000:
                actions.append({
                    'id': 'founder_loan', 'name': '💵 Pożycz firmie',
                    'description': f"Twoja gotówka: {player.personal_cash:,.0f} PLN",
                    'available': True,
                    'consequences': ["Transfer z portfela osobistego"],
                    'benefits': ["Szybka gotówka dla firmy"],
                    'risks': ["Ryzyko osobiste"]
                })
            
            if c.registered and c.cash_on_hand >= 5000:
                actions.append({
                    'id': 'founder_salary', 'name': '💰 Wypłać pensję',
                    'description': f"Firma ma: {c.cash_on_hand:,.0f} PLN",
                    'available': True,
                    'consequences': ["Transfer do portfela osobistego"],
                    'benefits': ["Gotówka na życie"],
                    'risks': ["Mniejszy runway firmy"]
                })
            
            if player.personal_cash >= 10000 and c.registered:
                actions.append({
                    'id': 'founder_invest', 'name': '📈 Zainwestuj w firmę',
                    'description': "Formalne dokapitalizowanie",
                    'available': True,
                    'consequences': ["Zwiększenie kapitału"],
                    'benefits': ["Więcej gotówki na rozwój"],
                    'risks': ["Ryzyko utraty środków"]
                })

        actions.append({
            'id': 'skip', 'name': '⏭️ Pomiń (następny miesiąc)',
            'description': "Kontynuuj obecną strategię",
            'available': True,
            'consequences': ["Organiczny wzrost/spadek"]
        })
        
        return actions
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        remaining = self.max_action_points - self.actions_this_month
        if remaining <= 0 or self.actions_taken_this_month >= self.max_actions_taken_per_month:
            return
        
        item_id = event.item.id
        if not item_id or not item_id.startswith("action-"):
            return
        
        idx = int(item_id.split("-")[1])
        
        if idx < len(self.current_actions):
            action = self.current_actions[idx]
            if action['available']:
                modes = action.get('modes')
                if modes and len(modes) > 1:
                    self._show_mode_selection(action, modes, remaining)
                else:
                    self._execute_action(action, modes[0] if modes else None)

    def _show_mode_selection(self, action: Dict, modes: List[ActionMode], remaining_points: int) -> None:
        """Pokaż modal wyboru trybu dla akcji z wieloma trybami"""
        cash = self.game_state.company.cash_on_hand if self.game_state else 0

        def _on_mode_selected(selected_mode: Optional[ActionMode]) -> None:
            if selected_mode:
                self._execute_action(action, selected_mode)

        self.app.push_screen(
            ModeSelectionModal(action['name'], modes, remaining_points, cash),
            _on_mode_selected
        )
    
    def _execute_action(self, action: Dict, mode: Optional[ActionMode] = None) -> None:
        c = self.game_state.company
        time_cost = int(mode.time_cost) if mode else 1

        before_state = self._get_state_snapshot()
        effect_msg = ""
        
        if action['id'] == 'skip':
            self.action_next_month()
            return
        
        if action['id'] == 'register':
            cost = action.get('cost', 2000)
            if c.cash_on_hand >= cost:
                c.cash_on_hand -= cost
                c.registered = True
                effect_msg = f"-{cost} PLN, spółka zarejestrowana"
                self._log_action(action['name'], effect_msg)
        
        elif action['id'] == 'sha':
            selected = mode or ActionMode(name="Prawnik", cost=5000, time_cost=1, success_rate=0.95)
            if c.cash_on_hand < selected.cost:
                effect_msg = f"Brak środków ({selected.cost} PLN)"
                self._log_action(action['name'], effect_msg)
            else:
                c.cash_on_hand -= selected.cost
                if random.random() <= selected.success_rate:
                    self.game_state.agreement_signed = True
                    self.game_state.founders_agreement.signed = True
                    effect_msg = f"-{selected.cost} PLN, SHA podpisana"
                else:
                    effect_msg = f"-{selected.cost} PLN, negocjacje trwają..."
                self._log_action(action['name'], effect_msg)

        elif action['id'] == 'invite_partner':
            result = self._invite_partner()
            effect_msg = result[1]
            self._log_action(action['name'], effect_msg)

        elif action['id'] == 'partner_leaves':
            partner = next((f for f in c.founders if not f.is_player and not f.left_company), None)
            if partner:
                # W TUI domyślnie good leaver (uproszczenie)
                result = self.game_state.process_founder_leaving(partner, is_good_leaver=True)
                self.app.config.has_partner = False
                kept = result.get('equity_kept', 0)
                returned = result.get('equity_returned', 0)
                effect_msg = f"Partner odszedł. Zachował {kept:.0f}%, zwrócono {returned:.0f}%"
                if result.get('warning'):
                    effect_msg += f" ⚠️ {result['warning']}"
                self._log_action(action['name'], effect_msg)
            else:
                effect_msg = "Brak partnera"
                self._log_action(action['name'], effect_msg)
        
        elif action['id'] == 'mvp':
            selected = mode or ActionMode(name="DIY", cost=0, time_cost=1, success_rate=0.7, quality_modifier=1.0)
            if c.cash_on_hand < selected.cost:
                effect_msg = f"Brak środków ({selected.cost} PLN)"
                self._log_action(action['name'], effect_msg)
            else:
                if selected.cost:
                    c.cash_on_hand -= selected.cost
                if random.random() <= selected.success_rate:
                    base_progress = random.randint(20, 30)
                    progress = int(round(base_progress * float(selected.quality_modifier)))
                    progress = max(1, min(40, progress))
                    self.game_state.mvp_progress = min(100, self.game_state.mvp_progress + progress)
                    if self.game_state.mvp_progress >= 100:
                        c.mvp_completed = True
                        effect_msg = f"🎉 MVP ukończone! (-{selected.cost} PLN)" if selected.cost else "🎉 MVP ukończone!"
                    else:
                        effect_msg = f"+{progress}% (teraz: {self.game_state.mvp_progress}%)"
                        if selected.cost:
                            effect_msg += f" -{selected.cost} PLN"
                else:
                    effect_msg = "Nie udało się posunąć MVP w tym miesiącu"
                    if selected.cost:
                        effect_msg += f" (-{selected.cost} PLN)"
                self._log_action(action['name'], effect_msg)
        
        elif action['id'] == 'customers':
            new_customers = random.randint(1, 5)
            avg_mrr = random.randint(150, 350)
            c.total_customers += new_customers
            c.paying_customers += new_customers
            c.mrr += new_customers * avg_mrr
            effect_msg = f"+{new_customers} klientów, MRR +{new_customers * avg_mrr} PLN"
            self._log_action(action['name'], effect_msg)
        
        elif action['id'] == 'investor':
            if random.random() < 0.3:
                amount = random.randint(200, 500) * 1000
                dilution = random.randint(15, 25)
                c.cash_on_hand += amount
                c.total_raised += amount
                # Rozwodnienie
                for f in c.founders:
                    f.equity_percentage *= (1 - dilution/100)
                c.esop_pool_percentage *= (1 - dilution/100)
                effect_msg = f"🎯 +{amount:,} PLN za {dilution}%"
                self._log_action(action['name'], effect_msg)
            else:
                effect_msg = "Rozmowy trwają..."
                self._log_action(action['name'], effect_msg)
        
        elif action['id'] == 'hire':
            c.employees += 1
            c.monthly_burn_rate += 12000
            effect_msg = "+1 pracownik, burn +12k/mies"
            self._log_action(action['name'], effect_msg)
        
        elif action['id'] == 'pivot':
            self.game_state.mvp_progress = max(30, self.game_state.mvp_progress - 40)
            c.total_customers = c.total_customers // 2
            c.paying_customers = c.paying_customers // 2
            c.mrr = c.mrr // 2
            effect_msg = "Pivot! -40% MVP, -50% klientów"
            self._log_action(action['name'], effect_msg)

        elif action['id'] == 'cut_costs':
            reduction = random.uniform(0.3, 0.5)
            old_burn = c.monthly_burn_rate
            c.cost_multiplier *= (1 - reduction)
            self._recalculate_company_burn()
            saved = max(0, old_burn - c.monthly_burn_rate)
            effect_msg = f"Burn -{reduction*100:.0f}% ({saved:,.0f} PLN/mies)"
            self._log_action(action['name'], effect_msg)

        elif action['id'] == 'emergency_funding':
            amount = random.randint(10000, 20000)
            payment = int(amount * 0.015)
            c.cash_on_hand += amount
            c.extra_monthly_costs += payment
            self._recalculate_company_burn()
            effect_msg = f"+{amount:,.0f} PLN, rata ~{payment:,.0f}/mies"
            self._log_action(action['name'], effect_msg)

        elif action['id'] == 'revenue_advance':
            if c.mrr <= 0:
                effect_msg = "Brak MRR"
                self._log_action(action['name'], effect_msg)
            elif c.mrr < 1000:
                effect_msg = "MRR < 1000"
                self._log_action(action['name'], effect_msg)
            elif getattr(self.game_state, 'revenue_advance_months', 0) > 0:
                effect_msg = "Aktywna zaliczka"
                self._log_action(action['name'], effect_msg)
            else:
                advance = c.mrr * 3
                c.cash_on_hand += advance
                self.game_state.revenue_advance_months = 3
                self.game_state.revenue_advance_mrr = c.mrr
                effect_msg = f"+{advance:,.0f} PLN (3x MRR)"
                self._log_action(action['name'], effect_msg)

        elif action['id'] == 'founder_loan':
            player = next((f for f in c.founders if f.is_player), None)
            if player and player.personal_cash >= 5000:
                loan = min(int(player.personal_cash), 10000)  # Domyślnie 10k w TUI
                player.personal_cash -= loan
                player.personal_invested += loan
                c.cash_on_hand += loan
                effect_msg = f"Pożyczyłeś firmie {loan:,.0f} PLN"
                self._log_action(action['name'], effect_msg)
            else:
                effect_msg = "Brak środków osobistych"
                self._log_action(action['name'], effect_msg)

        elif action['id'] == 'founder_salary':
            player = next((f for f in c.founders if f.is_player), None)
            if player and c.registered and c.cash_on_hand >= 5000:
                salary = min(int(c.cash_on_hand - 2000), 8000)  # Domyślnie max 8k
                c.cash_on_hand -= salary
                player.personal_cash += salary
                player.total_received += salary
                effect_msg = f"Wypłaciłeś sobie {salary:,.0f} PLN"
                self._log_action(action['name'], effect_msg)
            else:
                effect_msg = "Brak środków w firmie"
                self._log_action(action['name'], effect_msg)

        elif action['id'] == 'founder_invest':
            player = next((f for f in c.founders if f.is_player), None)
            if player and player.personal_cash >= 10000 and c.registered:
                invest = min(int(player.personal_cash), 15000)  # Domyślnie max 15k
                player.personal_cash -= invest
                player.personal_invested += invest
                c.cash_on_hand += invest
                c.total_raised += invest
                effect_msg = f"Zainwestowałeś {invest:,.0f} PLN w firmę"
                self._log_action(action['name'], effect_msg)
            else:
                effect_msg = "Brak środków lub firma niezarejestrowana"
                self._log_action(action['name'], effect_msg)

        after_state = self._get_state_snapshot()
        self.actions_this_month += time_cost
        self.actions_taken_this_month += 1
        self._recalculate_company_burn()
        self._recalculate_action_points()
        remaining = self.max_action_points - self.actions_this_month
        pending_next_month = remaining <= 0 or self.actions_taken_this_month >= self.max_actions_taken_per_month
        self._update_display()

        changes = self._format_state_changes(before_state, after_state)
        meaning = self._explain_action_meaning(action.get('id', ''), before_state, after_state)
        next_priority = self._get_priority_action()[0]

        def _after_modal(_: bool) -> None:
            if pending_next_month:
                self.action_next_month()

        self.app.push_screen(
            ActionResultModal(action.get('name', ''), effect_msg, changes, meaning, next_priority),
            _after_modal,
        )

    def _get_state_snapshot(self) -> Dict:
        c = self.game_state.company
        return {
            "cash": c.cash_on_hand,
            "mrr": c.mrr,
            "customers": c.paying_customers,
            "registered": c.registered,
            "agreement_signed": self.game_state.agreement_signed,
            "mvp_progress": self.game_state.mvp_progress,
            "mvp_completed": c.mvp_completed,
            "burn": c.monthly_burn_rate,
            "runway": c.runway_months(),
        }

    def _format_state_changes(self, before: Dict, after: Dict) -> List[str]:
        lines: List[str] = []

        def _fmt_money(x: float) -> str:
            return f"{x:,.0f} PLN"

        if before.get("cash") != after.get("cash"):
            diff = after["cash"] - before["cash"]
            color = "green" if diff > 0 else "red"
            lines.append(f"💰 Gotówka: {before['cash']:,.0f} → [{color}]{after['cash']:,.0f}[/{color}] ({diff:+,.0f})")

        if before.get("mrr") != after.get("mrr"):
            diff = after["mrr"] - before["mrr"]
            color = "green" if diff > 0 else "red"
            lines.append(f"📈 MRR: {before['mrr']:,.0f} → [{color}]{after['mrr']:,.0f}[/{color}] ({diff:+,.0f})")

        if before.get("customers") != after.get("customers"):
            diff = after["customers"] - before["customers"]
            color = "green" if diff > 0 else "red"
            lines.append(f"👥 Klienci: {before['customers']} → [{color}]{after['customers']}[/{color}] ({diff:+d})")

        if before.get("registered") != after.get("registered"):
            lines.append("🏢 Spółka: [red]✗[/red] → [green]✓[/green]" if after.get("registered") else "🏢 Spółka: [green]✓[/green] → [red]✗[/red]")

        if before.get("agreement_signed") != after.get("agreement_signed"):
            lines.append("📝 SHA: [red]✗[/red] → [green]✓[/green]" if after.get("agreement_signed") else "📝 SHA: [green]✓[/green] → [red]✗[/red]")

        if before.get("mvp_progress") != after.get("mvp_progress"):
            diff = after["mvp_progress"] - before["mvp_progress"]
            lines.append(f"🔧 MVP: {before['mvp_progress']}% → [green]{after['mvp_progress']}%[/green] ({diff:+d}%)")

        if before.get("burn") != after.get("burn"):
            diff = after["burn"] - before["burn"]
            color = "red" if diff > 0 else "green"
            lines.append(
                f"🔥 Burn: {before['burn']:,.0f} → [{color}]{after['burn']:,.0f}[/{color}] PLN/mies ({diff:+,.0f})"
            )

        if before.get("runway") != after.get("runway"):
            diff = after["runway"] - before["runway"]
            color = "green" if diff > 0 else "red"
            lines.append(f"⏱️ Runway: {before['runway']} → [{color}]{after['runway']}[/{color}] mies ({diff:+d})")

        return lines

    def _explain_action_meaning(self, action_id: str, before: Dict, after: Dict) -> List[str]:
        lines: List[str] = []

        if action_id == "register":
            lines.append("• Możesz teraz legalnie wystawiać faktury i podpisywać umowy")
            lines.append("• Twój majątek osobisty jest lepiej chroniony")
            lines.append("• Od teraz pamiętaj o kosztach księgowości")
        elif action_id == "sha":
            lines.append("• Macie jasne zasady podziału equity i rozwiązywania sporów")
            lines.append("• Inwestorzy traktują to jako minimum higieny prawnej")
        elif action_id == "mvp":
            if after.get("mvp_progress", 0) >= 100:
                lines.append("• MVP ukończone: możesz realnie testować sprzedaż")
                lines.append("• Teraz priorytetem są płacący klienci (PMF)")
            else:
                remaining = 100 - after.get("mvp_progress", 0)
                lines.append(f"• MVP jeszcze niegotowe: brakuje ~{remaining}%")
                lines.append("• Im szybciej wyjdziesz na rynek, tym szybciej dostaniesz feedback")
        elif action_id == "customers":
            lines.append("• Klienci płacący = walidacja + MRR")
            if after.get("customers", 0) >= 10:
                lines.append("• Masz 10+ klientów: solidna baza do rozmów z inwestorami")
        elif action_id == "investor":
            if after.get("cash", 0) > before.get("cash", 0):
                lines.append("• Pozyskałeś kapitał, ale Twoje equity się rozwodniło")
                lines.append("• Teraz kluczowe jest dostarczać wzrost zgodnie z oczekiwaniami")
            else:
                lines.append("• Proces fundraisingu trwa miesiącami; przygotuj pipeline i deck")
        elif action_id == "hire":
            lines.append("• Zespół rośnie, ale rośnie też burn (sprawdź runway)")
            if after.get("runway", 0) < 6:
                lines.append("• Uwaga: runway poniżej 6 mies to ryzyko operacyjne")
        elif action_id == "pivot":
            lines.append("• Pivot to koszt (utrata części pracy), ale szansa na lepszy PMF")
            lines.append("• Upewnij się, że pivot wynika z danych, nie z frustracji")
        elif action_id == "invite_partner":
            lines.append("• Masz teraz co-foundera – dzielicie odpowiedzialność")
            lines.append("• KRYTYCZNE: Podpiszcie SHA, zanim pojawią się konflikty!")
            lines.append("• Wspólnik komplementuje Twoje kompetencje")

        return lines

    def _invite_partner(self) -> Tuple[bool, str, Dict]:
        """Add a co-founder to the company with default values."""
        c = self.game_state.company

        has_partner = any((not f.is_player) and (not getattr(f, 'left_company', False)) for f in c.founders)
        if has_partner:
            return False, "Masz już wspólnika.", {}

        player = next((f for f in c.founders if f.is_player), None)
        if not player:
            return False, "Brak gracza w spółce.", {}

        partner_equity = 20.0
        partner_role = "business" if player.role == "technical" else "technical"

        partner = Founder(
            name="Partner",
            role=partner_role,
            equity_percentage=partner_equity,
            initial_investment=0.0,
            personal_invested=0.0,
            is_player=False,
        )
        c.founders.append(partner)

        player.equity_percentage = max(0.0, player.equity_percentage - partner_equity)

        self.app.config.has_partner = True
        self.app.config.partner_name = partner.name
        self.app.config.partner_equity = partner.equity_percentage
        self.app.config.player_equity = player.equity_percentage

        msg = f"Dodano wspólnika ({partner_equity:.0f}%)"
        if not self.game_state.agreement_signed:
            msg += " Teraz podpisz SHA!"

        return True, msg, {'equity_change': -partner_equity}
    
    def _log_action(self, name: str, effect: str) -> None:
        short_name = name[:35]
        short_effect = _shorten_text(effect, 30)
        self.action_history.append({
            'month': self.game_state.current_month,
            'name': short_name,
            'effect': short_effect
        })
    
    def action_next_month(self) -> None:
        if not self.game_state:
            return

        warnings = self._check_warnings_before_month()
        if warnings:
            self.app.push_screen(WarningsModal(warnings), self._on_month_warnings_result)
            return

        self._advance_month()
    
    def _random_event(self) -> None:
        c = self.game_state.company
        month = self.game_state.current_month
        
        events = [
            ('positive', '🚀 Viral marketing!', 'Twój post stał się viralowy!', lambda: (setattr(c, 'mrr', int(c.mrr * 1.2)), 'MRR +20%')[1]),
            ('positive', '🏆 Nagroda branżowa', 'Wygrałeś konkurs startupowy!', lambda: (setattr(c, 'cash_on_hand', c.cash_on_hand + 15000), '+15000 PLN')[1]),
            ('positive', '🤝 Strategiczny partner', 'Duża firma chce współpracować.', lambda: (setattr(c, 'mrr', c.mrr + 2000), 'MRR +2000 PLN')[1]),
            ('negative', '💸 Konkurent z funding', 'Konkurent dostał rundę i obniża ceny.', lambda: (setattr(c, 'mrr', int(c.mrr * 0.9)), 'MRR -10%')[1]),
            ('negative', '🔧 Awaria techniczna', 'Poważny bug wymagał naprawy.', lambda: (setattr(c, 'cash_on_hand', c.cash_on_hand - 3000), '-3000 PLN')[1]),
            ('negative', '😤 Klient rezygnuje', 'Duży klient odszedł do konkurencji.', lambda: self._apply_churn()),
        ]
        
        # Zdarzenia kontekstowe
        if _has_partner_shared(self.game_state, self.app.config) and not self.game_state.agreement_signed and month > 3:
            events.append(
                ('negative', '⚔️ Konflikt z partnerem!', 'Spór o podział obowiązków i equity!', lambda: 'Podpisz SHA aby uniknąć!')
            )

        # Zdarzenia związane z vestingiem
        if _has_partner_shared(self.game_state, self.app.config) and self.game_state.agreement_signed:
            partner = next((f for f in c.founders if not f.is_player and not f.left_company), None)
            if partner:
                vesting = self.game_state.founders_agreement.vesting_schedule
                if partner.months_in_company == vesting.cliff_months - 1:
                    events.append(
                        ('neutral', '📅 Cliff za miesiąc', f'{partner.name} osiągnie cliff w następnym miesiącu.', lambda: f'{vesting.cliff_percentage}% vested')
                    )
                elif partner.months_in_company == vesting.cliff_months:
                    events.append(
                        ('positive', '🎉 Cliff ukończony!', f'{partner.name} osiągnął cliff.', lambda: f'{vesting.cliff_percentage}% equity vested')
                    )
                elif partner.months_in_company > 6 and random.random() < 0.15:
                    events.append(
                        ('negative', '😤 Partner niezadowolony', f'{partner.name} rozważa odejście.', lambda: f'Vested: {partner.vested_percentage:.0f}%')
                    )
        
        event = random.choice(events)
        effect = event[3]()
        self._log_action(f"⚡ {event[1]}", effect or event[0])
        
        # Pokaż modal
        self.app.push_screen(EventModal(event[0], event[1], event[2], effect or ""))
    
    def _apply_churn(self) -> str:
        c = self.game_state.company
        if c.paying_customers > 0:
            lost = min(2, c.paying_customers)
            avg = c.mrr / c.paying_customers if c.paying_customers else 0
            c.paying_customers -= lost
            c.total_customers -= lost
            c.mrr -= lost * avg
            return f"-{lost} klientów"
        return "Brak klientów do stracenia"
    
    def action_status(self) -> None:
        self._update_status()
    
    def action_finanse(self) -> None:
        self.app.push_screen(FinanceScreen(self.game_state))

    def action_progress(self) -> None:
        self.app.push_screen(ProgressScreen(self.game_state, self.app.config))

    def action_mentor(self) -> None:
        self.app.mentor_mode = not getattr(self.app, "mentor_mode", True)
        self._update_display()

    def action_report(self) -> None:
        self.app.push_screen(MonthlyReportScreen(self.game_state, self.app.config))
    
    def action_equity(self) -> None:
        self.app.push_screen(EquityScreen(self.game_state))
    
    def action_historia(self) -> None:
        self.app.push_screen(HistoryScreen(self.action_history, self.game_state, self.app.config))
    
    def action_show_risk(self) -> None:
        self.app.push_screen(RiskModal(self.game_state, self.app.config))
    
    def action_glossary(self) -> None:
        self.app.push_screen(GlossaryScreen())
    
    def action_portfele(self) -> None:
        self.app.push_screen(PortfeleScreen(self.game_state, self.app.config))
    
    def action_quit_game(self) -> None:
        self.app.pop_screen()

    def action_save_game(self) -> None:
        if not self.game_state or not yaml:
            self.app.push_screen(EventModal("negative", "Błąd", "Zapis niedostępny (brak modułu yaml)", ""))
            return
        save_dir = Path.home() / ".biznes_saves"
        save_dir.mkdir(exist_ok=True)
        name = f"tui_save_{datetime.now().strftime('%Y%m%d_%H%M')}"
        path = save_dir / f"{name}.yaml"

        data = {
            'player_name': self.app.config.player_name,
            'player_role': self.app.config.player_role,
            'has_partner': self.app.config.has_partner,
            'partner_name': self.app.config.partner_name,
            'player_equity': self.app.config.player_equity,
            'partner_equity': self.app.config.partner_equity,
            'esop_pool': self.app.config.esop_pool,
            'legal_form': self.app.config.legal_form,
            'month': self.game_state.current_month,
            'cash': self.game_state.company.cash_on_hand,
            'mrr': self.game_state.company.mrr,
            'burn': self.game_state.company.monthly_burn_rate,
            'customers': self.game_state.company.paying_customers,
            'registered': self.game_state.company.registered,
            'mvp_completed': self.game_state.company.mvp_completed,
            'agreement_signed': self.game_state.agreement_signed,
            'mvp_progress': self.game_state.mvp_progress,
            'revenue_advance_months': getattr(self.game_state, 'revenue_advance_months', 0),
            'revenue_advance_mrr': getattr(self.game_state, 'revenue_advance_mrr', 0.0),
            'founders': [
                {
                    'name': f.name, 'role': f.role,
                    'equity_percentage': f.equity_percentage,
                    'vested_percentage': f.vested_percentage,
                    'months_in_company': f.months_in_company,
                    'cliff_completed': f.cliff_completed,
                    'personal_invested': f.personal_invested,
                    'is_player': f.is_player,
                }
                for f in self.game_state.company.founders
            ],
        }
        with open(path, 'w') as f:
            yaml.dump(data, f)
        self.app.push_screen(EventModal("positive", "✅ Zapisano", f"Gra zapisana jako: {name}", str(path)))

    def action_load_game(self) -> None:
        if not yaml:
            self.app.push_screen(EventModal("negative", "Błąd", "Wczytywanie niedostępne (brak modułu yaml)", ""))
            return
        self.app.push_screen(SaveLoadScreen(), self._on_load_result)

    def _on_load_result(self, save_data: Optional[Dict]) -> None:
        if not save_data:
            return
        self._restore_from_save(save_data)
        self._update_display()

    def _restore_from_save(self, data: Dict) -> None:
        self.app.config.player_name = data.get('player_name', 'Founder')
        self.app.config.player_role = data.get('player_role', 'technical')
        self.app.config.has_partner = data.get('has_partner', False)
        self.app.config.partner_name = data.get('partner_name', '')
        self.app.config.player_equity = data.get('player_equity', 50)
        self.app.config.partner_equity = data.get('partner_equity', 40)
        self.app.config.esop_pool = data.get('esop_pool', 10)
        self.app.config.legal_form = data.get('legal_form', 'psa')
        self.app.config.initial_cash = data.get('cash', 10000)
        self.app.config.monthly_burn = data.get('burn', 5000)

        self._initialize_game()

        self.game_state.current_month = data.get('month', 0)
        self.game_state.company.cash_on_hand = data.get('cash', 10000)
        self.game_state.company.mrr = data.get('mrr', 0)
        self.game_state.company.paying_customers = data.get('customers', 0)
        self.game_state.company.total_customers = data.get('customers', 0)
        self.game_state.company.registered = data.get('registered', False)
        self.game_state.company.mvp_completed = data.get('mvp_completed', False)
        self.game_state.agreement_signed = data.get('agreement_signed', False)
        self.game_state.mvp_progress = data.get('mvp_progress', 0)
        self.game_state.revenue_advance_months = int(data.get('revenue_advance_months', 0) or 0)
        self.game_state.revenue_advance_mrr = float(data.get('revenue_advance_mrr', 0.0) or 0.0)

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
                    is_player=bool(fdata.get('is_player', False)),
                ))
            if restored:
                if not any(f.is_player for f in restored):
                    restored[0].is_player = True
                self.game_state.company.founders = restored
                self.app.config.has_partner = any((not f.is_player) for f in restored)


class SaveLoadScreen(ModalScreen[Optional[Dict]]):
    """Ekran wyboru zapisu do wczytania"""

    BINDINGS = [Binding("escape", "cancel", "Anuluj")]

    def compose(self) -> ComposeResult:
        save_dir = Path.home() / ".biznes_saves"
        saves = []
        if save_dir.exists() and yaml:
            for f in sorted(save_dir.glob("*.yaml"), reverse=True)[:10]:
                try:
                    with open(f) as file:
                        data = yaml.safe_load(file) or {}
                    saves.append({'name': f.stem, 'path': f, 'data': data})
                except Exception:
                    pass

        items = []
        if saves:
            for i, s in enumerate(saves):
                month = s['data'].get('month', '?')
                cash = s['data'].get('cash', 0)
                items.append(
                    ListItem(Label(f"{s['name']} (mies. {month}, {cash:,.0f} PLN)"), id=f"save-{i}")
                )
        else:
            items.append(ListItem(Label("Brak zapisów"), id="save-none"))

        self._saves = saves
        yield Container(
            Static("💾 WCZYTAJ GRĘ", classes="modal-title"),
            Rule(),
            ListView(*items, id="saves-list"),
            Rule(),
            Button("Anuluj", id="cancel"),
            classes="save-load-modal",
        )

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item_id = event.item.id or ""
        if item_id.startswith("save-") and item_id != "save-none":
            idx = int(item_id.split("-")[1])
            if idx < len(self._saves):
                self.dismiss(self._saves[idx]['data'])
                return
        self.dismiss(None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)


class FinanceScreen(Screen):
    """Ekran finansów"""
    
    BINDINGS = [Binding("escape", "back", "Wróć")]
    
    def __init__(self, game_state: GameState):
        super().__init__()
        self.game_state = game_state
    
    def compose(self) -> ComposeResult:
        yield Header()
        c = self.game_state.company
        yield Container(
            Static("💰 FINANSE", classes="screen-title"),
            Rule(),
            Static(f"MRR: {c.mrr:,.0f} PLN"),
            Static(f"ARR: {c.mrr * 12:,.0f} PLN"),
            Static(f"Burn rate: {c.monthly_burn_rate:,.0f} PLN/mies"),
            Static(f"Gotówka: {c.cash_on_hand:,.0f} PLN"),
            Static(f"Runway: {_pluralize_months(c.runway_months())}"),
            Static(f"Wycena: {c.current_valuation:,.0f} PLN"),
            Rule(),
            Button("← Wróć", id="back"),
            classes="info-box"
        )
        yield Footer()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.app.pop_screen()
    
    def action_back(self) -> None:
        self.app.pop_screen()


class MonthlyReportScreen(Screen):
    """Ekran raportu miesięcznego"""

    BINDINGS = [Binding("escape", "back", "Wróć")]

    def __init__(self, game_state: GameState, config: PlayerConfig):
        super().__init__()
        self.game_state = game_state
        self.config = config

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("📋 RAPORT MIESIĘCZNY", classes="screen-title"),
            Rule(),
            ScrollableContainer(id="report-content"),
            Rule(),
            Button("← Wróć", id="back"),
            classes="glossary-box",
        )
        yield Footer()

    def on_mount(self) -> None:
        set_game_subtitle(self.app, self.game_state, self.config)

        c = self.game_state.company
        month = self.game_state.current_month
        profit = c.mrr - c.monthly_burn_rate
        runway = c.runway_months()
        risk_bar = get_risk_indicators(self.game_state, self.config)

        content = self.query_one("#report-content", ScrollableContainer)
        content.remove_children()

        content.mount(Static(f"[bold]Miesiąc {month}[/bold]"))
        content.mount(Static(""))
        content.mount(Static(f"[bold]💰 Gotówka:[/bold] {c.cash_on_hand:,.0f} PLN"))
        content.mount(Static(f"[bold]📈 MRR:[/bold] {c.mrr:,.0f} PLN"))
        content.mount(Static(f"[bold]🔥 Burn:[/bold] {c.monthly_burn_rate:,.0f} PLN/mies"))
        content.mount(Static(f"[bold]👥 Klienci:[/bold] {c.paying_customers}"))
        content.mount(Static(f"[bold]⏱️ Runway:[/bold] {_pluralize_months(runway)}"))
        content.mount(Static(""))

        color = "green" if profit >= 0 else "red"
        content.mount(Static(f"[bold]💹 Wynik miesiąca:[/bold] [{color}]{profit:+,.0f} PLN[/{color}]"))
        content.mount(Static(""))
        content.mount(Static(f"[bold]⚠️ Ryzyka:[/bold] {risk_bar}"))
        content.mount(Static(""))

        prio_action, prio_why, prio_consequence = self._get_priority_action_local()
        content.mount(Static("[bold yellow]🎯 PRIORYTET NA KOLEJNY MIESIĄC[/bold yellow]"))
        content.mount(Static(f"[bold]{prio_action}[/bold]"))
        content.mount(Static(f"[dim]{prio_why}[/dim]"))
        if prio_consequence:
            content.mount(Static(f"[red]{prio_consequence}[/red]"))

    def _get_priority_action_local(self) -> Tuple[str, str, str]:
        return _get_priority_action_shared(self.game_state, self.config)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.app.pop_screen()

    def action_back(self) -> None:
        self.app.pop_screen()


class ProgressScreen(Screen):
    """Ekran postępu vs cele"""

    BINDINGS = [Binding("escape", "back", "Wróć")]

    def __init__(self, game_state: GameState, config: PlayerConfig):
        super().__init__()
        self.game_state = game_state
        self.config = config

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("🎯 POSTĘP VS CELE (12 mies.)", classes="screen-title"),
            Rule(),
            Container(id="progress-content", classes="progress-box"),
            Rule(),
            Button("← Wróć", id="back"),
            classes="info-box",
        )
        yield Footer()

    def on_mount(self) -> None:
        set_game_subtitle(self.app, self.game_state, self.config)

        c = self.game_state.company
        month = min(12, self.game_state.current_month)
        target_mrr = getattr(self.config, "target_mrr_12_months", 0) or 0
        target_customers = getattr(self.config, "target_customers_12_months", 0) or 0

        expected_mrr = (target_mrr / 12) * month if target_mrr else 0
        expected_customers = (target_customers / 12) * month if target_customers else 0

        mrr_status = "🟢" if c.mrr >= expected_mrr else "🟡" if c.mrr >= expected_mrr * 0.5 else "🔴"
        cust_status = "🟢" if c.paying_customers >= expected_customers else "🟡" if c.paying_customers >= expected_customers * 0.5 else "🔴"

        mrr_pct = min(100.0, (c.mrr / target_mrr) * 100.0) if target_mrr else 0.0
        cust_pct = min(100.0, (c.paying_customers / target_customers) * 100.0) if target_customers else 0.0

        content = self.query_one("#progress-content", Container)
        content.remove_children()

        content.mount(Static("[bold]Tabela[/bold]"))
        content.mount(Static("| Metryka | Teraz | Oczekiwane | Cel | Status |"))
        content.mount(Static("|---------|------:|----------:|----:|:------:|"))
        content.mount(Static(f"| MRR | {c.mrr:,.0f} | {expected_mrr:,.0f} | {target_mrr:,.0f} | {mrr_status} |"))
        content.mount(Static(f"| Klienci | {c.paying_customers} | {expected_customers:.0f} | {target_customers} | {cust_status} |"))

        content.mount(Static(""))
        content.mount(Static(f"[bold]📈 MRR[/bold] {mrr_pct:.0f}%"))
        bar_mrr = ProgressBar(total=100)
        bar_mrr.progress = int(mrr_pct)
        content.mount(bar_mrr)

        content.mount(Static(""))
        content.mount(Static(f"[bold]👥 Klienci[/bold] {cust_pct:.0f}%"))
        bar_cust = ProgressBar(total=100)
        bar_cust.progress = int(cust_pct)
        content.mount(bar_cust)

        if month > 0 and c.mrr > 0:
            projected_mrr_12 = (c.mrr / month) * 12
            content.mount(Static(""))
            if projected_mrr_12 >= target_mrr:
                content.mount(Static(f"[green]📊 Prognoza MRR w mies. 12: {projected_mrr_12:,.0f} PLN (cel osiągalny!)[/green]"))
            else:
                missing = target_mrr - projected_mrr_12
                content.mount(Static(f"[yellow]📊 Prognoza MRR w mies. 12: {projected_mrr_12:,.0f} PLN (brakuje {missing:,.0f} PLN)[/yellow]"))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.app.pop_screen()

    def action_back(self) -> None:
        self.app.pop_screen()


class PortfeleScreen(Screen):
    """Ekran portfeli wspólników i biznesu"""
    
    BINDINGS = [Binding("escape", "back", "Wróć")]
    
    def __init__(self, game_state: GameState, config):
        super().__init__()
        self.game_state = game_state
        self.config = config
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("💼 PRZEJRZYSTOŚĆ FINANSOWA", classes="screen-title"),
            Rule(),
            ScrollableContainer(id="portfele-content"),
            Button("← Wróć", id="back"),
            classes="glossary-box"
        )
        yield Footer()
    
    def on_mount(self) -> None:
        set_game_subtitle(self.app, self.game_state, self.app.config)
        content = self.query_one("#portfele-content")
        c = self.game_state.company
        
        # Portfele wspólników
        content.mount(Static("[bold cyan]┌─ PORTFELE WSPÓLNIKÓW ─────────────────┐[/bold cyan]"))
        
        for f in c.founders:
            verified = "✓" if f.krs_verified and f.debtor_registry_verified else "⚠️"
            content.mount(Static(f"\n[bold]👤 {f.name} {verified}[/bold]"))
            content.mount(Static(f"   Equity: {f.equity_percentage:.0f}% (vested: {f.vested_percentage:.1f}%)"))
            content.mount(Static(f"   Zainwestowane: {f.personal_invested:,.0f} PLN"))
            content.mount(Static(f"   Otrzymane: {f.total_received:,.0f} PLN"))
            
            # Wkłady
            contributions = []
            if f.mvp_value > 0:
                contributions.append(f"MVP: {f.mvp_value:,.0f} PLN")
            if f.contacts_count > 0:
                contributions.append(f"Kontakty: {f.contacts_count}")
            if f.experience_years > 0:
                contributions.append(f"Doświadczenie: {f.experience_years} lat")
            if contributions:
                content.mount(Static(f"   Wkłady: {', '.join(contributions)}"))
            
            balance = f.total_received - f.personal_invested
            color = "green" if balance >= 0 else "red"
            content.mount(Static(f"   Bilans: [{color}]{balance:+,.0f} PLN[/{color}]"))
        
        content.mount(Static("\n[bold cyan]└──────────────────────────────────────┘[/bold cyan]"))
        
        # Finanse biznesu
        content.mount(Static("\n[bold cyan]┌─ FINANSE BIZNESU ─────────────────────┐[/bold cyan]"))
        content.mount(Static(f"\n💰 STAN KONTA FIRMOWEGO"))
        content.mount(Static(f"   Gotówka: {c.cash_on_hand:,.0f} PLN"))
        content.mount(Static(f"   MRR: {c.mrr:,.0f} PLN"))
        content.mount(Static(f"   Burn rate: {c.monthly_burn_rate:,.0f} PLN/mies"))
        content.mount(Static(f"   Runway: {c.runway_months()} mies"))
        
        # P&L
        profit = c.mrr - c.monthly_burn_rate
        color = "green" if profit >= 0 else "red"
        content.mount(Static(f"\n[bold]📊 MIESIĘCZNY P&L[/bold]"))
        content.mount(Static(f"   [green]Przychody (MRR):[/green] {c.mrr:,.0f} PLN"))
        content.mount(Static(f"   [red]Koszty (burn):[/red] {c.monthly_burn_rate:,.0f} PLN"))
        content.mount(Static(f"   [{color}]WYNIK: {profit:+,.0f} PLN[/{color}]"))
        
        # Podział zysków
        if profit > 0 and len(c.founders) > 1:
            content.mount(Static(f"\n[bold]📈 POTENCJALNY PODZIAŁ ZYSKÓW[/bold]"))
            for f in c.founders:
                share = profit * (f.equity_percentage / 100)
                content.mount(Static(f"   {f.name} ({f.equity_percentage:.0f}%): {share:,.0f} PLN/mies"))
        
        content.mount(Static("\n[bold cyan]└──────────────────────────────────────┘[/bold cyan]"))
        
        if not self.game_state.agreement_signed and len(c.founders) > 1:
            content.mount(Static("\n[bold red]⚠️ Bez SHA podział może być sporny![/bold red]"))
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.app.pop_screen()
    
    def action_back(self) -> None:
        self.app.pop_screen()


class EquityScreen(Screen):
    """Ekran cap table"""
    
    BINDINGS = [Binding("escape", "back", "Wróć")]
    
    def __init__(self, game_state: GameState):
        super().__init__()
        self.game_state = game_state
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("📊 CAP TABLE", classes="screen-title"),
            Rule(),
            id="equity-content",
            classes="info-box"
        )
        yield Footer()
    
    def on_mount(self) -> None:
        set_game_subtitle(self.app, self.game_state, self.app.config)
        content = self.query_one("#equity-content")
        for f in self.game_state.company.founders:
            status = "✓ cliff" if f.cliff_completed else f"{f.months_in_company}/12 mies"
            content.mount(Static(f"{f.name}: {f.equity_percentage:.0f}% (vested: {f.vested_percentage:.1f}%) [{status}]"))
        content.mount(Static(f"ESOP: {self.game_state.company.esop_pool_percentage}%"))
        content.mount(Rule())
        content.mount(Button("← Wróć", id="back"))
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.app.pop_screen()
    
    def action_back(self) -> None:
        self.app.pop_screen()


class HistoryScreen(Screen):
    """Ekran historii"""
    
    BINDINGS = [Binding("escape", "back", "Wróć")]
    
    def __init__(self, history: List[Dict], game_state: GameState, config: PlayerConfig):
        super().__init__()
        self.history = history
        self.game_state = game_state
        self.config = config
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("📜 HISTORIA", classes="screen-title"),
            Rule(),
            ScrollableContainer(id="history-content"),
            Button("← Wróć", id="back"),
            classes="info-box"
        )
        yield Footer()
    
    def on_mount(self) -> None:
        set_game_subtitle(self.app, self.game_state, self.config)
        content = self.query_one("#history-content")
        if not self.history:
            content.mount(Static("Brak historii"))
        else:
            current_month = -1
            for entry in self.history[-20:]:
                if entry['month'] != current_month:
                    current_month = entry['month']
                    content.mount(Static(f"\n[bold cyan]Miesiąc {current_month}[/bold cyan]"))

                name = _shorten_text(str(entry.get('name', '')), 50)
                effect = _shorten_text(str(entry.get('effect', '')), 70)
                color = "yellow" if str(entry.get('name', '')).startswith("⚡") else "green"
                content.mount(Static(f"  [{color}]{name}[/{color}] [dim]→ {effect}[/dim]"))

        content.mount(Rule())
        self._mount_history_analysis(content)

    def _mount_history_analysis(self, content: ScrollableContainer) -> None:
        actions = [e for e in self.history if isinstance(e, dict) and e.get("name") and not str(e.get("name")).startswith("⚡")]
        events = [e for e in self.history if isinstance(e, dict) and str(e.get("name", "")).startswith("⚡")]

        good: List[Tuple[str, str]] = []
        bad: List[Tuple[str, str]] = []

        for entry in actions:
            name = str(entry.get("name", ""))
            effect = str(entry.get("effect", ""))
            blob = f"{name} {effect}".lower()

            if "sha" in blob:
                good.append(("Podpisanie SHA", "Zmniejsza ryzyko konfliktów i blokady decyzyjnej"))
            if "spółka" in blob and "zarejestrow" in blob:
                good.append(("Rejestracja spółki", "Ochrona prawna + większa wiarygodność"))
            if "mvp" in blob and "ukończ" in blob:
                good.append(("Ukończenie MVP", "Możesz realnie walidować sprzedaż"))

        for entry in events:
            name = str(entry.get("name", ""))
            if "konflikt" in name.lower() and _has_partner_shared(self.game_state, self.config) and not self.game_state.agreement_signed:
                bad.append(("Konflikt bez SHA", "Wysokie ryzyko sporów founderów – podpisz SHA wcześniej"))

        content.mount(Static("[bold]📚 ANALIZA DECYZJI[/bold]"))

        if good:
            content.mount(Static("\n[bold green]✅ DOBRE DECYZJE[/bold green]"))
            for title, why in good[:6]:
                content.mount(Static(f"  • [green]{title}[/green] — {why}"))

        if bad:
            content.mount(Static("\n[bold red]❌ BŁĘDY DO UNIKNIĘCIA[/bold red]"))
            for title, lesson in bad[:6]:
                content.mount(Static(f"  • [red]{title}[/red] — {lesson}"))

        content.mount(Static("\n[bold]📊 STATYSTYKI[/bold]"))
        content.mount(Static(f"  • Akcje: {len(actions)}"))
        content.mount(Static(f"  • Zdarzenia losowe: {len(events)}"))
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.app.pop_screen()
    
    def action_back(self) -> None:
        self.app.pop_screen()


class GlossaryScreen(Screen):
    """Ekran słownika pojęć"""
    
    BINDINGS = [Binding("escape", "back", "Wróć")]
    
    TERMS = {
        "MRR": "Monthly Recurring Revenue - miesięczny przychód powtarzalny",
        "ARR": "Annual Recurring Revenue - roczny przychód powtarzalny (MRR × 12)",
        "Runway": "Ile miesięcy firma może działać przy obecnym burn rate",
        "Burn rate": "Miesięczne koszty operacyjne firmy",
        "Vesting": "Stopniowe nabywanie udziałów w czasie (zwykle 48 mies)",
        "Cliff": "Okres próbny przed vestingiem (zwykle 12 mies, 25%)",
        "SHA": "Shareholders Agreement - umowa wspólników",
        "Cap table": "Tabela kapitalizacji - kto ile ma udziałów",
        "ESOP": "Employee Stock Option Pool - pula opcji dla pracowników",
        "Good leaver": "Odejście w dobrych okolicznościach - zachowuje vested",
        "Bad leaver": "Odejście w złych okolicznościach - traci wszystko/większość",
        "Tag-along": "Prawo mniejszościowego do dołączenia do sprzedaży",
        "Drag-along": "Prawo większościowego do zmuszenia do sprzedaży",
        "PMF": "Product-Market Fit - dopasowanie produktu do rynku",
        "PSA": "Prosta Spółka Akcyjna - nowa forma prawna dla startupów",
        "Due diligence": "Audyt prawny/finansowy przed inwestycją",
    }
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("📚 SŁOWNIK POJĘĆ", classes="screen-title"),
            Rule(),
            ScrollableContainer(
                *[Static(f"[bold]{term}[/bold]: {desc}") for term, desc in self.TERMS.items()],
                id="glossary-content"
            ),
            Rule(),
            Button("← Wróć", id="back"),
            classes="glossary-box"
        )
        yield Footer()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.app.pop_screen()
    
    def action_back(self) -> None:
        self.app.pop_screen()


class HelpScreen(Screen):
    """Ekran pomocy"""
    
    BINDINGS = [Binding("escape", "back", "Wróć")]
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("❓ POMOC", classes="screen-title"),
            Rule(),
            Static("[bold]Nawigacja:[/bold]"),
            Static("  ↑↓ - wybór opcji"),
            Static("  Enter - zatwierdź"),
            Static("  Esc - wróć"),
            Static("  Tab - przełącz panele"),
            Static(""),
            Static("[bold]Skróty w grze:[/bold]"),
            Static("  M - następny miesiąc"),
            Static("  T - postęp vs cele"),
            Static("  R - analiza ryzyka"),
            Static("  K - mentor (włącz/wyłącz)"),
            Static("  O - raport miesięczny"),
            Static("  F - finanse"),
            Static("  E - equity/cap table"),
            Static("  G - słownik pojęć"),
            Static("  H - historia"),
            Static("  Q - wyjście"),
            Static(""),
            Static("[bold]Panel nawigacji (lewy):[/bold]"),
            Static("  Kliknij lub użyj strzałek do nawigacji"),
            Static(""),
            Static("[bold]Panel podglądu (prawy):[/bold]"),
            Static("  Pokazuje szczegóły wybranej akcji"),
            Static("  Ryzyka, korzyści, konsekwencje"),
            Rule(),
            Button("← Wróć", id="back"),
            classes="info-box"
        )
        yield Footer()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.app.pop_screen()
    
    def action_back(self) -> None:
        self.app.pop_screen()


class GameOverScreen(Screen):
    """Ekran końca gry"""
    
    BINDINGS = [Binding("enter", "restart", "Nowa gra"), Binding("q", "quit", "Wyjście")]
    
    def __init__(self, success: bool):
        super().__init__()
        self.success = success
    
    def compose(self) -> ComposeResult:
        yield Header()
        if self.success:
            yield Container(
                Static("🎉 SUKCES!", classes="title"),
                Static("Osiągnąłeś cele biznesowe!", classes="subtitle"),
                Rule(),
                Button("▶ Nowa gra", id="restart", variant="primary"),
                Button("✕ Wyjście", id="quit"),
                classes="gameover-box"
            )
        else:
            yield Container(
                Static("💀 GAME OVER", classes="title-fail"),
                Static("Skończyła Ci się gotówka.", classes="subtitle"),
                Rule(),
                Static("[bold]Wnioski:[/bold]"),
                Static("  • Pilnuj runway (min 6 miesięcy)"),
                Static("  • Szukaj klientów ASAP"),
                Static("  • Podpisz SHA z partnerem"),
                Rule(),
                Button("▶ Spróbuj ponownie", id="restart", variant="primary"),
                Button("✕ Wyjście", id="quit"),
                classes="gameover-box"
            )
        yield Footer()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "restart":
            self.app.pop_screen()
            self.app.pop_screen()
            self.app.push_screen(SetupScreen())
        else:
            self.app.exit()
    
    def action_restart(self) -> None:
        self.app.pop_screen()
        self.app.pop_screen()
        self.app.push_screen(SetupScreen())
    
    def action_quit(self) -> None:
        self.app.exit()


# ============================================================================
# GŁÓWNA APLIKACJA
# ============================================================================

class BiznesApp(App):
    """Główna aplikacja Textual"""
    
    CSS = """
    .title { text-align: center; text-style: bold; color: $primary; padding: 1; }
    .title-fail { text-align: center; text-style: bold; color: $error; padding: 1; }
    .subtitle { text-align: center; color: $text-muted; }
    .desc { text-align: center; padding: 1; }
    .screen-title { text-style: bold; color: $primary; }
    .step-title { text-style: bold; color: $secondary; padding-bottom: 1; }
    .hint { color: $text-muted; }
    .panel-title { text-style: bold; background: $primary; color: $background; padding: 0 1; }
    .status-content { padding: 1; }
    .actions-info { text-align: center; color: $warning; padding: 1; }
    .learn-header { text-style: bold; }
    .preview-content { padding: 1; }
    
    .welcome-box { align: center middle; width: 50; height: auto; border: solid $primary; padding: 2; }
    .setup-box { align: center middle; width: 60; height: auto; border: solid $secondary; padding: 2; }
    .info-box { align: center middle; width: 60; height: auto; border: solid $primary; padding: 2; }
    .gameover-box { align: center middle; width: 50; height: auto; border: solid $error; padding: 2; }
    .glossary-box { align: center middle; width: 70; height: 80%; border: solid $primary; padding: 2; }
    
    .game-layout { height: 100%; }
    .left-panel { width: 25%; border-right: solid $primary; }
    .center-panel { width: 40%; border-right: solid $secondary; }
    .right-panel { width: 35%; }
    
    #actions-container { height: 1fr; }
    #preview-container { height: 1fr; }
    #glossary-content { height: 1fr; }
    #nav-tree { height: auto; max-height: 10; }
    
    /* Event modal */
    .event-modal { align: center middle; width: 50; height: auto; border: double $warning; padding: 2; background: $surface; }
    .modal-title { text-style: bold; text-align: center; }
    .modal-hint { text-align: center; color: $text-muted; }
    .event-positive { color: $success; text-style: bold; }
    .event-negative { color: $error; text-style: bold; }
    .event-desc { color: $text; padding: 1 0; }
    .event-effect { color: $warning; }
    
    /* Risk modal */
    .risk-modal { align: center middle; width: 55; height: auto; border: solid $error; padding: 2; background: $surface; }
    .risk-low { color: $success; text-style: bold; }
    .risk-medium { color: $warning; text-style: bold; }
    .risk-high { color: $error; text-style: bold; }

    .warnings-modal { align: center middle; width: 70; height: auto; border: double $warning; padding: 2; background: $surface; }
    .warnings-actions { align: center middle; height: auto; }

    .action-result-modal { align: center middle; width: 78; height: auto; border: double $success; padding: 2; background: $surface; }
    .save-load-modal { align: center middle; width: 70; height: auto; border: solid $primary; padding: 2; background: $surface; }
    .mode-selection-modal { align: center middle; width: 80; height: auto; border: double $warning; padding: 2; background: $surface; }
    .mode-info { color: $text-muted; text-align: center; }
    .action-title { text-style: bold; }
    .action-message { color: $text; }
    .section-title { text-style: bold; color: $primary; }
    .change-line { color: $text; }
    .meaning-line { color: $text; }
    .next-priority { text-style: bold; color: $success; }
    .progress-box { width: 100%; height: auto; }
    
    Button { margin: 1 0; }
    ListView { height: auto; max-height: 12; }
    Tree { height: auto; }
    """
    
    TITLE = "BIZNES - Symulator Startupu"
    
    def __init__(self):
        super().__init__()
        self.config: Optional[PlayerConfig] = None
        self.mentor_mode: bool = True
    
    def on_mount(self) -> None:
        self.push_screen(WelcomeScreen())


def main():
    """Punkt wejścia dla TUI"""
    app = BiznesApp()
    app.run()


if __name__ == "__main__":
    main()
