from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static


_HELP_TEXT = """\
[bold]Global (always available)[/bold]
  d         → Dashboard
  c         → Calendar (weekly view)
  q         → Quit
  ?         → This help

[bold]Dashboard[/bold]
  p         → Projects
  n         → Planning
  m         → Meetings

[bold]Projects Screen[/bold]
  a         → Add project
  Enter     → Open project
  D         → Delete project (capital D)

[bold]Project Detail[/bold]
  1 / 2 / 3 → Switch to Tasks / Papers / Notes tab
  a         → Add item
  e         → Edit selected item
  Space     → Toggle task done/open
  o         → Open PDF or note in editor
  d         → Delete item
  f         → Cycle filter

[bold]Calendar Screen[/bold]
  [ / ]     → Previous / next week
  t         → Jump to current week

[bold]Planning Screen[/bold]
  Space     → Add/remove task from plan
  s         → AI Schedule (generates time-blocked day)
  [ / ]     → Navigate to previous/next day
  t         → Jump to today
  f         → Filter task pool by project

[bold]Modals[/bold]
  Ctrl+S    → Save
  Escape    → Cancel / close
"""


class HelpModal(ModalScreen):
    BINDINGS = [
        Binding("escape", "dismiss_modal", "Close"),
        Binding("q", "dismiss_modal", "Close"),
    ]

    def compose(self) -> ComposeResult:
        with Container(classes="modal-container"):
            yield Label("Keyboard Reference", classes="modal-title")
            yield Static(_HELP_TEXT, id="help-content")
            yield Button("Close", variant="default", id="btn-close")

    def action_dismiss_modal(self) -> None:
        self.dismiss()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss()
