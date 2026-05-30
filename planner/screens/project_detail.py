from __future__ import annotations
import subprocess
import sys
from datetime import date
from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import (
    DataTable, Footer, Header, Label, ListView, ListItem, Static, TabbedContent, TabPane
)

from planner import config, storage
from planner.app import PAPER_STATUS_COLORS, PRIORITY_COLORS, STATUS_COLORS
from planner.models import Task, Paper


_FILTER_CYCLE_TASK = ["all", "open", "done"]
_FILTER_CYCLE_PAPER = ["all", "unread", "reading", "read"]


class ProjectDetailScreen(Screen):
    BINDINGS = [
        Binding("1", "show_tab('tab-tasks')", "Tasks", show=False),
        Binding("2", "show_tab('tab-papers')", "Papers", show=False),
        Binding("3", "show_tab('tab-notes')", "Notes", show=False),
        Binding("a", "add_item", "Add", show=False),
        Binding("e", "edit_item", "Edit", show=False),
        Binding("d", "delete_item", "Delete", show=False),
        Binding("space", "toggle_item", "Toggle", show=False),
        Binding("o", "open_file", "Open", show=False),
        Binding("f", "cycle_filter", "Filter", show=False),
        Binding("escape", "back", "Back", show=True),
    ]

    def __init__(self, project_name: str) -> None:
        super().__init__()
        self._project_name = project_name
        self._task_filter = "all"
        self._paper_filter = "all"

    # ── layout ────────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with TabbedContent(id="detail-tabs"):
            with TabPane("Tasks", id="tab-tasks"):
                yield DataTable(
                    id="tasks-table",
                    cursor_type="row",
                    zebra_stripes=True,
                )
            with TabPane("Papers", id="tab-papers"):
                yield DataTable(
                    id="papers-table",
                    cursor_type="row",
                    zebra_stripes=True,
                )
            with TabPane("Notes", id="tab-notes"):
                yield ListView(id="notes-list")
        yield Static("", id="detail-footer")
        yield Footer()

    def on_mount(self) -> None:
        self.sub_title = self._project_name

        tasks_table = self.query_one("#tasks-table", DataTable)
        tasks_table.add_columns("Title", "Priority", "Deadline", "Est.", "Status")

        papers_table = self.query_one("#papers-table", DataTable)
        papers_table.add_columns("Title", "Authors", "Year", "Venue", "Status")

        self._reload_tasks()
        self._reload_papers()
        self._reload_notes()

    # ── data loading ──────────────────────────────────────────────────────────

    def _reload_tasks(self) -> None:
        table = self.query_one("#tasks-table", DataTable)
        table.clear()
        tasks = storage.load_tasks(self._project_name)
        shown = [t for t in tasks if self._task_filter == "all" or t.status == self._task_filter]
        for t in shown:
            deadline_str = t.deadline.isoformat() if t.deadline else "—"
            days = t.deadline_days()
            if days is not None and t.is_open():
                if days < 0:
                    deadline_str = f"[red]{deadline_str}[/red]"
                elif days <= 3:
                    deadline_str = f"[yellow]{deadline_str}[/yellow]"

            est_str = f"{t.estimate_hours}h" if t.estimate_hours else "—"
            color = PRIORITY_COLORS.get(t.priority, "white")
            status_color = STATUS_COLORS.get(t.status, "white")
            table.add_row(
                f"[{color}]{t.title}[/{color}]",
                f"[{color}]{t.priority}[/{color}]",
                deadline_str,
                est_str,
                f"[{status_color}]{t.status}[/{status_color}]",
                key=t.id,
            )
        self._update_footer()

    def _reload_papers(self) -> None:
        table = self.query_one("#papers-table", DataTable)
        table.clear()
        papers = storage.load_papers(self._project_name)
        shown = [p for p in papers if self._paper_filter == "all" or p.status == self._paper_filter]
        for p in shown:
            color = PAPER_STATUS_COLORS.get(p.status, "white")
            table.add_row(
                f"[{color}]{p.title}[/{color}]",
                p.authors or "—",
                str(p.year) if p.year else "—",
                p.venue or "—",
                f"[{color}]{p.status}[/{color}]",
                key=p.id,
            )
        self._update_footer()

    def _reload_notes(self) -> None:
        lv = self.query_one("#notes-list", ListView)
        lv.clear()
        for path in storage.list_notes(self._project_name):
            lv.append(ListItem(Label(path.name), name=path.name))
        self._update_footer()

    def _update_footer(self) -> None:
        tab = self._active_tab()
        if tab == "tasks":
            tasks = storage.load_tasks(self._project_name)
            open_c = sum(1 for t in tasks if t.is_open())
            self.query_one("#detail-footer", Static).update(
                f" [dim]1[/dim] Tasks  [dim]2[/dim] Papers  [dim]3[/dim] Notes"
                f"   Filter: {self._task_filter}   Open: {open_c}/{len(tasks)}"
                "   [dim]a[/dim]dd  [dim]e[/dim]dit  [dim]spc[/dim] toggle  [dim]d[/dim]el  [dim]f[/dim]ilter"
            )
        elif tab == "papers":
            papers = storage.load_papers(self._project_name)
            self.query_one("#detail-footer", Static).update(
                f" [dim]1[/dim] Tasks  [dim]2[/dim] Papers  [dim]3[/dim] Notes"
                f"   Filter: {self._paper_filter}   Total: {len(papers)}"
                "   [dim]a[/dim]dd  [dim]e[/dim]dit  [dim]o[/dim]pen PDF  [dim]d[/dim]el  [dim]f[/dim]ilter"
            )
        else:
            notes = storage.list_notes(self._project_name)
            self.query_one("#detail-footer", Static).update(
                f" [dim]1[/dim] Tasks  [dim]2[/dim] Papers  [dim]3[/dim] Notes"
                f"   Notes: {len(notes)}"
                "   [dim]a[/dim]dd  [dim]enter[/dim] open  [dim]d[/dim]el"
            )

    def _active_tab(self) -> str:
        tc = self.query_one(TabbedContent)
        active = tc.active
        if active == "tab-tasks":
            return "tasks"
        if active == "tab-papers":
            return "papers"
        return "notes"

    def on_tabbed_content_tab_activated(self, event) -> None:
        self._update_footer()

    # ── actions ───────────────────────────────────────────────────────────────

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_show_tab(self, tab_id: str) -> None:
        self.query_one(TabbedContent).active = tab_id
        self._update_footer()

    def action_cycle_filter(self) -> None:
        tab = self._active_tab()
        if tab == "tasks":
            idx = _FILTER_CYCLE_TASK.index(self._task_filter)
            self._task_filter = _FILTER_CYCLE_TASK[(idx + 1) % len(_FILTER_CYCLE_TASK)]
            self._reload_tasks()
        elif tab == "papers":
            idx = _FILTER_CYCLE_PAPER.index(self._paper_filter)
            self._paper_filter = _FILTER_CYCLE_PAPER[(idx + 1) % len(_FILTER_CYCLE_PAPER)]
            self._reload_papers()

    # ── Tasks actions ─────────────────────────────────────────────────────────

    def action_add_item(self) -> None:
        tab = self._active_tab()
        if tab == "tasks":
            from planner.modals.task_editor import TaskEditorModal
            self.app.push_screen(
                TaskEditorModal(project_name=self._project_name),
                callback=self._on_task_saved,
            )
        elif tab == "papers":
            from planner.modals.paper_editor import PaperEditorModal
            self.app.push_screen(PaperEditorModal(), callback=self._on_paper_saved)
        else:
            from planner.modals.input_modal import InputModal
            self.app.push_screen(
                InputModal("New Note", "Filename (without extension):"),
                callback=self._on_note_created,
            )

    def _on_task_saved(self, result) -> None:
        if result is None:
            return
        task, project = result
        storage.save_task(project, task)
        if project == self._project_name:
            self._reload_tasks()
        self.notify(f"Task saved.")

    def action_edit_item(self) -> None:
        tab = self._active_tab()
        if tab == "tasks":
            task = self._selected_task()
            if task:
                from planner.modals.task_editor import TaskEditorModal
                self.app.push_screen(
                    TaskEditorModal(task=task, project_name=self._project_name),
                    callback=self._on_task_saved,
                )
        elif tab == "papers":
            paper = self._selected_paper()
            if paper:
                from planner.modals.paper_editor import PaperEditorModal
                self.app.push_screen(PaperEditorModal(paper=paper), callback=self._on_paper_saved)

    def action_toggle_item(self) -> None:
        if self._active_tab() != "tasks":
            return
        task = self._selected_task()
        if task:
            if task.status == "done":
                task.status = "open"
                task.completed = None
            else:
                task.status = "done"
                task.completed = date.today()
            storage.save_task(self._project_name, task)
            self._reload_tasks()

    def action_delete_item(self) -> None:
        tab = self._active_tab()
        if tab == "tasks":
            task = self._selected_task()
            if task:
                from planner.modals.confirm import ConfirmModal
                self.app.push_screen(
                    ConfirmModal(f"Delete task '{task.title}'?"),
                    callback=lambda ok: self._do_delete_task(ok, task.id),
                )
        elif tab == "papers":
            paper = self._selected_paper()
            if paper:
                from planner.modals.confirm import ConfirmModal
                self.app.push_screen(
                    ConfirmModal(f"Delete paper '{paper.title}'?"),
                    callback=lambda ok: self._do_delete_paper(ok, paper.id),
                )
        else:
            name = self._selected_note_name()
            if name:
                from planner.modals.confirm import ConfirmModal
                self.app.push_screen(
                    ConfirmModal(f"Delete note '{name}'?"),
                    callback=lambda ok: self._do_delete_note(ok, name),
                )

    def _do_delete_task(self, ok: bool, task_id: str) -> None:
        if ok:
            storage.delete_task(self._project_name, task_id)
            self._reload_tasks()
            self.notify("Task deleted.", severity="warning")

    def _do_delete_paper(self, ok: bool, paper_id: str) -> None:
        if ok:
            storage.delete_paper(self._project_name, paper_id)
            self._reload_papers()
            self.notify("Paper deleted.", severity="warning")

    def _do_delete_note(self, ok: bool, name: str) -> None:
        if ok:
            storage.delete_note(self._project_name, name)
            self._reload_notes()
            self.notify("Note deleted.", severity="warning")

    # ── Papers / Notes actions ────────────────────────────────────────────────

    def _on_paper_saved(self, paper: Paper | None) -> None:
        if paper:
            storage.save_paper(self._project_name, paper)
            self._reload_papers()
            self.notify("Paper saved.")

    def action_open_file(self) -> None:
        tab = self._active_tab()
        if tab == "papers":
            paper = self._selected_paper()
            if paper and paper.file:
                full_path = storage.pdf_path(self._project_name, paper.file)
                self._open_path(full_path)
            elif paper:
                self.notify("No file attached to this paper.", severity="warning")
        elif tab == "notes":
            name = self._selected_note_name()
            if name:
                path = storage.project_dir(self._project_name) / "notes" / name
                self._open_in_editor(path)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if self._active_tab() == "notes":
            name = event.item.name
            if name:
                path = storage.project_dir(self._project_name) / "notes" / name
                self._open_in_editor(path)

    def _on_note_created(self, filename: str | None) -> None:
        if filename and filename.strip():
            path = storage.create_note(self._project_name, filename.strip())
            self._reload_notes()
            self._open_in_editor(path)

    def _open_in_editor(self, path: Path) -> None:
        editor = config.editor()
        try:
            with self.app.suspend():
                subprocess.run([editor, str(path)])
        except Exception as e:
            self.notify(f"Could not open editor: {e}", severity="error")

    def _open_path(self, path: Path) -> None:
        try:
            if sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except Exception as e:
            self.notify(f"Could not open file: {e}", severity="error")

    # ── selection helpers ─────────────────────────────────────────────────────

    def _selected_task(self) -> Task | None:
        table = self.query_one("#tasks-table", DataTable)
        if table.row_count == 0:
            return None
        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        if not row_key.value:
            return None
        for t in storage.load_tasks(self._project_name):
            if t.id == row_key.value:
                return t
        return None

    def _selected_paper(self) -> Paper | None:
        table = self.query_one("#papers-table", DataTable)
        if table.row_count == 0:
            return None
        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        if not row_key.value:
            return None
        for p in storage.load_papers(self._project_name):
            if p.id == row_key.value:
                return p
        return None

    def _selected_note_name(self) -> str | None:
        lv = self.query_one("#notes-list", ListView)
        if lv.highlighted_child is None:
            return None
        return lv.highlighted_child.name
