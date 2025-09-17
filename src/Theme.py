from textual.theme import Theme

default_theme = Theme(
    name="default",
    primary="#C45AFF",
    secondary="#a684e8",
    warning="#FFD700",
    error="#FF4500",
    success="#00FA9A",
    accent="#FF69B4",
    background="#0F0F1F",
    surface="#1E1E3F",
    panel="#2D2B55",
    dark=True,
    variables={
        "input-cursor-background": "#C45AFF",
        "footer-background": "transparent",
    },
)
