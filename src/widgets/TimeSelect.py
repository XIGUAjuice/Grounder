from textual.app import ComposeResult
from textual.containers import Horizontal, Middle
from textual.widgets import Label, Select


class TimeSelect(Horizontal):

    DEFAULT_CSS = """
    TimeSelect {
        width: auto;
        
        Select {
            width: 10;
        }
    }
    """

    def __init__(
        self, *children, name=None, id=None, classes=None, disabled=False, markup=True
    ):
        super().__init__(
            *children,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
            markup=markup,
        )

    def compose(self) -> ComposeResult:
        hour_options = [(f"{hour:02}", hour) for hour in range(24)]
        minute_options = [(f"{minute:02}", minute) for minute in range(60)]
        second_options = [(f"{second:02}", second) for second in range(60)]
        yield Middle(
            Select(hour_options, id="hour-select", value=12, allow_blank=False)
        )
        yield Middle(Label(":"))
        yield Middle(
            Select(minute_options, id="minute-select", value=0, allow_blank=False)
        )
        yield Middle(Label(":"))
        yield Middle(
            Select(second_options, id="second-select", value=0, allow_blank=False)
        )
