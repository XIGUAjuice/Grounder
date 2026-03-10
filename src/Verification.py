# %%
import json
import logging
from pathlib import Path

import zendriver as zd

# %%
logger = logging.getLogger(__name__)


class Verification:
    def __init__(self, trace_path):
        with open(trace_path, "r") as f:
            trace = json.load(f)["trace"]
        trace = [
            (x2 - x1, y2 - y1) for (x1, y1), (x2, y2) in zip(trace[:-1], trace[1:])
        ]
        self.trace = trace

    async def move_slider(self, slider: zd.Element):
        for dx, dy in self.trace:
            await slider.mouse_drag((dx, dy), relative=True, steps=3)

    async def start_browser(self):
        self.browser = await zd.start(headless=True)

    async def solve(self, html_path):
        page = await self.browser.get(f"file://{Path(html_path).resolve()}")
        slider = await page.find("div[id='aliyunCaptcha-sliding-slider']")
        await self.move_slider(slider)
        form = (await page.xpath("//form[@action]"))[0]
        return form.attrs["action"]


if __name__ == "__main__":
    assets_path = Path(__file__).parent / "assets"
    varification = Verification(assets_path / "trace.json")
    varification.start_browser()
    print(varification.solve(assets_path / "v2.html"))
