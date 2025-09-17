import json
import logging
from datetime import datetime

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Middle, ScrollableContainer
from textual.widgets import Button, Label, Select

from GroundSelectScreen import GroundSelectScreen
from JSApi import JSApi
from widgets.TimeSelect import TimeSelect

logger = logging.getLogger(__name__)


class GroundInfoPanel(ScrollableContainer):

    def __init__(
        self,
        *children,
        name=None,
        id=None,
        classes=None,
        disabled=False,
        can_focus=None,
        can_focus_children=None,
        can_maximize=None,
    ):
        super().__init__(
            *children,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
            can_focus=can_focus,
            can_focus_children=can_focus_children,
            can_maximize=can_maximize,
        )

    def compose(self) -> ComposeResult:
        self.border_title = "场馆预定"
        with Horizontal():
            yield Middle(Label("[b]选择运动：[/]", id="ground-sports-label"))
            yield Middle(
                Select(
                    [("羽毛球", "羽毛球")],
                    prompt="请选择运动项目",
                    id="ground-sports-select",
                )
            )
            yield Middle(Label("[b]选择场馆：[/]", id="ground-venue-label"))
            yield Middle(Select([], prompt="请选择场馆", id="ground-venue-select"))
            yield Middle(Button("选择场地", id="ground-button"))

        with Horizontal():
            yield Middle(Label("开抢时间: "))
            yield Middle(TimeSelect(id="time-select"))
            yield Middle(Button("开始预定", id="order-button"))

    def app_load_done(self) -> None:
        self.js_api: JSApi = self.app.js_api

    @work
    @on(Button.Pressed, "#ground-button")
    async def show_ground_select_screen(self):
        self.grounds_selected = await self.app.push_screen_wait(GroundSelectScreen())

    @work(thread=True)
    @on(Button.Pressed, "#order-button")
    async def send_order(self):
        hour_select: Select = self.query_one("#hour-select")
        minute_select: Select = self.query_one("#minute-select")
        second_select: Select = self.query_one("#second-select")
        hour_expected = hour_select.value
        minute_expected = minute_select.value
        second_expected = second_select.value

        logger.info(
            f"将在 {hour_expected:02}:{minute_expected:02}:{second_expected:02} 发送订单"
        )

        while True:
            now = datetime.now()
            if (
                now.hour == hour_expected
                and now.minute == minute_expected
                and now.second == second_expected
            ):
                break

        contact_select: Select = self.app.query_one("#user-contact-select")
        venue_select: Select = self.app.query_one("#ground-venue-select")
        contact_id = contact_select.value
        venue_info = json.loads(venue_select.value)
        ground_list = self.grounds_selected

        try:
            await self.js_api.post_book(
                contact_id=contact_id,
                venue_id=venue_info["venue_id"],
                venue_name=venue_info["venue_name"],
                agency_id=venue_info["agency_id"],
                agency_name=venue_info["agency_name"],
                sports_name=venue_info["sports_name"],
                ground_list=ground_list,
            )
        except Exception as e:
            logger.error("预定失败")
            raise

        logger.info("下单成功，请前往小程序付款")

    @work
    @on(Select.Changed, "#ground-sports-select")
    async def update_venue(self, event: Select.Changed):
        sports_name = event.value
        if sports_name != Select.BLANK:
            venue_list = []
            try:
                venues = await self.js_api.get_venue_list(sports_name)
            except Exception as e:
                logger.error("查询场馆信息失败")
                return
            for venue in venues:
                agency_id = venue["agencyId"]
                agency_name = venue["agencyName"]
                venue_id = venue["venueId"]
                venue_name = venue["venueName"]
                sports_name = sports_name
                venue_dict = {
                    "agency_id": agency_id,
                    "agency_name": agency_name,
                    "venue_id": venue_id,
                    "venue_name": venue_name,
                    "sports_name": sports_name,
                }
                venue_list.append((agency_name, json.dumps(venue_dict)))

            venue_select: Select = self.query_one("#ground-venue-select")
            venue_select.set_options(venue_list)
