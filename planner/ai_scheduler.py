from __future__ import annotations
import json
import os
from datetime import date
from typing import Optional

from planner.models import DayPlan, Meeting, ScheduledBlock, Task


def build_prompt(
    plan_date: date,
    tasks: list[tuple[Task, str]],   # (task, project_name)
    available_hours: float,
    meetings: list[Meeting] | None = None,
    constraints: str = "",
    start_time: str = "09:00",
) -> str:
    task_list = []
    for t, pname in tasks:
        task_list.append({
            "id": t.id,
            "title": t.title,
            "project": pname,
            "priority": t.priority,
            "deadline_days": t.deadline_days(),
            "estimate_hours": t.estimate_hours,
        })

    meetings_section = ""
    if meetings:
        mtg_list = [
            {"title": m.title, "start": m.start_time, "end": m.end_time, "location": m.location}
            for m in meetings
        ]
        mtg_hours = sum(m.duration_hours() for m in meetings)
        meetings_section = (
            f"\nFixed meetings today (DO NOT schedule tasks during these blocks):\n"
            f"{json.dumps(mtg_list, indent=2)}\n"
            f"Total meeting time: {mtg_hours:.1f}h  →  Free for tasks: {max(0.0, available_hours - mtg_hours):.1f}h\n"
        )

    weekday = plan_date.strftime("%A")
    prompt = (
        f"Today is {plan_date.isoformat()} ({weekday}).\n"
        f"Total available working hours: {available_hours}\n"
        f"Preferred start time: {start_time}\n"
        f"User constraints: {constraints or 'none'}\n"
        + meetings_section +
        f"\nTasks to schedule:\n{json.dumps(task_list, indent=2)}\n\n"
        "Create a time-blocked schedule. Avoid the meeting blocks above.\n"
        "For tasks without an estimate, make a reasonable guess.\n"
        "Prioritize by: deadlines first, then priority level, then project balance.\n\n"
        "Return ONLY valid JSON in this exact format:\n"
        "{\n"
        '  "rationale": "short paragraph explaining prioritization decisions",\n'
        '  "schedule": [\n'
        '    {"task_id": "...", "start": "HH:MM", "end": "HH:MM", "notes": "optional tip"}\n'
        "  ],\n"
        '  "unscheduled": ["task_id", ...],\n'
        '  "unscheduled_reason": "why these were left out, or empty string"\n'
        "}"
    )
    return prompt


def schedule(
    plan_date: date,
    tasks: list[tuple[Task, str]],
    available_hours: float,
    meetings: list[Meeting] | None = None,
    constraints: str = "",
    start_time: str = "09:00",
) -> dict:
    """Call Claude synchronously and return parsed JSON result."""
    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY environment variable not set.")

    client = anthropic.Anthropic(api_key=api_key)
    prompt = build_prompt(plan_date, tasks, available_hours, meetings, constraints, start_time)

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system="You are a research scheduling assistant. Return only valid JSON with no markdown fences.",
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    # strip accidental markdown fences
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    return json.loads(raw)


def apply_schedule(plan: DayPlan, result: dict, tasks: list[tuple[Task, str]]) -> DayPlan:
    """Update plan.schedule with time blocks from the AI result."""
    task_map = {t.id: (t, pname) for t, pname in tasks}
    new_schedule = []
    for entry in result.get("schedule", []):
        task_id = entry.get("task_id")
        if task_id and task_id in task_map:
            _, pname = task_map[task_id]
            new_schedule.append(ScheduledBlock(
                task_id=task_id,
                project=pname,
                start_time=entry.get("start"),
                end_time=entry.get("end"),
                notes=entry.get("notes", ""),
            ))
    # keep unscheduled tasks in plan without time blocks
    scheduled_ids = {b.task_id for b in new_schedule}
    for block in plan.schedule:
        if block.task_id not in scheduled_ids:
            new_schedule.append(block)

    plan.schedule = new_schedule
    plan.ai_rationale = result.get("rationale", "")
    return plan
