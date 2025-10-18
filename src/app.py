# nuitka-project: --mode=onefile
# nuitka-project: --windows-icon-from-ico={MAIN_DIRECTORY}/assets/grounder.ico
# nuitka-project: --include-data-files={MAIN_DIRECTORY}/grounder.css=grounder.css
# nuitka-project: --include-data-files={MAIN_DIRECTORY}/assets/trace.json=./assets/trace.json
# nuitka-project: --include-data-files={MAIN_DIRECTORY}/assets/type__1754.js=./assets/type__1754.js
# nuitka-project: --include-data-files={MAIN_DIRECTORY}/RequestLogger.py=./RequestLogger.py
# nuitka-project: --include-data-files={MAIN_DIRECTORY}/assets/mitmdump.exe=./assets/mitmdump.exe
# nuitka-project: --output-filename=Grounder.exe
# nuitka-project: --company-name=https://github.com/XIGUAjuice
# nuitka-project: --product-name=Grounder
# nuitka-project: --product-version=1.0.0
# nuitka-project: --copyright=https://github.com/XIGUAjuice
# %%
import logging
from datetime import datetime
from pathlib import Path

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Vertical

from AppLogPanel import AppLogHandler, AppLogPanel
from GroundInfoPanel import GroundInfoPanel
from GroundSelectScreen import GroundSelectScreen
from JSApi import JSApi
from Theme import default_theme
from UserInfoPanel import UserInfoPanel
from widgets.Header import Header

# %%
logger = logging.getLogger(__name__)
httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.ERROR)


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
        root_logger = logging.getLogger()
        log_widgt = self.query_one("#app-log")
        root_logger.addHandler(AppLogHandler(log_widgt))

        logger.info("加载 JSApi")
        self.js_api = JSApi()

        user_info_panel = self.query_one(UserInfoPanel)
        await user_info_panel.app_load_done()

        ground_info_panel = self.query_one(GroundInfoPanel)
        ground_info_panel.app_load_done()

    @on(UserInfoPanel.LoggedStatusChanged)
    @on(GroundInfoPanel.LoggedStatusChanged)
    @on(GroundSelectScreen.LoggedStatusChanged)
    def update_logged_status(
        self,
        message: (
            UserInfoPanel.LoggedStatusChanged
            | GroundInfoPanel.LoggedStatusChanged
            | GroundSelectScreen.LoggedStatusChanged
        ),
    ) -> None:
        user_info_panel = self.query_one(UserInfoPanel)
        user_info_panel.logged_status = message.logged_status
        if message.logged_status is False:
            self.js_api.clear_token()


def start():
    time_str = datetime.now().strftime("%Y_%m_%d_%H%M%S")
    log_path = Path(__file__).parent / "logs"
    log_path.mkdir(parents=True, exist_ok=True)
    log_file = log_path / f"Grounder_{time_str}.log"
    logging.basicConfig(
        handlers=[
            logging.FileHandler(log_file, mode="w", encoding="utf-8"),
        ],
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    app = Grounder()
    app.run()


if __name__ == "__main__":
    start()

# %%
