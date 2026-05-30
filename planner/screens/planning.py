from __future__ import annotations
from datetime import date, timedelta

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Label, Static

from planner import storage
from planner.app import PRIORITY_COLORS


class PlanningScreen(Screen):
    BINDINGS = [
        Binding("space", "toggle_task", "Add/Remove", show=True),
        Binding("s", "ai_schedule", "AI Schedule", show=True),
        Binding("[", "prev_day", "← Day", show=True),
        Binding("]", "next_day", "Day →", show=True),
        Binding("t", "goto_today", "Today", show=False),
        Binding("f", "cycle_project_filter", "Filter", show=False),
        Binding("r", "refresh", "Refresh", show=False),
        Binding("escape", "app.goto_dashboard", "Back", show=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._current_date = date.today()
        self._project_filter: str | None = None
        self._project_names: list[str] = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="plan-grid"):
            with Vertical(id="pool-panel"):
                yield Static("", id="pool-header")
                yield DataTable(id="pool-table", cursor_type="row", zebra_stripes=True)
            with Vertical(id="today-panel"):
                yield Static("", id="today-header")
                yield DataTable(id="today-table", cursor_type="row", zebra_stripes=False)
        yield Static("", id="plan-date-bar")
        yield Footer()

    def on_mount(self) -> None:
        pool_table = self.query_one("#pool-table", DataTable)
        pool_table.add_columns("Project", "Title", "Priority", "Deadline", "Est.")

        today_table = self.query_one("#today-table", DataTable)
        today_table.add_columns("Time", "Project", "Title", "Status")

        self._project_names = storage.list_project_names()
        self._reload()

    def _reload(self) -> None:
        self._project_names = storage.list_project_names()
        plan = storage.load_day_plan(self._current_date)

        task_lookup: dict[str, tuple] = {}
        all_open: list[tuple] = []  # (task, project_name)

        for proj_name in self._project_names:
            if self._project_filter and proj_name != self._project_filter:
                continue
            for t in storage.load_tasks(proj_name):
                task_lookup[t.id] = (t, proj_name)
                if t.is_open():
                    all_open.append((t, proj_name))

        # sort by deadline (nulls last), then priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        all_open.sort(key=lambda x: (
            x[0].deadline or date(9999, 12, 31),
            priority_order.get(x[0].priority, 1),
        ))

        scheduled_ids = {b.task_id for b in plan.schedule}

        # pool table
        pool_table = self.query_one("#pool-table", DataTable)
        pool_table.clear()
        for t, pname in all_open:
            deadline_str = t.deadline.isoformat() if t.deadline else "—"
            days = t.deadline_days()
            if days is not None:
                if days < 0:
                    deadline_str = f"[red]{deadline_str}[/red]"
                elif days <= 3:
                    deadline_str = f"[yellow]{deadline_str}[/yellow]"
            color = PRIORITY_COLORS.get(t.priority, "white")
            in_plan = " ✓" if t.id in scheduled_ids else ""
            pool_table.add_row(
                pname,
                f"[{color}]{t.title}{in_plan}[/{color}]",
                f"[{color}]{t.priority}[/{color}]",
                deadline_str,
                f"{t.estimate_hours}h" if t.estimate_hours else "—",
                key=t.id,
            )

        # today table — meetings first (sorted by start), then tasks
        today_table = self.query_one("#today-table", DataTable)
        today_table.clear()

        meetings_today = storage.get_meetings_for_date(self._current_date)
        mtg_hours = sum(m.duration_hours() for m in meetings_today)

        # meetings rows (non-selectable sentinel keys with "mtg:" prefix)
        for m in meetings_today:
            loc_str = f" [dim]@ {m.location}[/dim]" if m.location else ""
            today_table.add_row(
                f"{m.start_time}–{m.end_time}",
                "[dim]—[/dim]",
                f"[blue]{m.title}[/blue]{loc_str}",
                "[dim]mtg[/dim]",
                key=f"mtg:{m.id}",
            )

        total_task_hours = 0.0
        for block in plan.schedule:
            info = task_lookup.get(block.task_id)
            if info:
                t, pname = info
                time_str = "—"
                if block.start_time and block.end_time:
                    time_str = f"{block.start_time}–{block.end_time}"
                color = PRIORITY_COLORS.get(t.priority, "white")
                status_str = "[dim]✓[/dim]" if t.status == "done" else " "
                today_table.add_row(
                    time_str,
                    pname,
                    f"[{color}]{t.title}[/{color}]",
                    status_str,
                    key=block.task_id,
                )
                if t.estimate_hours:
                    total_task_hours += t.estimate_hours

        free_hours = max(0.0, plan.available_hours - mtg_hours)

        # headers
        filter_str = f"  [dim]filter: {self._project_filter or 'all'}[/dim]"
        self.query_one("#pool-header", Static).update(
            f"[bold]Task Pool[/bold] ({len(all_open)} open){filter_str}"
        )
        date_label = self._current_date.strftime("%A, %B %-d, %Y")
        is_today = self._current_date == date.today()
        day_str = "Today" if is_today else date_label
        mtg_str = f"  [blue]{len(meetings_today)} mtg ({mtg_hours:.1f}h)[/blue]" if meetings_today else ""
        self.query_one("#today-header", Static).update(
            f"[bold]{day_str}[/bold]"
            + mtg_str
            + f"  ({len(plan.schedule)} tasks"
            + (f", ~{total_task_hours:.1f}h" if total_task_hours else "")
            + f"  |  {free_hours:.1f}h free)"
        )

        # date bar
        if plan.ai_rationale:
            rationale = plan.ai_rationale[:100] + ("…" if len(plan.ai_rationale) > 100 else "")
            self.query_one("#plan-date-bar", Static).update(
                f" [dim]AI: {rationale}[/dim]"
            )
        else:
            self.query_one("#plan-date-bar", Static).update(
                " [dim]Space: add/remove task   s: AI schedule   [ / ]: navigate days[/dim]"
            )

    def action_refresh(self) -> None:
        self._reload()

    def action_toggle_task(self) -> None:
        pool_table = self.query_one("#pool-table", DataTable)
        if pool_table.has_focus and pool_table.row_count > 0:
            row_key, _ = pool_table.coordinate_to_cell_key(pool_table.cursor_coordinate)
            if row_key.value and not str(row_key.value).startswith("mtg:"):
                task_id = row_key.value
                # find project
                proj_name = None
                for pname in self._project_names:
                    for t in storage.load_tasks(pname):
                        if t.id == task_id:
                            proj_name = pname
                            break
                    if proj_name:
                        break
                if proj_name:
                    plan = storage.load_day_plan(self._current_date)
                    storage.toggle_task_in_plan(plan, task_id, proj_name)
                    self._reload()
            return

        today_table = self.query_one("#today-table", DataTable)
        if today_table.has_focus and today_table.row_count > 0:
            row_key, _ = today_table.coordinate_to_cell_key(today_table.cursor_coordinate)
            if row_key.value and not str(row_key.value).startswith("mtg:"):
                plan = storage.load_day_plan(self._current_date)
                storage.toggle_task_in_plan(plan, row_key.value, "")
                self._reload()

    def action_prev_day(self) -> None:
        self._current_date -= timedelta(days=1)
        self._reload()

    def action_next_day(self) -> None:
        self._current_date += timedelta(days=1)
        self._reload()

    def action_goto_today(self) -> None:
        self._current_date = date.today()
        self._reload()

    def action_cycle_project_filter(self) -> None:
        names = [None] + self._project_names
        idx = names.index(self._project_filter) if self._project_filter in names else 0
        self._project_filter = names[(idx + 1) % len(names)]
        self._reload()

    def action_ai_schedule(self) -> None:
        plan = storage.load_day_plan(self._current_date)
        if not plan.schedule:
            self.notify("Add tasks to today's plan first (Space), then use AI scheduling.", severity="warning")
            return
        from planner.modals.schedule_modal import ScheduleModal
        self.app.push_screen(
            ScheduleModal(self._current_date, plan),
            callback=self._on_schedule_accepted,
        )

    def _on_schedule_accepted(self, updated_plan) -> None:
        if updated_plan is not None:
            storage.save_day_plan(updated_plan)
            self._reload()
            self.notify("Schedule saved.")
