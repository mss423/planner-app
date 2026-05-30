from __future__ import annotations
from datetime import date
from typing import Optional

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Input, Label, Select, Static

from planner.models import Meeting, _WEEKDAY_MAP, _WEEKDAY_NAMES


class MeetingEditorModal(ModalScreen[Meeting | None]):
    BINDINGS = [
        Binding("ctrl+s", "save", "Save"),
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, meeting: Optional[Meeting] = None) -> None:
        super().__init__()
        self._meeting = meeting

    def compose(self) -> ComposeResult:
        m = self._meeting
        recurrence = m.recurrence if m else "none"

        with Container(classes="modal-container"):
            yield Label("Edit Meeting" if m else "New Meeting", classes="modal-title")
            with VerticalScroll(classes="modal-body"):
                yield Label("Title *")
                yield Input(value=m.title if m else "", id="mtg-title", placeholder="Meeting title")

                yield Label("Start time (HH:MM) *")
                yield Input(value=m.start_time if m else "09:00", id="mtg-start", placeholder="09:00")

                yield Label("End time (HH:MM) *")
                yield Input(value=m.end_time if m else "10:00", id="mtg-end", placeholder="10:00")

                yield Label("Location")
                yield Input(value=m.location if m else "", id="mtg-location", placeholder="Room / Zoom link")

                yield Label("Recurrence")
                yield Select(
                    [("One-time", "none"), ("Weekly", "weekly"), ("Daily", "daily")],
                    value=recurrence,
                    id="mtg-recurrence",
                )

                # one-time date field
                yield Label("Date (YYYY-MM-DD)", id="lbl-date")
                yield Input(
                    value=m.date.isoformat() if (m and m.date) else date.today().isoformat(),
                    id="mtg-date",
                    placeholder="2026-06-03",
                )

                # weekly day checkboxes
                yield Static("[bold]Repeat on:[/bold]", id="lbl-days")
                with Horizontal(id="days-row"):
                    active_days = m.days if m else []
                    for i, name in enumerate(_WEEKDAY_NAMES[:5]):  # Mon–Fri
                        yield Checkbox(name, value=(i in active_days), id=f"day-{i}")
                    for i, name in enumerate(_WEEKDAY_NAMES[5:], start=5):  # Sat–Sun
                        yield Checkbox(name, value=(i in active_days), id=f"day-{i}")

                yield Label("Notes")
                yield Input(value=m.notes if m else "", id="mtg-notes", placeholder="Optional notes")

            with Horizontal(classes="modal-buttons"):
                yield Button("Cancel", variant="default", id="btn-cancel")
                yield Button("Save", variant="primary", id="btn-save")

    def on_mount(self) -> None:
        self.query_one("#mtg-title", Input).focus()
        self._update_recurrence_fields()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "mtg-recurrence":
            self._update_recurrence_fields()

    def _update_recurrence_fields(self) -> None:
        sel = self.query_one("#mtg-recurrence", Select)
        recurrence = sel.value if sel.value != Select.BLANK else "none"
        self.query_one("#lbl-date").display = (recurrence == "none")
        self.query_one("#mtg-date").display = (recurrence == "none")
        self.query_one("#lbl-days").display = (recurrence == "weekly")
        self.query_one("#days-row").display = (recurrence == "weekly")

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
        title = self.query_one("#mtg-title", Input).value.strip()
        if not title:
            self.notify("Title is required.", severity="error")
            return

        start = self.query_one("#mtg-start", Input).value.strip()
        end = self.query_one("#mtg-end", Input).value.strip()
        for label, val in [("Start time", start), ("End time", end)]:
            if not val:
                self.notify(f"{label} is required.", severity="error")
                return
            parts = val.split(":")
            if len(parts) != 2 or not all(p.isdigit() for p in parts):
                self.notify(f"{label} must be HH:MM format.", severity="error")
                return

        sel = self.query_one("#mtg-recurrence", Select)
        recurrence = sel.value if sel.value != Select.BLANK else "none"

        mtg_date = None
        if recurrence == "none":
            date_str = self.query_one("#mtg-date", Input).value.strip()
            try:
                mtg_date = date.fromisoformat(date_str)
            except ValueError:
                self.notify("Invalid date format. Use YYYY-MM-DD.", severity="error")
                return

        days = []
        if recurrence == "weekly":
            for i in range(7):
                cb = self.query_one(f"#day-{i}", Checkbox)
                if cb.value:
                    days.append(i)
            if not days:
                self.notify("Select at least one day for weekly recurrence.", severity="error")
                return

        location = self.query_one("#mtg-location", Input).value.strip()
        notes = self.query_one("#mtg-notes", Input).value.strip()

        if self._meeting:
            self._meeting.title = title
            self._meeting.start_time = start
            self._meeting.end_time = end
            self._meeting.location = location
            self._meeting.notes = notes
            self._meeting.recurrence = recurrence
            self._meeting.days = days
            self._meeting.date = mtg_date
            self.dismiss(self._meeting)
        else:
            self.dismiss(Meeting(
                title=title,
                start_time=start,
                end_time=end,
                location=location,
                notes=notes,
                recurrence=recurrence,
                days=days,
                date=mtg_date,
            ))
