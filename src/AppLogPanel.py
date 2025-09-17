from rich.logging import RichHandler
from textual.widgets import RichLog


class AppLogPanel(RichLog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file = False
        self.border_title = "日志"

    def print(self, content):
        self.write(content)


class AppLogHandler(RichHandler):
    def __init__(self, widget: AppLogPanel, *args, **kwargs):
        super().__init__(console=widget, *args, **kwargs)
