from textual.containers import Horizontal


class TableRow(Horizontal):
    DEFAULT_CSS = """
    TableRow {
        height: auto;
        width: auto;
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


class TabelCell(Horizontal):
    DEFAULT_CSS = """
    TabelCell {
        height: auto;
        width: auto;
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
