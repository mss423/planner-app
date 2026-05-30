from __future__ import annotations
from typing import Optional

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select, TextArea

from planner.models import Paper


class PaperEditorModal(ModalScreen[Paper | None]):
    BINDINGS = [
        Binding("ctrl+s", "save", "Save"),
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, paper: Optional[Paper] = None) -> None:
        super().__init__()
        self._paper = paper

    def compose(self) -> ComposeResult:
        p = self._paper
        with Container(classes="modal-container"):
            yield Label("Edit Paper" if p else "Add Paper", classes="modal-title")
            with VerticalScroll(classes="modal-body"):
                yield Label("Title *")
                yield Input(value=p.title if p else "", id="paper-title", placeholder="Paper title")

                yield Label("Authors")
                yield Input(value=p.authors if p else "", id="paper-authors", placeholder="e.g. Vaswani et al.")

                yield Label("Year")
                yield Input(value=str(p.year) if (p and p.year) else "", id="paper-year", placeholder="e.g. 2017")

                yield Label("Venue")
                yield Input(value=p.venue if p else "", id="paper-venue", placeholder="e.g. NeurIPS 2017")

                yield Label("PDF file path (relative to project dir)")
                yield Input(
                    value=p.file if (p and p.file) else "",
                    id="paper-file",
                    placeholder="papers/filename.pdf",
                )

                yield Label("Status")
                yield Select(
                    [("Unread", "unread"), ("Reading", "reading"), ("Read", "read")],
                    value=p.status if p else "unread",
                    id="paper-status",
                )

                yield Label("Abstract / Notes")
                yield TextArea(text=p.abstract if p else "", id="paper-abstract")

            with Horizontal(classes="modal-buttons"):
                yield Button("Cancel", variant="default", id="btn-cancel")
                yield Button("Save", variant="primary", id="btn-save")

    def on_mount(self) -> None:
        self.query_one("#paper-title", Input).focus()

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
        title = self.query_one("#paper-title", Input).value.strip()
        if not title:
            self.notify("Title is required.", severity="error")
            return

        year_str = self.query_one("#paper-year", Input).value.strip()
        year = None
        if year_str:
            try:
                year = int(year_str)
            except ValueError:
                self.notify("Year must be a number.", severity="error")
                return

        status_sel = self.query_one("#paper-status", Select)
        status = status_sel.value if status_sel.value != Select.BLANK else "unread"

        if self._paper:
            self._paper.title = title
            self._paper.authors = self.query_one("#paper-authors", Input).value.strip()
            self._paper.year = year
            self._paper.venue = self.query_one("#paper-venue", Input).value.strip()
            self._paper.file = self.query_one("#paper-file", Input).value.strip() or None
            self._paper.status = status
            self._paper.abstract = self.query_one("#paper-abstract", TextArea).text
            self.dismiss(self._paper)
        else:
            self.dismiss(Paper(
                title=title,
                authors=self.query_one("#paper-authors", Input).value.strip(),
                year=year,
                venue=self.query_one("#paper-venue", Input).value.strip(),
                file=self.query_one("#paper-file", Input).value.strip() or None,
                status=status,
                abstract=self.query_one("#paper-abstract", TextArea).text,
            ))
