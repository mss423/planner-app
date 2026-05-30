from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from typing import Optional
import uuid


def _new_id() -> str:
    return str(uuid.uuid4())


@dataclass
class Task:
    title: str
    id: str = field(default_factory=_new_id)
    priority: str = "medium"          # high | medium | low
    deadline: Optional[date] = None
    estimate_hours: Optional[float] = None
    status: str = "open"              # open | in_progress | done
    created: date = field(default_factory=date.today)
    completed: Optional[date] = None
    notes: str = ""

    def is_open(self) -> bool:
        return self.status != "done"

    def deadline_days(self) -> Optional[int]:
        if self.deadline is None:
            return None
        return (self.deadline - date.today()).days


@dataclass
class Paper:
    title: str
    id: str = field(default_factory=_new_id)
    authors: str = ""
    year: Optional[int] = None
    venue: str = ""
    file: Optional[str] = None        # path relative to project dir
    status: str = "unread"            # unread | reading | read
    added: date = field(default_factory=date.today)
    abstract: str = ""
    notes: str = ""


@dataclass
class ScheduledBlock:
    task_id: str
    project: str
    start_time: Optional[str] = None  # "HH:MM"
    end_time: Optional[str] = None
    notes: str = ""


@dataclass
class DayPlan:
    date: date
    available_hours: float = 6.0
    ai_rationale: str = ""
    schedule: list[ScheduledBlock] = field(default_factory=list)


_WEEKDAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
_WEEKDAY_MAP = {name: i for i, name in enumerate(_WEEKDAY_NAMES)}


@dataclass
class Meeting:
    title: str
    id: str = field(default_factory=_new_id)
    start_time: str = "09:00"           # "HH:MM"
    end_time: str = "10:00"             # "HH:MM"
    location: str = ""
    notes: str = ""
    recurrence: str = "none"            # "none" | "daily" | "weekly"
    days: list[int] = field(default_factory=list)  # weekday ints 0=Mon..6=Sun (weekly only)
    date: Optional[date] = None         # for one-time meetings
    active: bool = True

    def occurs_on(self, d: date) -> bool:
        if not self.active:
            return False
        if self.recurrence == "none":
            return self.date == d
        if self.recurrence == "daily":
            return True
        if self.recurrence == "weekly":
            return d.weekday() in self.days
        return False

    def duration_hours(self) -> float:
        try:
            sh, sm = map(int, self.start_time.split(":"))
            eh, em = map(int, self.end_time.split(":"))
            return max(0.0, (eh * 60 + em - sh * 60 - sm) / 60)
        except Exception:
            return 0.0

    def days_label(self) -> str:
        if self.recurrence == "none":
            return self.date.isoformat() if self.date else "—"
        if self.recurrence == "daily":
            return "Every day"
        if self.recurrence == "weekly":
            return ", ".join(_WEEKDAY_NAMES[d] for d in sorted(self.days)) or "—"
        return "—"


@dataclass
class Project:
    name: str
    tasks: list[Task] = field(default_factory=list)
    papers: list[Paper] = field(default_factory=list)

    def open_tasks(self) -> list[Task]:
        return [t for t in self.tasks if t.is_open()]

    def upcoming_deadlines(self, within_days: int = 14) -> list[Task]:
        result = []
        for t in self.tasks:
            if t.is_open() and t.deadline is not None:
                days = t.deadline_days()
                if days is not None and days <= within_days:
                    result.append(t)
        return sorted(result, key=lambda t: t.deadline)
