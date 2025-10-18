import datetime
import json
from pathlib import Path

from pynput import keyboard, mouse


class TraceRecorder:
    def __init__(self):
        self.active = False
        self.pressed = False
        self.trace = []

        self.listener_keyboard = keyboard.GlobalHotKeys(
            {
                "<ctrl>+<alt>+h": self.on_activate,
            }
        )
        self.listener_mouse = mouse.Listener(
            on_move=self.on_move, on_click=self.on_click
        )
        self.listener_keyboard.start()
        self.listener_mouse.start()
        print("Ctrl+Alt+H to start recording mouse path.")

    def on_activate(self):
        self.active = True
        print("activate recording!")

    def on_move(self, x, y):
        if self.pressed:
            print(f"record mouse moved to ({x}, {y})")
            self.trace.append((x, y))

    def on_click(self, x, y, button, pressed):
        if pressed and self.active:
            print(f"record started at ({x}, {y})")
            self.pressed = True
            self.trace.append((x, y))

        if not pressed and self.active:
            print(f"recording stopped at ({x}, {y})")
            self.pressed = False
            self.active = False
            assets_path = Path(__file__).parent / "assets"
            trace_file = (
                assets_path
                / f"trace_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            with open(trace_file, "w") as f:
                json.dump({"trace": self.trace}, f)
                self.trace = []


if __name__ == "__main__":
    recorder = TraceRecorder()
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("recording end.")
