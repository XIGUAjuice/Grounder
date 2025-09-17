# %%
import logging
from datetime import datetime
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Vertical

from AppLogPanel import AppLogHandler, AppLogPanel
from GroundInfoPanel import GroundInfoPanel
from JSApi import JSApi
from Theme import default_theme
from UserInfoPanel import UserInfoPanel
from widgets.Header import Header

# %%
logger = logging.getLogger(__name__)


class Grounder(App):
    CSS_PATH = "grounder.css"

    def compose(self) -> ComposeResult:
        with Vertical(id="main"):
            yield Header()
            yield UserInfoPanel(classes="panel")
            yield GroundInfoPanel(classes="panel")
            yield AppLogPanel(id="app-log", classes="panel")

    def on_mount(self) -> None:
        self.register_theme(default_theme)
        self.theme = "default"

    async def on_ready(self) -> None:
        time_str = datetime.now().strftime("%Y_%m_%d_%H%M%S")
        log_path = Path(__file__).parents[1] / "logs"
        log_path.mkdir(parents=True, exist_ok=True)
        log_file = log_path / f"Grounder_{time_str}.log"
        log_widgt = self.query_one("#app-log")
        logging.basicConfig(
            handlers=[
                logging.FileHandler(log_file, mode="w", encoding="utf-8"),
                AppLogHandler(log_widgt, rich_tracebacks=True, level=logging.INFO),
            ],
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        logger.info("加载 JSApi")
        self.js_api = JSApi()

        user_info_panel = self.query_one(UserInfoPanel)
        await user_info_panel.app_load_done()

        ground_info_panel = self.query_one(GroundInfoPanel)
        ground_info_panel.app_load_done()


if __name__ == "__main__":
    app = Grounder()
    app.run()

# %%
