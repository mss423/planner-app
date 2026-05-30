from __future__ import annotations
from datetime import date, timedelta

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from planner import storage
from planner.app import PRIORITY_COLORS


def _week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


class CalendarScreen(Screen):
    BINDINGS = [
        Binding("[", "prev_week", "← Week", show=True),
        Binding("]", "next_week", "Week →", show=True),
        Binding("t", "goto_today", "Today", show=False),
        Binding("escape", "app.goto_dashboard", "Back", show=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._week_monday = _week_start(date.today())

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("", id="cal-week-label")
        with Horizontal(id="cal-grid"):
            for i in range(7):
                yield Static("", id=f"cal-day-{i}", classes="cal-day")
        yield Footer()

    def on_mount(self) -> None:
        self._reload()

    def _reload(self) -> None:
        projects = storage.load_all_projects()

        # deadline map: date → [(task, project_name)]
        deadline_map: dict[date, list] = {}
        for proj in projects:
            for t in proj.tasks:
                if t.is_open() and t.deadline:
                    deadline_map.setdefault(t.deadline, []).append((t, proj.name))

        today = date.today()
        week_end = self._week_monday + timedelta(days=6)
        self.query_one("#cal-week-label", Static).update(
            f"[bold]  {self._week_monday.strftime('%B %-d')} – "
            f"{week_end.strftime('%B %-d, %Y')}[/bold]"
        )

        for i in range(7):
            day = self._week_monday + timedelta(days=i)
            self._render_day(i, day, today, deadline_map)

    def _render_day(
        self,
        col: int,
        day: date,
        today: date,
        deadline_map: dict,
    ) -> None:
        is_today = day == today
        is_past = day < today

        day_name = day.strftime("%a")
        date_str = day.strftime("%-m/%-d")

        if is_today:
            header = f"[bold reverse] {day_name} {date_str} [/bold reverse]"
        elif is_past:
            header = f"[dim]{day_name} {date_str}[/dim]"
        else:
            header = f"[bold]{day_name} {date_str}[/bold]"

        lines = [header, "[dim]────────────[/dim]"]

        meetings = storage.get_meetings_for_date(day)
        for m in meetings:
            title = m.title if len(m.title) <= 16 else m.title[:15] + "…"
            loc = f"\n  [dim]{m.location[:14]}[/dim]" if m.location else ""
            lines.append(f"[blue]{m.start_time}[/blue] {title}{loc}")

        deadlines = deadline_map.get(day, [])
        deadlines.sort(key=lambda x: PRIORITY_COLORS.get(x[0].priority, "z"))
        for t, pname in deadlines:
            color = PRIORITY_COLORS.get(t.priority, "white")
            title = t.title if len(t.title) <= 14 else t.title[:13] + "…"
            proj = pname if len(pname) <= 14 else pname[:13] + "…"
            lines.append(f"[{color}]▶ DUE: {title}[/{color}]")
            lines.append(f"  [dim]{proj}[/dim]")

        if not meetings and not deadlines:
            lines.append("[dim]—[/dim]")

        if is_past and (meetings or deadlines):
            # dim the whole day's content slightly
            content = "\n".join(lines)
        else:
            content = "\n".join(lines)

        self.query_one(f"#cal-day-{col}", Static).update(content)

    def action_prev_week(self) -> None:
        self._week_monday -= timedelta(weeks=1)
        self._reload()

    def action_next_week(self) -> None:
        self._week_monday += timedelta(weeks=1)
        self._reload()

    def action_goto_today(self) -> None:
        self._week_monday = _week_start(date.today())
        self._reload()
