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
import sys
from datetime import datetime
from pathlib import Path
from app import Grounder

logger = logging.getLogger(__name__)


def config_logger():
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


if __name__ == "__main__":
    try:
        config_logger()
        app = Grounder()
        app.run()
        return_code = app.return_code
    except Exception as e:
        logger.exception("发生未知错误，程序终止")
        return_code = 1
    finally:
        selenium_driver = app.js_api.verification.driver
        if selenium_driver:
            selenium_driver.quit()
        sys.exit(return_code)
