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
        
        if self.config.has_partner and not self.game_state.agreement_signed:
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
        Binding("r", "show_risk", "Ryzyko"),
        Binding("g", "glossary", "Słownik"),
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
        self.current_actions: List[Dict] = []
    
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
        info.add_leaf("📊 Equity", data="equity")
        info.add_leaf("📜 Historia", data="historia")
        info.expand()
        
        tools = tree.root.add("🛠️ Narzędzia")
        tools.add_leaf("⚠️ Ryzyko", data="risk")
        tools.add_leaf("📚 Słownik", data="glossary")
        tools.add_leaf("❓ Pomoc", data="help")
        tools.expand()
    
    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Obsługa nawigacji drzewem"""
        data = event.node.data
        if data == "finanse":
            self.action_finanse()
        elif data == "equity":
            self.action_equity()
        elif data == "historia":
            self.action_historia()
        elif data == "risk":
            self.action_show_risk()
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
        
        self.current_actions = self._get_available_actions()
        
        for i, action in enumerate(self.current_actions):
            if action['available']:
                rec = "⭐ " if action.get('recommended') else ""
                item = ListItem(Label(f"✓ {rec}{action['name']}"), id=f"action-{i}")
            else:
                item = ListItem(Label(f"✗ {action['name']}"), id=f"action-{i}")
                item.disabled = True
            actions_list.append(item)
        
        remaining = self.max_actions - self.actions_this_month
        self.query_one("#actions-remaining", Static).update(
            f"Pozostało akcji: {remaining}/{self.max_actions}  |  [M] nowy miesiąc"
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
            actions.append({
                'id': 'sha', 'name': '📝 Podpisz SHA',
                'description': "Shareholders Agreement - umowa wspólników",
                'available': has_partner and c.cash_on_hand >= 5000,
                'blocked': 'Brak partnera' if not has_partner else 'Potrzebujesz 5000 PLN' if c.cash_on_hand < 5000 else '',
                'recommended': has_partner,
                'cost': 5000,
                'consequences': ["Koszt prawnika: 3000-8000 PLN"],
                'benefits': ["Jasne zasady vestingu", "Ochrona przed bad leaver", "Procedury rozwiązywania sporów"],
                'risks': ["Bez umowy: KRYTYCZNE RYZYKO sporów!"],
                'warning': "⚠️ BEZ UMOWY RYZYKUJESZ WSZYSTKO!" if has_partner else ""
            })
        
        # PRODUKT
        if not c.mvp_completed:
            actions.append({
                'id': 'mvp', 'name': '🔧 Rozwijaj MVP',
                'description': "Kontynuuj prace nad produktem",
                'available': True,
                'recommended': True,
                'consequences': ["Postęp: +20-35%"],
                'benefits': ["Przybliża do klientów", "Walidacja pomysłu"],
                'risks': []
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
        
        actions.append({
            'id': 'skip', 'name': '⏭️ Pomiń (następny miesiąc)',
            'description': "Kontynuuj obecną strategię",
            'available': True,
            'consequences': ["Organiczny wzrost/spadek"]
        })
        
        return actions
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if self.actions_this_month >= self.max_actions:
            return
        
        item_id = event.item.id
        if not item_id or not item_id.startswith("action-"):
            return
        
        idx = int(item_id.split("-")[1])
        
        if idx < len(self.current_actions):
            action = self.current_actions[idx]
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
                self._log_action(action['name'], f"-{cost} PLN, spółka zarejestrowana")
        
        elif action['id'] == 'sha':
            cost = action.get('cost', 5000)
            if c.cash_on_hand >= cost:
                c.cash_on_hand -= cost
                self.game_state.agreement_signed = True
                self.game_state.founders_agreement.signed = True
                self._log_action(action['name'], f"-{cost} PLN, SHA podpisana")
        
        elif action['id'] == 'mvp':
            progress = random.randint(20, 35)
            self.game_state.mvp_progress = min(100, self.game_state.mvp_progress + progress)
            if self.game_state.mvp_progress >= 100:
                c.mvp_completed = True
                self._log_action(action['name'], "🎉 MVP ukończone!")
            else:
                self._log_action(action['name'], f"+{progress}% (teraz: {self.game_state.mvp_progress}%)")
        
        elif action['id'] == 'customers':
            new_customers = random.randint(1, 5)
            avg_mrr = random.randint(150, 350)
            c.total_customers += new_customers
            c.paying_customers += new_customers
            c.mrr += new_customers * avg_mrr
            self._log_action(action['name'], f"+{new_customers} klientów, MRR +{new_customers * avg_mrr} PLN")
        
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
                self._log_action(action['name'], f"🎯 +{amount:,} PLN za {dilution}%")
            else:
                self._log_action(action['name'], "Rozmowy trwają...")
        
        elif action['id'] == 'hire':
            c.employees += 1
            c.monthly_burn_rate += 12000
            self._log_action(action['name'], "+1 pracownik, burn +12k/mies")
        
        elif action['id'] == 'pivot':
            self.game_state.mvp_progress = max(30, self.game_state.mvp_progress - 40)
            c.total_customers = c.total_customers // 2
            c.paying_customers = c.paying_customers // 2
            c.mrr = c.mrr // 2
            self._log_action(action['name'], "Pivot! -40% MVP, -50% klientów")
        
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
        if self.app.config.has_partner and not self.game_state.agreement_signed and month > 3:
            events.append(
                ('negative', '⚔️ Konflikt z partnerem!', 'Spór o podział obowiązków i equity!', lambda: 'Podpisz SHA aby uniknąć!')
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
    
    def action_equity(self) -> None:
        self.app.push_screen(EquityScreen(self.game_state))
    
    def action_historia(self) -> None:
        self.app.push_screen(HistoryScreen(self.action_history))
    
    def action_show_risk(self) -> None:
        self.app.push_screen(RiskModal(self.game_state, self.app.config))
    
    def action_glossary(self) -> None:
        self.app.push_screen(GlossaryScreen())
    
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
            Static("  R - analiza ryzyka"),
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
    .hint { color: $text-muted; font-size: 80%; }
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
    
    Button { margin: 1 0; }
    ListView { height: auto; max-height: 12; }
    Tree { height: auto; }
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
