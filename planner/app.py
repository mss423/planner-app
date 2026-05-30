from __future__ import annotations
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Header

from planner import config


PRIORITY_COLORS = {"high": "red", "medium": "yellow", "low": "green"}
STATUS_COLORS = {"open": "white", "in_progress": "cyan", "done": "dim"}
PAPER_STATUS_COLORS = {"unread": "white", "reading": "yellow", "read": "dim"}


class PlannerApp(App):
    CSS = """
    Screen {
        background: $background;
    }

    /* ── common ── */
    .title {
        text-style: bold;
        color: $accent;
        padding: 0 1;
    }

    .section-header {
        background: $panel;
        color: $text;
        text-style: bold;
        padding: 0 1;
        height: 1;
    }

    .hint {
        color: $text-muted;
        text-style: italic;
    }

    /* ── dashboard ── */
    #dash-grid {
        layout: grid;
        grid-size: 2 1;
        grid-gutter: 1;
        padding: 1;
        height: 1fr;
    }

    #dash-today {
        border: round $accent;
        padding: 0 1;
    }

    #dash-deadlines {
        border: round $warning;
        padding: 0 1;
    }

    #dash-stats {
        dock: bottom;
        height: 1;
        background: $panel;
        padding: 0 1;
        color: $text-muted;
    }

    /* ── projects screen ── */
    #projects-table {
        height: 1fr;
    }

    /* ── project detail ── */
    #detail-tabs {
        height: 1fr;
    }

    /* ── planning screen ── */
    #plan-grid {
        layout: grid;
        grid-size: 2 1;
        grid-gutter: 1;
        padding: 1;
        height: 1fr;
    }

    #pool-panel {
        border: round $accent;
        padding: 0 1;
    }

    #today-panel {
        border: round $success;
        padding: 0 1;
    }

    #plan-date-bar {
        dock: bottom;
        height: 1;
        background: $panel;
        padding: 0 1;
        color: $text-muted;
    }

    /* ── calendar ── */
    #cal-week-label {
        height: 1;
        padding: 0 1;
        background: $panel;
    }

    #cal-grid {
        height: 1fr;
    }

    .cal-day {
        width: 1fr;
        border: round $panel;
        padding: 0 1;
        overflow-y: auto;
    }

    /* ── modals ── */
    ModalScreen {
        align: center middle;
    }

    .modal-container {
        background: $surface;
        border: round $accent;
        padding: 1 2;
        width: 70;
        height: 28;
    }

    .modal-body {
        height: 1fr;
    }

    .modal-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    .modal-buttons {
        layout: horizontal;
        height: 3;
        align: right middle;
        margin-top: 1;
    }

    .modal-buttons Button {
        margin-left: 1;
    }

    Input {
        margin-bottom: 1;
    }

    Select {
        margin-bottom: 1;
    }

    TextArea {
        margin-bottom: 1;
        height: 4;
    }

    #sched-container {
        height: 36;
    }

    /* ── schedule modal ── */
    #schedule-result {
        border: round $panel;
        padding: 0 1;
        margin-top: 1;
    }

    /* ── setup screen ── */
    #setup-container {
        align: center middle;
        height: 100%;
    }

    #setup-box {
        background: $surface;
        border: round $accent;
        padding: 2 4;
        width: 60;
    }
    """

    BINDINGS = [
        Binding("question_mark", "show_help", "Help", show=False),
        Binding("c", "goto_calendar", "Calendar", show=True),
        Binding("d", "goto_dashboard", "Dashboard", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    def _handle_exception(self, error: Exception) -> None:
        import traceback, datetime
        log = f"/tmp/planner_crash_{datetime.datetime.now().strftime('%H%M%S')}.log"
        with open(log, "w") as f:
            traceback.print_exc(file=f)
            f.write(f"\nException type: {type(error)}\nException: {error}\n")
        super()._handle_exception(error)

    def on_mount(self) -> None:
        if not config.is_configured():
            from planner.screens.setup import SetupScreen
            self.push_screen(SetupScreen())
        else:
            from planner.screens.dashboard import DashboardScreen
            self.push_screen(DashboardScreen())

    def action_goto_dashboard(self) -> None:
        from planner.screens.dashboard import DashboardScreen
        self.switch_screen(DashboardScreen())

    def action_goto_projects(self) -> None:
        from planner.screens.projects import ProjectsScreen
        self.switch_screen(ProjectsScreen())

    def action_goto_planning(self) -> None:
        from planner.screens.planning import PlanningScreen
        self.switch_screen(PlanningScreen())

    def action_goto_calendar(self) -> None:
        from planner.screens.calendar import CalendarScreen
        self.switch_screen(CalendarScreen())

    def action_goto_meetings(self) -> None:
        from planner.screens.meetings import MeetingsScreen
        self.switch_screen(MeetingsScreen())

    def action_show_help(self) -> None:
        from planner.modals.help_modal import HelpModal
        self.push_screen(HelpModal())
