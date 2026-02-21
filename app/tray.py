import pystray
from PIL import Image, ImageDraw
import threading
import os
import sys

def get_base_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(__file__))

icon_path = os.path.join(get_base_path(), "assets", "icon.png")

def _create_default_icon():
    """Create a simple colored circle as default tray icon."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, 60, 60], fill="#1f6aa5")
    draw.ellipse([20, 20, 44, 44], fill="white")
    return img


def create_tray(on_show, on_exit):
    icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icon.png")
    if os.path.exists(icon_path):
        try:
            img = Image.open(icon_path).resize((64, 64))
        except Exception:
            img = _create_default_icon()
    else:
        img = _create_default_icon()

    menu = pystray.Menu(
        pystray.MenuItem("Open Gacha Reminder", on_show, default=True),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Exit", on_exit)
    )

    icon = pystray.Icon("gacha-reminder", img, "Gacha Reminder", menu)
    return icon


def run_tray(icon):
    """Run the tray icon in a background thread."""
    t = threading.Thread(target=icon.run, daemon=True)
    t.start()
    return t