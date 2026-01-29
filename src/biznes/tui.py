"""
Biznes - Interaktywny interfejs TUI (Textual)
Wersja z nawigacją strzałkami i minimalnym pisaniem
"""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header, Footer, Static, Button, Label, 
    ListItem, ListView, ProgressBar, Rule
)
from textual.screen import Screen
from textual.message import Message
from typing import Optional, List, Dict
import random

from .core.models import (
    GameState, PlayerConfig, Company, Founder,
    LegalForm, FoundersAgreement
)


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


class GameScreen(Screen):
    """Główny ekran gry"""
    
    BINDINGS = [
        Binding("m", "next_month", "Następny miesiąc"),
        Binding("s", "status", "Status"),
        Binding("f", "finanse", "Finanse"),
        Binding("e", "equity", "Equity"),
        Binding("h", "historia", "Historia"),
        Binding("q", "quit_game", "Wyjście"),
    ]
    
    def __init__(self):
        super().__init__()
        self.game_state: Optional[GameState] = None
        self.action_history: List[Dict] = []
        self.actions_this_month = 0
        self.max_actions = 2
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Horizontal(
            # Lewa kolumna - status
            Vertical(
                Static("📊 STATUS", classes="panel-title"),
                Static(id="status-panel", classes="status-content"),
                classes="left-panel"
            ),
            # Prawa kolumna - akcje
            Vertical(
                Static("⚡ AKCJE", classes="panel-title"),
                ScrollableContainer(
                    ListView(id="actions-list"),
                    id="actions-container"
                ),
                Static(id="actions-remaining", classes="actions-info"),
                classes="right-panel"
            ),
            classes="game-layout"
        )
        yield Footer()
    
    def on_mount(self) -> None:
        self._initialize_game()
        self._update_display()
    
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
            is_player=True
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
    
    def _update_display(self) -> None:
        self._update_status()
        self._update_actions()
    
    def _update_status(self) -> None:
        if not self.game_state:
            return
        
        c = self.game_state.company
        month = self.game_state.current_month
        runway = c.runway_months()
        
        status_text = f"""
[bold]Miesiąc {month}[/bold]

💰 Gotówka: {c.cash_on_hand:,.0f} PLN
📈 MRR: {c.mrr:,.0f} PLN
👥 Klienci: {c.paying_customers}
⏱️ Runway: {runway} mies

🏢 Spółka: {'✓' if c.registered else '✗'}
📝 SHA: {'✓' if self.game_state.agreement_signed else '✗'}
🔧 MVP: {'✓' if c.mvp_completed else f'{self.game_state.mvp_progress}%'}
"""
        self.query_one("#status-panel", Static).update(status_text)
    
    def _update_actions(self) -> None:
        actions_list = self.query_one("#actions-list", ListView)
        actions_list.clear()
        
        actions = self._get_available_actions()
        
        for i, action in enumerate(actions):
            if action['available']:
                label = f"{'[ZALECANE] ' if action.get('recommended') else ''}{action['name']}"
                item = ListItem(Label(f"✓ {label}"), id=f"action-{i}")
            else:
                item = ListItem(Label(f"✗ {action['name']} - {action.get('blocked', '')}"), id=f"action-{i}")
                item.disabled = True
            actions_list.append(item)
        
        remaining = self.max_actions - self.actions_this_month
        self.query_one("#actions-remaining", Static).update(
            f"Pozostało akcji: {remaining}/{self.max_actions}"
        )
    
    def _get_available_actions(self) -> List[Dict]:
        c = self.game_state.company
        actions = []
        
        if not c.registered:
            actions.append({
                'id': 'register', 'name': '🏢 Załóż spółkę',
                'available': True, 'recommended': True,
                'cost': 2000
            })
        
        has_partner = len([f for f in c.founders if not f.is_player]) > 0
        if not self.game_state.agreement_signed:
            actions.append({
                'id': 'sha', 'name': '📝 Podpisz SHA',
                'available': has_partner,
                'blocked': 'Brak partnera' if not has_partner else '',
                'recommended': has_partner,
                'cost': 5000
            })
        
        if not c.mvp_completed:
            actions.append({
                'id': 'mvp', 'name': '🔧 Rozwijaj MVP',
                'available': True, 'recommended': True
            })
        
        if c.mvp_completed:
            actions.append({
                'id': 'customers', 'name': '🎯 Szukaj klientów',
                'available': True, 'recommended': c.paying_customers < 10
            })
        
        if c.registered and c.mrr > 0:
            actions.append({
                'id': 'investor', 'name': '💰 Szukaj inwestora',
                'available': self.game_state.agreement_signed,
                'blocked': 'Najpierw SHA' if not self.game_state.agreement_signed else ''
            })
        
        actions.append({
            'id': 'skip', 'name': '⏭️ Pomiń (następny miesiąc)',
            'available': True
        })
        
        return actions
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if self.actions_this_month >= self.max_actions:
            return
        
        item_id = event.item.id
        if not item_id or not item_id.startswith("action-"):
            return
        
        idx = int(item_id.split("-")[1])
        actions = self._get_available_actions()
        
        if idx < len(actions):
            action = actions[idx]
            if action['available']:
                self._execute_action(action)
    
    def _execute_action(self, action: Dict) -> None:
        c = self.game_state.company
        
        if action['id'] == 'skip':
            self.action_next_month()
            return
        
        if action['id'] == 'register':
            cost = action.get('cost', 2000)
            if c.cash_on_hand >= cost:
                c.cash_on_hand -= cost
                c.registered = True
                self._log_action(action['name'], f"-{cost} PLN")
        
        elif action['id'] == 'sha':
            cost = action.get('cost', 5000)
            if c.cash_on_hand >= cost:
                c.cash_on_hand -= cost
                self.game_state.agreement_signed = True
                self._log_action(action['name'], f"-{cost} PLN")
        
        elif action['id'] == 'mvp':
            progress = random.randint(20, 35)
            self.game_state.mvp_progress = min(100, self.game_state.mvp_progress + progress)
            if self.game_state.mvp_progress >= 100:
                c.mvp_completed = True
                self._log_action(action['name'], "MVP ukończone!")
            else:
                self._log_action(action['name'], f"+{progress}%")
        
        elif action['id'] == 'customers':
            new_customers = random.randint(1, 5)
            avg_mrr = random.randint(150, 350)
            c.total_customers += new_customers
            c.paying_customers += new_customers
            c.mrr += new_customers * avg_mrr
            self._log_action(action['name'], f"+{new_customers} klientów")
        
        elif action['id'] == 'investor':
            if random.random() < 0.3:
                amount = random.randint(200, 500) * 1000
                self._log_action(action['name'], f"Oferta: {amount:,} PLN!")
            else:
                self._log_action(action['name'], "Brak oferty")
        
        self.actions_this_month += 1
        self._update_display()
        
        if self.actions_this_month >= self.max_actions:
            self.action_next_month()
    
    def _log_action(self, name: str, effect: str) -> None:
        self.action_history.append({
            'month': self.game_state.current_month,
            'name': name,
            'effect': effect
        })
    
    def action_next_month(self) -> None:
        if not self.game_state:
            return
        
        self.game_state.current_month += 1
        self.actions_this_month = 0
        
        c = self.game_state.company
        
        # Burn
        net_burn = c.monthly_burn_rate - c.mrr
        c.cash_on_hand -= net_burn
        
        # Organic growth
        if c.paying_customers > 0:
            growth = random.uniform(0.02, 0.08)
            new_cust = max(1, int(c.paying_customers * growth))
            avg_rev = c.mrr / c.paying_customers if c.paying_customers else 200
            c.total_customers += new_cust
            c.paying_customers += new_cust
            c.mrr += new_cust * avg_rev
        
        # Random event (40% chance)
        if random.random() < 0.4:
            self._random_event()
        
        # Game over check
        if c.cash_on_hand < 0:
            self.app.push_screen(GameOverScreen(success=False))
        elif c.mrr >= self.app.config.target_mrr_12_months:
            self.app.push_screen(GameOverScreen(success=True))
        
        self._update_display()
    
    def _random_event(self) -> None:
        c = self.game_state.company
        events = [
            ('positive', '🚀 Viral!', lambda: setattr(c, 'mrr', int(c.mrr * 1.2))),
            ('positive', '🏆 Nagroda', lambda: setattr(c, 'cash_on_hand', c.cash_on_hand + 15000)),
            ('negative', '💸 Konkurent', lambda: setattr(c, 'mrr', int(c.mrr * 0.9))),
            ('negative', '🔧 Awaria', lambda: setattr(c, 'cash_on_hand', c.cash_on_hand - 3000)),
        ]
        event = random.choice(events)
        event[2]()
        self._log_action(f"⚡ {event[1]}", event[0])
    
    def action_status(self) -> None:
        self._update_status()
    
    def action_finanse(self) -> None:
        self.app.push_screen(FinanceScreen(self.game_state))
    
    def action_equity(self) -> None:
        self.app.push_screen(EquityScreen(self.game_state))
    
    def action_historia(self) -> None:
        self.app.push_screen(HistoryScreen(self.action_history))
    
    def action_quit_game(self) -> None:
        self.app.pop_screen()


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
            Static(f"Runway: {c.runway_months()} miesięcy"),
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
    
    def __init__(self, history: List[Dict]):
        super().__init__()
        self.history = history
    
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
        content = self.query_one("#history-content")
        if not self.history:
            content.mount(Static("Brak historii"))
        else:
            current_month = -1
            for entry in self.history[-20:]:
                if entry['month'] != current_month:
                    current_month = entry['month']
                    content.mount(Static(f"\n[bold]Miesiąc {current_month}[/bold]"))
                content.mount(Static(f"  {entry['name']} → {entry['effect']}"))
    
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
            Static(""),
            Static("[bold]Skróty w grze:[/bold]"),
            Static("  M - następny miesiąc"),
            Static("  S - status"),
            Static("  F - finanse"),
            Static("  E - equity/cap table"),
            Static("  H - historia"),
            Static("  Q - wyjście"),
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
    .hint { color: $text-muted; font-size: 80%; }
    .panel-title { text-style: bold; background: $primary; color: $background; padding: 0 1; }
    .status-content { padding: 1; }
    .actions-info { text-align: center; color: $warning; padding: 1; }
    .learn-header { text-style: bold; }
    
    .welcome-box { align: center middle; width: 50; height: auto; border: solid $primary; padding: 2; }
    .setup-box { align: center middle; width: 60; height: auto; border: solid $secondary; padding: 2; }
    .info-box { align: center middle; width: 50; height: auto; border: solid $primary; padding: 2; }
    .gameover-box { align: center middle; width: 50; height: auto; border: solid $error; padding: 2; }
    
    .game-layout { height: 100%; }
    .left-panel { width: 35%; border-right: solid $primary; }
    .right-panel { width: 65%; }
    
    #actions-container { height: 1fr; }
    
    Button { margin: 1 0; }
    ListView { height: auto; max-height: 15; }
    """
    
    TITLE = "BIZNES - Symulator Startupu"
    
    def __init__(self):
        super().__init__()
        self.config: Optional[PlayerConfig] = None
    
    def on_mount(self) -> None:
        self.push_screen(WelcomeScreen())


def main():
    """Punkt wejścia dla TUI"""
    app = BiznesApp()
    app.run()


if __name__ == "__main__":
    main()
