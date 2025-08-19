from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Select, Label, Footer, SelectionList
from typing import Optional

from .data import agent_rules, services


class SelectAgentApp(App):
    CSS_PATH = "stylesheet/selection_list.tcss"
    BINDINGS = [
        Binding(
            key="ctrl+q", action="quit", description="Submit", key_display="ctrl+q"
        ),
        Binding(
            key="ctrl+d",
            action="toggle_dark",
            description="Toggle Dark Theme",
            key_display="ctrl+d",
        ),
    ]
    selected: list[str] = []

    def compose(self) -> ComposeResult:
        yield SelectionList[str](
            *[(agent, agent_rules[agent]) for agent in agent_rules]
        )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one(
            SelectionList
        ).border_title = "Select the Coding Agents you want to write instructions for."

    def action_toggle_dark(self) -> None:
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"  # type: ignore
        )

    @on(SelectionList.SelectedChanged)
    def select_changed(self, event: SelectionList.SelectedChanged) -> None:
        self.selected.extend(event.selection_list.selected)
        self.selected = list(set(self.selected))


class SelectServiceApp(App):
    CSS_PATH = "stylesheet/select.tcss"
    BINDINGS = [
        Binding(
            key="ctrl+q", action="quit", description="Submit", key_display="ctrl+q"
        ),
        Binding(
            key="ctrl+d",
            action="toggle_dark",
            description="Toggle Dark Theme",
            key_display="ctrl+d",
        ),
    ]
    selected: Optional[str] = None

    def compose(self) -> ComposeResult:
        yield Label("Select the service", id="label1")
        yield Select(
            options=[(service, services[service]) for service in services],
            prompt="Select the service you would like to work with",
        )
        yield Footer()

    def action_toggle_dark(self) -> None:
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"  # type: ignore
        )

    @on(Select.Changed)
    def select_changed(self, event: Select.Changed) -> None:
        self.selected = str(event.value)
