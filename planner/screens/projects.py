from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header

from planner import storage


class ProjectsScreen(Screen):
    BINDINGS = [
        Binding("a", "add_project", "Add", show=True),
        Binding("D", "delete_project", "Delete", show=True),
        Binding("r", "refresh", "Refresh", show=False),
        Binding("escape", "app.goto_dashboard", "Back", show=True),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield DataTable(id="projects-table", cursor_type="row", zebra_stripes=True)
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Project", "Open Tasks", "Papers", "Notes")
        self._reload()

    def _reload(self) -> None:
        table = self.query_one(DataTable)
        table.clear()
        for name in storage.list_project_names():
            proj = storage.load_project(name)
            notes_count = len(storage.list_notes(name))
            table.add_row(
                name,
                str(len(proj.open_tasks())),
                str(len(proj.papers)),
                str(notes_count),
                key=name,
            )

    def action_refresh(self) -> None:
        self._reload()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.row_key.value:
            from planner.screens.project_detail import ProjectDetailScreen
            self.app.push_screen(ProjectDetailScreen(event.row_key.value))

    def action_add_project(self) -> None:
        from planner.modals.input_modal import InputModal
        self.app.push_screen(
            InputModal("New Project", "Project name:"),
            callback=self._on_project_created,
        )

    def _on_project_created(self, name: str | None) -> None:
        if name and name.strip():
            name = name.strip()
            storage.create_project(name)
            self._reload()
            self.notify(f"Project '{name}' created.")

    def action_delete_project(self) -> None:
        table = self.query_one(DataTable)
        if table.row_count == 0:
            return
        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        if row_key.value:
            from planner.modals.confirm import ConfirmModal
            self.app.push_screen(
                ConfirmModal(f"Delete project '{row_key.value}'? This cannot be undone."),
                callback=lambda ok: self._on_delete_confirmed(ok, row_key.value),
            )

    def _on_delete_confirmed(self, ok: bool, name: str) -> None:
        if ok:
            storage.delete_project(name)
            self._reload()
            self.notify(f"Project '{name}' deleted.", severity="warning")
