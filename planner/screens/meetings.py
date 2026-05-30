from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header

from planner import storage
from planner.models import Meeting


class MeetingsScreen(Screen):
    BINDINGS = [
        Binding("a", "add_meeting", "Add", show=True),
        Binding("e", "edit_meeting", "Edit", show=True),
        Binding("d", "delete_meeting", "Delete", show=True),
        Binding("r", "refresh", "Refresh", show=False),
        Binding("escape", "app.goto_dashboard", "Back", show=True),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield DataTable(id="meetings-table", cursor_type="row", zebra_stripes=True)
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Title", "Type", "Schedule", "Time", "Location")
        self._reload()

    def _reload(self) -> None:
        table = self.query_one(DataTable)
        table.clear()
        for m in storage.load_meetings():
            if not m.active:
                continue
            recurrence_label = {"none": "One-time", "daily": "Daily", "weekly": "Weekly"}.get(
                m.recurrence, m.recurrence
            )
            table.add_row(
                m.title,
                recurrence_label,
                m.days_label(),
                f"{m.start_time}–{m.end_time}",
                m.location or "—",
                key=m.id,
            )

    def action_refresh(self) -> None:
        self._reload()

    def action_add_meeting(self) -> None:
        from planner.modals.meeting_editor import MeetingEditorModal
        self.app.push_screen(MeetingEditorModal(), callback=self._on_saved)

    def _on_saved(self, meeting: Meeting | None) -> None:
        if meeting:
            storage.save_meeting(meeting)
            self._reload()
            self.notify(f"Meeting '{meeting.title}' saved.")

    def action_edit_meeting(self) -> None:
        meeting = self._selected_meeting()
        if meeting:
            from planner.modals.meeting_editor import MeetingEditorModal
            self.app.push_screen(MeetingEditorModal(meeting=meeting), callback=self._on_saved)

    def action_delete_meeting(self) -> None:
        meeting = self._selected_meeting()
        if meeting:
            from planner.modals.confirm import ConfirmModal
            self.app.push_screen(
                ConfirmModal(f"Delete meeting '{meeting.title}'?"),
                callback=lambda ok: self._on_delete_confirmed(ok, meeting.id),
            )

    def _on_delete_confirmed(self, ok: bool, meeting_id: str) -> None:
        if ok:
            storage.delete_meeting(meeting_id)
            self._reload()
            self.notify("Meeting deleted.", severity="warning")

    def _selected_meeting(self) -> Meeting | None:
        table = self.query_one(DataTable)
        if table.row_count == 0:
            return None
        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        if not row_key.value:
            return None
        for m in storage.load_meetings():
            if m.id == row_key.value:
                return m
        return None
