import json
import logging
from datetime import datetime

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Select, TabbedContent, TabPane

from JSApi import JSApi, TokenExpiredError
from widgets.Table import TabelCell, TableRow

logger = logging.getLogger(__name__)


class GroundButton(Button):
    def __init__(self, variant="default", ground_info=None, *args, **kwargs):
        self.ground_info = ground_info
        self.selected = False
        if ground_info["status"] == "0":
            label = "已订"
        else:
            label = f"¥{ground_info['price']}"
        super().__init__(label, variant, *args, **kwargs)

    @on(Button.Pressed)
    def ground_button_pressed(self):
        if self.selected == True:
            self.selected = False
            self.remove_class("selected")
        else:
            self.selected = True
            self.add_class("selected")


class GroundTable(ScrollableContainer):
    def __init__(self, timestamp, id=None):
        super().__init__(id=id)
        self.timestamp = timestamp


class GroundSelectScreen(ModalScreen):
    class LoggedStatusChanged(Message):
        def __init__(self, sender: "GroundSelectScreen", logged_status: bool) -> None:
            self.sender = sender
            self.logged_status = logged_status
            super().__init__()

        @property
        def control(self) -> "GroundSelectScreen":
            return self.sender

    def __init__(self, *children, name=None, id=None, classes=None):
        super().__init__(*children, name=name, id=id, classes=classes)
        self.js_api: JSApi = self.app.js_api

    def timestamp_to_label(self, timestamp: int):
        dt = datetime.fromtimestamp(timestamp / 1000)
        date_str = f"{dt.month:02}-{dt.day:02}"
        if dt.date() == datetime.today().date():
            weekday_str = "今天"
        else:
            match dt.isoweekday():
                case 1:
                    weekday_str = "星期一"
                case 2:
                    weekday_str = "星期二"
                case 3:
                    weekday_str = "星期三"
                case 4:
                    weekday_str = "星期四"
                case 5:
                    weekday_str = "星期五"
                case 6:
                    weekday_str = "星期六"
                case 7:
                    weekday_str = "星期日"
        return f"{date_str}\n{weekday_str}"

    def compose(self) -> ComposeResult:
        with Vertical(id="ground-select-container"):
            with TabbedContent(id="ground-tabs"):
                timestamps = self.js_api.get_timestamps_from_now()
                for timestamp in timestamps:
                    tab_label = self.timestamp_to_label(timestamp)
                    with TabPane(tab_label, id=f"ground-tab-{timestamp}"):
                        yield Vertical(id="ground-time-container")
                        yield GroundTable(timestamp, id=f"ground-table-{timestamp}")

            with Horizontal(id="ground-buttons-container"):
                yield Button("确定", id="ground-confirm-button")
                yield Button("取消", id="ground-cancel-button")

    @on(Button.Pressed, "#ground-confirm-button")
    def return_grounds_selected(self) -> None:
        selected_grounds = []
        for button in self.query(GroundButton):
            if button.selected:
                info = button.ground_info
                selected_grounds.append(
                    {
                        "groundId": info["groundId"],
                        "groundName": info["groundName"],
                        "startTime": info["start_time"],
                        "endTime": info["end_time"],
                        "sportsType": info["sportsType"],
                    }
                )

        if not selected_grounds:
            logger.warning("未选择任何场地")
        else:
            logger.info(f"已选择场地: {selected_grounds}")
        self.dismiss(selected_grounds)

    @on(Button.Pressed, "#ground-cancel-button")
    def cancel(self) -> None:
        self.dismiss(None)

    @work
    @on(TabbedContent.TabActivated)
    async def show_grounds_info(self, event: TabbedContent.TabActivated) -> None:
        table: GroundTable = event.pane.query_one("GroundTable")
        table.remove_children()

        time_container: Vertical = event.pane.query_one("#ground-time-container")
        time_container.remove_children()

        venue_select: Select = self.app.query_one("#ground-venue-select")
        venue_info = json.loads(venue_select.value)
        venue_id = venue_info["venue_id"]

        dt_starts, ground_dict = await self.get_ground_dict(venue_id, table.timestamp)

        ground_name_labels = [
            Label(ground_name, classes="ground-name")
            for ground_name in ground_dict.keys()
        ]
        table.mount(TableRow(*ground_name_labels, id="ground-name-row"))

        button_containers: dict[datetime, dict[str, TabelCell]] = {}
        for dt_start in dt_starts:
            button_containers.setdefault(dt_start, {})
            str_time = dt_start.strftime("%H:%M")
            time_container.mount(Label(str_time, classes="ground-time"))
            row = TableRow()
            table.mount(row)
            for ground_name in ground_dict.keys():
                button_container = TabelCell()
                button_containers[dt_start][ground_name] = button_container
                row.mount(button_container)

        for ground_name, grounds in ground_dict.items():
            for ground in grounds:
                start_time = ground["start_time"]
                dt_start = datetime.fromtimestamp(start_time / 1000)
                button = GroundButton(
                    ground_info=ground,
                )
                container = button_containers[dt_start][ground_name]
                container.mount(button)

    async def get_ground_dict(self, venue_id, timestamp):
        grounds_dict = {}
        dt_starts = []

        try:
            ground_infos = await self.js_api.get_ground(venue_id, timestamp)
        except TokenExpiredError:
            logger.info("Token 已过期，请重新登录")
            self.post_message(self.LoggedStatusChanged(self, False))
            return dt_starts, grounds_dict
        except Exception as e:
            logger.info(f"获取场地信息失败")
            logger.debug(e, exc_info=True)
            return dt_starts, grounds_dict

        for info in ground_infos:
            start_time = int(info["startTime"])
            end_time = int(info["endTime"])
            dt_start = datetime.fromtimestamp(start_time / 1000)
            dt_starts.append(dt_start)
            if dt_start < datetime.now():
                continue
            for ground in info["blockModel"]:
                ground_name = ground["groundName"]
                grounds_dict.setdefault(ground_name, [])
                ground["start_time"] = start_time
                ground["end_time"] = end_time
                grounds_dict[ground_name].append(ground)
        return dt_starts, grounds_dict
