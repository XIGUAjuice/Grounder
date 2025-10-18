# %%
import json
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


# %%
class Verification:
    def __init__(self, trace_path):
        options = webdriver.ChromeOptions()
        service = webdriver.ChromeService(service_args=["--enable-chrome-logs"])
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        self.driver = webdriver.Chrome(options=options, service=service)

        with open(trace_path, "r") as f:
            trace = json.load(f)["trace"]
        trace = [
            (x2 - x1, y2 - y1) for (x1, y1), (x2, y2) in zip(trace[:-1], trace[1:])
        ]
        self.trace = trace

    def move_slider(self, slider):
        ActionChains(self.driver, 100).click_and_hold(slider).perform()
        for dx, dy in self.trace:
            ActionChains(self.driver, 0).move_by_offset(dx, dy).perform()
        ActionChains(self.driver, 100).release().perform()

    def solve(self, html_path):
        html_path = f"file://{Path(html_path).resolve()}"
        self.driver.get(html_path)
        wait = WebDriverWait(self.driver, timeout=10)
        slider = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".btn_slide"))
        )
        self.move_slider(slider)
        form = wait.until(EC.presence_of_element_located((By.XPATH, "//form[@action]")))
        return form.get_attribute("action")


if __name__ == "__main__":
    assets_path = Path(__file__).parent / "assets"
    varification = Verification(assets_path / "trace.json")
    print(varification.solve(assets_path / "v2.html"))
