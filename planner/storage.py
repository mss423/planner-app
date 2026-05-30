from __future__ import annotations
from datetime import date
from pathlib import Path
from typing import Optional
import yaml

from planner import config
from planner.models import DayPlan, Meeting, Paper, Project, ScheduledBlock, Task


# ── helpers ──────────────────────────────────────────────────────────────────

def _projects_dir() -> Path:
    return config.research_dir() / "projects"


def _planning_dir() -> Path:
    return config.research_dir() / "planning" / "days"


def _parse_date(val) -> Optional[date]:
    if val is None:
        return None
    if isinstance(val, date):
        return val
    return date.fromisoformat(str(val))


# ── projects ──────────────────────────────────────────────────────────────────

def list_project_names() -> list[str]:
    d = _projects_dir()
    if not d.exists():
        return []
    return sorted(p.name for p in d.iterdir() if p.is_dir())


def project_dir(name: str) -> Path:
    return _projects_dir() / name


def create_project(name: str) -> Project:
    d = project_dir(name)
    (d / "notes").mkdir(parents=True, exist_ok=True)
    (d / "papers").mkdir(parents=True, exist_ok=True)
    _write_tasks(name, [])
    _write_papers(name, [])
    return Project(name=name)


def delete_project(name: str) -> None:
    import shutil
    shutil.rmtree(project_dir(name), ignore_errors=True)


def load_project(name: str) -> Project:
    return Project(
        name=name,
        tasks=load_tasks(name),
        papers=load_papers(name),
    )


def load_all_projects() -> list[Project]:
    return [load_project(n) for n in list_project_names()]


# ── tasks ─────────────────────────────────────────────────────────────────────

def _tasks_file(name: str) -> Path:
    return project_dir(name) / "tasks.yaml"


def _task_from_dict(d: dict) -> Task:
    return Task(
        id=d["id"],
        title=d["title"],
        priority=d.get("priority", "medium"),
        deadline=_parse_date(d.get("deadline")),
        estimate_hours=d.get("estimate_hours"),
        status=d.get("status", "open"),
        created=_parse_date(d.get("created")) or date.today(),
        completed=_parse_date(d.get("completed")),
        notes=d.get("notes", ""),
    )


def _task_to_dict(t: Task) -> dict:
    return {
        "id": t.id,
        "title": t.title,
        "priority": t.priority,
        "deadline": t.deadline.isoformat() if t.deadline else None,
        "estimate_hours": t.estimate_hours,
        "status": t.status,
        "created": t.created.isoformat(),
        "completed": t.completed.isoformat() if t.completed else None,
        "notes": t.notes,
    }


def load_tasks(project_name: str) -> list[Task]:
    f = _tasks_file(project_name)
    if not f.exists():
        return []
    with open(f) as fh:
        data = yaml.safe_load(fh) or {}
    return [_task_from_dict(d) for d in data.get("tasks", [])]


def _write_tasks(project_name: str, tasks: list[Task]) -> None:
    f = _tasks_file(project_name)
    f.parent.mkdir(parents=True, exist_ok=True)
    with open(f, "w") as fh:
        yaml.dump({"tasks": [_task_to_dict(t) for t in tasks]}, fh, default_flow_style=False)


def save_task(project_name: str, task: Task) -> None:
    tasks = load_tasks(project_name)
    for i, t in enumerate(tasks):
        if t.id == task.id:
            tasks[i] = task
            _write_tasks(project_name, tasks)
            return
    tasks.append(task)
    _write_tasks(project_name, tasks)


def delete_task(project_name: str, task_id: str) -> None:
    tasks = [t for t in load_tasks(project_name) if t.id != task_id]
    _write_tasks(project_name, tasks)


# ── papers ────────────────────────────────────────────────────────────────────

def _papers_file(name: str) -> Path:
    return project_dir(name) / "papers.yaml"


def _paper_from_dict(d: dict) -> Paper:
    return Paper(
        id=d["id"],
        title=d["title"],
        authors=d.get("authors", ""),
        year=d.get("year"),
        venue=d.get("venue", ""),
        file=d.get("file"),
        status=d.get("status", "unread"),
        added=_parse_date(d.get("added")) or date.today(),
        abstract=d.get("abstract", ""),
        notes=d.get("notes", ""),
    )


def _paper_to_dict(p: Paper) -> dict:
    return {
        "id": p.id,
        "title": p.title,
        "authors": p.authors,
        "year": p.year,
        "venue": p.venue,
        "file": p.file,
        "status": p.status,
        "added": p.added.isoformat(),
        "abstract": p.abstract,
        "notes": p.notes,
    }


def load_papers(project_name: str) -> list[Paper]:
    f = _papers_file(project_name)
    if not f.exists():
        return []
    with open(f) as fh:
        data = yaml.safe_load(fh) or {}
    return [_paper_from_dict(d) for d in data.get("papers", [])]


def _write_papers(project_name: str, papers: list[Paper]) -> None:
    f = _papers_file(project_name)
    f.parent.mkdir(parents=True, exist_ok=True)
    with open(f, "w") as fh:
        yaml.dump({"papers": [_paper_to_dict(p) for p in papers]}, fh, default_flow_style=False)


def save_paper(project_name: str, paper: Paper) -> None:
    papers = load_papers(project_name)
    for i, p in enumerate(papers):
        if p.id == paper.id:
            papers[i] = paper
            _write_papers(project_name, papers)
            return
    papers.append(paper)
    _write_papers(project_name, papers)


def delete_paper(project_name: str, paper_id: str) -> None:
    papers = [p for p in load_papers(project_name) if p.id != paper_id]
    _write_papers(project_name, papers)


# ── notes ─────────────────────────────────────────────────────────────────────

def list_notes(project_name: str) -> list[Path]:
    notes_dir = project_dir(project_name) / "notes"
    if not notes_dir.exists():
        return []
    return sorted(p for p in notes_dir.iterdir() if p.is_file())


def create_note(project_name: str, filename: str) -> Path:
    if not filename.endswith((".md", ".tex")):
        filename += ".md"
    p = project_dir(project_name) / "notes" / filename
    p.touch()
    return p


def delete_note(project_name: str, filename: str) -> None:
    p = project_dir(project_name) / "notes" / filename
    p.unlink(missing_ok=True)


def pdf_path(project_name: str, relative_file: str) -> Path:
    return project_dir(project_name) / relative_file


# ── day plans ─────────────────────────────────────────────────────────────────

def _day_plan_file(d: date) -> Path:
    return _planning_dir() / f"{d.isoformat()}.yaml"


def _block_from_dict(d: dict) -> ScheduledBlock:
    return ScheduledBlock(
        task_id=d["task_id"],
        project=d["project"],
        start_time=d.get("start_time"),
        end_time=d.get("end_time"),
        notes=d.get("notes", ""),
    )


def _block_to_dict(b: ScheduledBlock) -> dict:
    return {
        "task_id": b.task_id,
        "project": b.project,
        "start_time": b.start_time,
        "end_time": b.end_time,
        "notes": b.notes,
    }


def load_day_plan(d: date) -> DayPlan:
    f = _day_plan_file(d)
    default_h = config.default_hours()
    if not f.exists():
        return DayPlan(date=d, available_hours=default_h)
    with open(f) as fh:
        data = yaml.safe_load(fh) or {}
    return DayPlan(
        date=_parse_date(data.get("date")) or d,
        available_hours=data.get("available_hours", default_h),
        ai_rationale=data.get("ai_rationale", ""),
        schedule=[_block_from_dict(b) for b in data.get("schedule", [])],
    )


def save_day_plan(plan: DayPlan) -> None:
    f = _day_plan_file(plan.date)
    f.parent.mkdir(parents=True, exist_ok=True)
    with open(f, "w") as fh:
        yaml.dump(
            {
                "date": plan.date.isoformat(),
                "available_hours": plan.available_hours,
                "ai_rationale": plan.ai_rationale,
                "schedule": [_block_to_dict(b) for b in plan.schedule],
            },
            fh,
            default_flow_style=False,
        )


# ── meetings ──────────────────────────────────────────────────────────────────

def _meetings_file() -> Path:
    return config.research_dir() / "meetings.yaml"


def _meeting_from_dict(d: dict) -> Meeting:
    return Meeting(
        id=d["id"],
        title=d["title"],
        start_time=d.get("start_time", "09:00"),
        end_time=d.get("end_time", "10:00"),
        location=d.get("location", ""),
        notes=d.get("notes", ""),
        recurrence=d.get("recurrence", "none"),
        days=d.get("days", []),
        date=_parse_date(d.get("date")),
        active=d.get("active", True),
    )


def _meeting_to_dict(m: Meeting) -> dict:
    return {
        "id": m.id,
        "title": m.title,
        "start_time": m.start_time,
        "end_time": m.end_time,
        "location": m.location,
        "notes": m.notes,
        "recurrence": m.recurrence,
        "days": m.days,
        "date": m.date.isoformat() if m.date else None,
        "active": m.active,
    }


def load_meetings() -> list[Meeting]:
    f = _meetings_file()
    if not f.exists():
        return []
    with open(f) as fh:
        data = yaml.safe_load(fh) or {}
    return [_meeting_from_dict(d) for d in data.get("meetings", [])]


def _write_meetings(meetings: list[Meeting]) -> None:
    f = _meetings_file()
    f.parent.mkdir(parents=True, exist_ok=True)
    with open(f, "w") as fh:
        yaml.dump({"meetings": [_meeting_to_dict(m) for m in meetings]}, fh, default_flow_style=False)


def save_meeting(meeting: Meeting) -> None:
    meetings = load_meetings()
    for i, m in enumerate(meetings):
        if m.id == meeting.id:
            meetings[i] = meeting
            _write_meetings(meetings)
            return
    meetings.append(meeting)
    _write_meetings(meetings)


def delete_meeting(meeting_id: str) -> None:
    meetings = [m for m in load_meetings() if m.id != meeting_id]
    _write_meetings(meetings)


def get_meetings_for_date(d: date) -> list[Meeting]:
    return sorted(
        [m for m in load_meetings() if m.occurs_on(d)],
        key=lambda m: m.start_time,
    )


def meetings_hours_for_date(d: date) -> float:
    return sum(m.duration_hours() for m in get_meetings_for_date(d))


# ─────────────────────────────────────────────────────────────────────────────

def is_task_in_plan(plan: DayPlan, task_id: str) -> bool:
    return any(b.task_id == task_id for b in plan.schedule)


def toggle_task_in_plan(plan: DayPlan, task_id: str, project_name: str) -> DayPlan:
    if is_task_in_plan(plan, task_id):
        plan.schedule = [b for b in plan.schedule if b.task_id != task_id]
    else:
        plan.schedule.append(ScheduledBlock(task_id=task_id, project=project_name))
    save_day_plan(plan)
    return plan
