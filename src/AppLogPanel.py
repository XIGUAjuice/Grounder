import logging

from rich.logging import RichHandler
from textual.widgets import RichLog

logger = logging.getLogger(__name__)


class AppLogPanel(RichLog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file = False
        self.border_title = "日志"

    def print(self, content):
        self.write(content)


class AppLogHandler(RichHandler):
    def __init__(self, widget: AppLogPanel, *args, **kwargs):
        super().__init__(
            console=widget,
            rich_tracebacks=False,
            level=logging.INFO,
            show_level=False,
            show_path=False,
            *args,
            **kwargs
        )
        formatter = logging.Formatter("%(message)s")
        self.setFormatter(formatter)
