from __future__ import annotations
import threading
from datetime import date

from textual.app import ComposeResult
from textual.binding import Binding
from textual import on
from textual.containers import Container, Horizontal, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, LoadingIndicator, Select, Static

from planner.models import DayPlan


class ScheduleModal(ModalScreen[DayPlan | None]):
    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, plan_date: date, plan: DayPlan) -> None:
        super().__init__()
        self._plan_date = plan_date
        self._plan = plan
        self._result: dict | None = None

    def compose(self) -> ComposeResult:
        with Container(classes="modal-container", id="sched-container"):
            yield Label("AI Schedule Assistant", classes="modal-title")
            with VerticalScroll(classes="modal-body"):
                yield Label(f"Date: {self._plan_date.isoformat()}  |  Tasks: {len(self._plan.schedule)}")

                yield Label("Available hours today")
                yield Input(
                    value=str(self._plan.available_hours),
                    id="sched-hours",
                    placeholder="e.g. 6",
                )

                yield Label("Preferred start time (HH:MM)")
                yield Input(value="09:00", id="sched-start", placeholder="09:00")

                yield Label("Constraints (optional)")
                yield Input(id="sched-constraints", placeholder='e.g. "no meetings before 10am, break at noon"')

                yield LoadingIndicator(id="sched-spinner")
                yield Static("", id="schedule-result")

            with Horizontal(classes="modal-buttons"):
                yield Button("Cancel", variant="default", id="btn-cancel")
                yield Button("Generate Schedule", variant="primary", id="btn-generate")
                yield Button("Accept", variant="success", id="btn-accept", disabled=True)

    def on_mount(self) -> None:
        self.query_one("#sched-spinner", LoadingIndicator).display = False
        self.query_one("#schedule-result", Static).display = False
        self.query_one("#sched-hours", Input).focus()

    @on(Button.Pressed, "#btn-cancel")
    def handle_cancel(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed, "#btn-generate")
    def handle_generate(self) -> None:
        self._run_schedule()

    @on(Button.Pressed, "#btn-accept")
    def handle_accept(self) -> None:
        self._accept()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def _run_schedule(self) -> None:
        hours_str = self.query_one("#sched-hours", Input).value.strip()
        try:
            hours = float(hours_str)
        except ValueError:
            self.notify("Enter a valid number for available hours.", severity="error")
            return

        start_time = self.query_one("#sched-start", Input).value.strip() or "09:00"
        constraints = self.query_one("#sched-constraints", Input).value.strip()

        self._plan.available_hours = hours
        self.query_one("#sched-spinner", LoadingIndicator).display = True
        self.query_one("#schedule-result", Static).display = False
        self.query_one("#btn-generate", Button).disabled = True
        self.query_one("#btn-accept", Button).disabled = True

        # gather tasks and today's meetings
        from planner import storage
        tasks = []
        for block in self._plan.schedule:
            for pname in storage.list_project_names():
                for t in storage.load_tasks(pname):
                    if t.id == block.task_id:
                        tasks.append((t, pname))
                        break
        meetings = storage.get_meetings_for_date(self._plan_date)

        def _worker():
            try:
                from planner import ai_scheduler
                result = ai_scheduler.schedule(
                    self._plan_date, tasks, hours, meetings, constraints, start_time
                )
                self.app.call_from_thread(self._on_result, result, None)
            except Exception as e:
                self.app.call_from_thread(self._on_result, None, str(e))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_result(self, result: dict | None, error: str | None) -> None:
        self.query_one("#sched-spinner", LoadingIndicator).display = False
        result_widget = self.query_one("#schedule-result", Static)
        result_widget.display = True

        if error:
            result_widget.update(f"[red]Error:[/red] {error}")
            self.query_one("#btn-generate", Button).disabled = False
            return

        self._result = result

        # format result for display
        lines = []
        rationale = result.get("rationale", "")
        if rationale:
            lines.append(f"[bold]Rationale:[/bold] {rationale}\n")

        lines.append("[bold]Schedule:[/bold]")
        from planner import storage
        task_title_map = {}
        for pname in storage.list_project_names():
            for t in storage.load_tasks(pname):
                task_title_map[t.id] = (t.title, pname)

        for entry in result.get("schedule", []):
            tid = entry.get("task_id", "")
            title, pname = task_title_map.get(tid, ("Unknown task", ""))
            start = entry.get("start", "?")
            end = entry.get("end", "?")
            notes = entry.get("notes", "")
            note_str = f" — [dim]{notes}[/dim]" if notes else ""
            lines.append(f"  [cyan]{start}–{end}[/cyan]  {title} [dim]({pname})[/dim]{note_str}")

        unscheduled = result.get("unscheduled", [])
        if unscheduled:
            reason = result.get("unscheduled_reason", "")
            lines.append(f"\n[yellow]Not scheduled ({len(unscheduled)} tasks):[/yellow] {reason}")
            for tid in unscheduled:
                title, _ = task_title_map.get(tid, ("Unknown", ""))
                lines.append(f"  • {title}")

        result_widget.update("\n".join(lines))
        self.query_one("#btn-generate", Button).disabled = False
        self.query_one("#btn-accept", Button).disabled = False

    def _accept(self) -> None:
        if self._result is None:
            return
        from planner import storage, ai_scheduler
        tasks = []
        for block in self._plan.schedule:
            for pname in storage.list_project_names():
                for t in storage.load_tasks(pname):
                    if t.id == block.task_id:
                        tasks.append((t, pname))
                        break
        updated = ai_scheduler.apply_schedule(self._plan, self._result, tasks)
        self.dismiss(updated)
