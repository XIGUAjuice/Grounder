import asyncio
import json
import logging
from datetime import datetime

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Middle, ScrollableContainer
from textual.message import Message
from textual.widgets import Button, Label, Select, Input

from GroundSelectScreen import GroundSelectScreen
from JSApi import JSApi, TokenExpiredError, retry
from widgets.TimeSelect import TimeSelect

logger = logging.getLogger(__name__)


class GroundInfoPanel(ScrollableContainer):
    class LoggedStatusChanged(Message):
        def __init__(self, sender: "GroundInfoPanel", logged_status: bool) -> None:
            self.sender = sender
            self.logged_status = logged_status
            super().__init__()

        @property
        def control(self) -> "GroundInfoPanel":
            return self.sender

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
                    [
                        ("羽毛球", "羽毛球"),
                        ("网球", "网球"),
                    ],
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

        with Horizontal():
            yield Middle(Label("重试次数: "), id="retry-label")
            yield Middle(Input(value="10", type="integer", id="retry-input"))

            yield Middle(Label("重试间隔: "), id="delay-label")
            yield Middle(Input(value="200", type="integer", id="delay-input"))
            yield Middle(Label("毫秒"), id="delay-unit-label")

            yield Middle(Label("随机偏差: "), id="jitter-label")
            yield Middle(Input(value="10", type="integer", id="jitter-input"))
            yield Middle(Label("%"), id="jitter-unit-label")

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
        retry_input: Input = self.query_one("#retry-input")
        delay_input: Input = self.query_one("#delay-input")
        jitter_input: Input = self.query_one("#jitter-input")
        contact_select: Select = self.app.query_one("#user-contact-select")
        venue_select: Select = self.app.query_one("#ground-venue-select")

        hour_expected = hour_select.value
        minute_expected = minute_select.value
        second_expected = second_select.value

        max_retries = int(retry_input.value)
        delay = int(delay_input.value)
        jitter_percent = int(jitter_input.value)

        contact_id = contact_select.value
        venue_info = json.loads(venue_select.value)
        ground_list = self.grounds_selected

        now = datetime.now()
        target_time = now.replace(
            hour=int(hour_expected),
            minute=int(minute_expected),
            second=int(second_expected),
            microsecond=0,
        )

        if target_time < now:
            logger.info("预定时间无法早于当前时间")
            return
        else:
            wait_seconds = (target_time - now).total_seconds()
            logger.info(
                f"将在 {hour_expected:02}:{minute_expected:02}:{second_expected:02} 发送订单"
            )
            logger.info(f"距离预定时间还有 {wait_seconds:.3f} 秒")
            await asyncio.sleep(wait_seconds)
            logger.info("开始发送订单")

        try:
            book_with_retry = retry(
                max_retries=max_retries, delay=delay, jitter_percent=jitter_percent
            )(self.js_api.post_book)
            await book_with_retry(
                contact_id=contact_id,
                venue_id=venue_info["venue_id"],
                venue_name=venue_info["venue_name"],
                agency_id=venue_info["agency_id"],
                agency_name=venue_info["agency_name"],
                sports_name=venue_info["sports_name"],
                ground_list=ground_list,
            )
        except TokenExpiredError:
            logger.info("Token 已过期，请重新登录")
            self.post_message(self.LoggedStatusChanged(self, False))
            return
        except Exception as e:
            logger.info("预定失败")
            logger.debug(e, exc_info=True)
            return

    @work
    @on(Select.Changed, "#ground-sports-select")
    async def update_venue(self, event: Select.Changed):
        sports_name = event.value
        if sports_name != Select.BLANK:
            try:
                venues = await self.js_api.get_venue_list(sports_name)
            except TokenExpiredError:
                logger.info("Token 已过期，请重新登录")
                self.post_message(self.LoggedStatusChanged(self, False))
                return
            except Exception as e:
                logger.info("查询场馆信息失败")
                logger.debug(e, exc_info=True)
                return

            venue_list = []
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
