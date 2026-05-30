from __future__ import annotations
from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Button, Footer, Input, Label, Static

from planner import config


class SetupScreen(Screen):
    BINDINGS = [
        Binding("ctrl+s", "save", "Save & Launch"),
    ]

    def compose(self) -> ComposeResult:
        with Container(id="setup-container"):
            with Container(id="setup-box"):
                yield Static(
                    "[bold]Welcome to AI Research Planner[/bold]\n\n"
                    "Let's set up your research directory.\n"
                    "All projects, tasks, and notes will be stored there.",
                    id="setup-intro",
                )
                yield Label("Research directory:")
                yield Input(
                    value=str(config._DEFAULT_RESEARCH_DIR),
                    id="setup-dir",
                    placeholder="~/Documents/research",
                )
                yield Static("", id="setup-error")
                yield Button("Save & Launch", variant="primary", id="btn-save")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#setup-dir", Input).focus()

    @on(Button.Pressed, "#btn-save")
    def handle_save_button(self) -> None:
        self.action_save()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.action_save()

    def action_save(self) -> None:
        raw = self.query_one("#setup-dir", Input).value.strip()
        if not raw:
            self.query_one("#setup-error", Static).update("[red]Please enter a directory path.[/red]")
            return
        path = Path(raw).expanduser()
        try:
            config.initialize(path)
        except Exception as e:
            self.query_one("#setup-error", Static).update(f"[red]Error: {e}[/red]")
            return

        self.notify(f"Initialized at {path}")
        from planner.screens.dashboard import DashboardScreen
        self.app.switch_screen(DashboardScreen())
