from __future__ import annotations
from datetime import date

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from planner import storage
from planner.app import PRIORITY_COLORS


class DashboardScreen(Screen):
    BINDINGS = [
        Binding("p", "app.goto_projects", "Projects", show=True),
        Binding("n", "app.goto_planning", "Planning", show=True),
        Binding("m", "app.goto_meetings", "Meetings", show=True),
        Binding("r", "refresh", "Refresh", show=False),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="dash-grid"):
            yield Static("", id="dash-today")
            yield Static("", id="dash-deadlines")
        yield Static("", id="dash-stats")
        yield Footer()

    def on_mount(self) -> None:
        self._reload()

    def _reload(self) -> None:
        projects = storage.load_all_projects()
        today = date.today()
        plan = storage.load_day_plan(today)

        task_lookup: dict[str, tuple] = {}
        for proj in projects:
            for t in proj.tasks:
                task_lookup[t.id] = (t, proj.name)

        # Today panel — meetings then tasks
        meetings_today = storage.get_meetings_for_date(today)
        mtg_hours = sum(m.duration_hours() for m in meetings_today)
        free_hours = max(0.0, plan.available_hours - mtg_hours)

        plan_lines = []
        for m in meetings_today:
            loc = f" [dim]@ {m.location}[/dim]" if m.location else ""
            plan_lines.append(f"[dim]{m.start_time}–{m.end_time}[/dim] [blue]■[/blue] {m.title}{loc}")

        for block in plan.schedule:
            info = task_lookup.get(block.task_id)
            if info:
                t, pname = info
                time_str = ""
                if block.start_time and block.end_time:
                    time_str = f"[dim]{block.start_time}–{block.end_time}[/dim] "
                color = PRIORITY_COLORS.get(t.priority, "white")
                done_mark = " [dim]✓[/dim]" if t.status == "done" else ""
                plan_lines.append(f"{time_str}[{color}]●[/{color}] {t.title}[dim] ({pname})[/dim]{done_mark}")

        today_str = today.strftime("%A, %B %-d")
        avail_str = f"{free_hours:.1f}h free" + (f" [dim]({mtg_hours:.1f}h meetings)[/dim]" if meetings_today else "")
        today_text = f"[bold]Today — {today_str}[/bold]\n[dim]{avail_str}[/dim]\n\n"
        if plan_lines:
            today_text += "\n".join(plan_lines)
        else:
            today_text += "[dim]No meetings or tasks scheduled.\nPress [bold]n[/bold] to open Planning.[/dim]"
        self.query_one("#dash-today", Static).update(today_text)

        # Deadlines panel
        deadline_lines = []
        for proj in projects:
            for t in proj.upcoming_deadlines(within_days=14):
                days = t.deadline_days()
                if days is None:
                    continue
                if days < 0:
                    when = f"[red]{abs(days)}d overdue[/red]"
                elif days == 0:
                    when = "[red bold]TODAY[/red bold]"
                elif days == 1:
                    when = "[yellow]tomorrow[/yellow]"
                else:
                    when = f"[yellow]in {days}d[/yellow]"
                color = PRIORITY_COLORS.get(t.priority, "white")
                deadline_lines.append(
                    f"[{color}]●[/{color}] {t.title} [dim]({proj.name})[/dim] — {when}"
                )

        dead_text = "[bold]Upcoming Deadlines[/bold]\n[dim](next 14 days)[/dim]\n\n"
        if deadline_lines:
            dead_text += "\n".join(deadline_lines)
        else:
            dead_text += "[dim]No upcoming deadlines.[/dim]"
        self.query_one("#dash-deadlines", Static).update(dead_text)

        # Stats bar
        open_count = sum(len(p.open_tasks()) for p in projects)
        self.query_one("#dash-stats", Static).update(
            f" Projects: {len(projects)}   Open tasks: {open_count}"
            f"   Scheduled today: {len(plan.schedule)}"
        )

    def action_refresh(self) -> None:
        self._reload()
