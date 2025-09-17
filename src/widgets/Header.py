from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Label


class Header(Horizontal):
    def compose(self) -> ComposeResult:
        yield Label("[b]Grounder[/]", id="app-title")
