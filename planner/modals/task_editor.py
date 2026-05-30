from __future__ import annotations
from datetime import date
from typing import Optional

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select, TextArea

from planner.models import Task
from planner import storage


class TaskEditorModal(ModalScreen[Task | None]):
    BINDINGS = [
        Binding("ctrl+s", "save", "Save"),
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, task: Optional[Task] = None, project_name: Optional[str] = None) -> None:
        super().__init__()
        self._edit_task = task
        self._project_name = project_name

    def compose(self) -> ComposeResult:
        t = self._edit_task
        projects = storage.list_project_names()
        project_options = [(name, name) for name in projects]

        with Container(classes="modal-container"):
            yield Label("Edit Task" if t else "New Task", classes="modal-title")
            with VerticalScroll(classes="modal-body"):
                yield Label("Title *")
                yield Input(value=t.title if t else "", id="task-title", placeholder="Task title")

                yield Label("Project *")
                yield Select(
                    project_options,
                    value=self._project_name or (projects[0] if projects else None),
                    id="task-project",
                )

                yield Label("Priority")
                yield Select(
                    [("High", "high"), ("Medium", "medium"), ("Low", "low")],
                    value=t.priority if t else "medium",
                    id="task-priority",
                )

                yield Label("Deadline (YYYY-MM-DD)")
                yield Input(
                    value=t.deadline.isoformat() if (t and t.deadline) else "",
                    id="task-deadline",
                    placeholder="e.g. 2026-06-30",
                )

                yield Label("Estimate (hours)")
                yield Input(
                    value=str(t.estimate_hours) if (t and t.estimate_hours) else "",
                    id="task-estimate",
                    placeholder="e.g. 2.5",
                )

                yield Label("Notes")
                yield TextArea(text=t.notes if t else "", id="task-notes")

            with Horizontal(classes="modal-buttons"):
                yield Button("Cancel", variant="default", id="btn-cancel")
                yield Button("Save", variant="primary", id="btn-save")

    def on_mount(self) -> None:
        self.query_one("#task-title", Input).focus()

    def action_save(self) -> None:
        self._do_save()

    def action_cancel(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed, "#btn-save")
    def handle_save(self) -> None:
        self._do_save()

    @on(Button.Pressed, "#btn-cancel")
    def handle_cancel(self) -> None:
        self.dismiss(None)

    def _do_save(self) -> None:
        title = self.query_one("#task-title", Input).value.strip()
        if not title:
            self.notify("Title is required.", severity="error")
            return

        project_sel = self.query_one("#task-project", Select)
        project = project_sel.value if project_sel.value != Select.BLANK else None
        if not project:
            self.notify("Project is required.", severity="error")
            return

        priority_sel = self.query_one("#task-priority", Select)
        priority = priority_sel.value if priority_sel.value != Select.BLANK else "medium"

        deadline_str = self.query_one("#task-deadline", Input).value.strip()
        deadline = None
        if deadline_str:
            try:
                deadline = date.fromisoformat(deadline_str)
            except ValueError:
                self.notify("Invalid date format. Use YYYY-MM-DD.", severity="error")
                return

        estimate_str = self.query_one("#task-estimate", Input).value.strip()
        estimate = None
        if estimate_str:
            try:
                estimate = float(estimate_str)
            except ValueError:
                self.notify("Estimate must be a number.", severity="error")
                return

        notes = self.query_one("#task-notes", TextArea).text

        if self._edit_task:
            self._edit_task.title = title
            self._edit_task.priority = priority
            self._edit_task.deadline = deadline
            self._edit_task.estimate_hours = estimate
            self._edit_task.notes = notes
            result = (self._edit_task, project)
        else:
            result = (Task(
                title=title,
                priority=priority,
                deadline=deadline,
                estimate_hours=estimate,
                notes=notes,
            ), project)

        self.dismiss(result)
