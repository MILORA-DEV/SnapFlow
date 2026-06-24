"""System tray integration."""

from __future__ import annotations

import logging
import sys
import threading
from pathlib import Path
from typing import Callable, Optional

import pystray
from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)


def _icon_path() -> Path:
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).resolve().parent.parent.parent
    return base / "snapflow" / "assets" / "icon.ico"


def _fallback_icon(size: int = 64) -> Image.Image:
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((4, 4, size - 4, size - 4), radius=12, fill=(10, 132, 255, 255))
    draw.polygon(
        [(size * 0.28, size * 0.35), (size * 0.72, size * 0.5), (size * 0.28, size * 0.65)],
        fill="white",
    )
    return image


def _create_icon(size: int = 64) -> Image.Image:
    path = _icon_path()
    if path.exists():
        try:
            return Image.open(path).convert("RGBA").resize((size, size))
        except Exception:
            logger.debug("Failed to load bundled tray icon, using fallback", exc_info=True)
    return _fallback_icon(size)


class TrayController:
    def __init__(
        self,
        *,
        hotkey_label: str,
        on_show: Callable[[], None],
        on_capture: Callable[[], None],
        on_quit: Callable[[], None],
    ) -> None:
        self._hotkey_label = hotkey_label
        self._on_show = on_show
        self._on_capture = on_capture
        self._on_quit = on_quit
        self._icon: Optional[pystray.Icon] = None
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        menu = pystray.Menu(
            pystray.MenuItem("Open Dashboard", lambda *_: self._on_show(), default=True),
            pystray.MenuItem(
                f"Capture ({self._hotkey_label})",
                lambda *_: self._on_capture(),
            ),
            pystray.MenuItem("Quit", lambda *_: self._quit()),
        )
        self._icon = pystray.Icon(
            "snapflow",
            _create_icon(),
            "SnapFlow — Ready",
            menu,
        )
        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._icon is not None:
            self._icon.stop()

    def notify(self, title: str, message: str) -> None:
        if self._icon is not None:
            try:
                self._icon.notify(message, title)
            except Exception:
                logger.debug("Tray notification failed", exc_info=True)

    def set_status(self, status: str) -> None:
        if self._icon is not None:
            self._icon.title = f"SnapFlow — {status}"

    def update_hotkey_label(self, hotkey: str) -> None:
        self._hotkey_label = hotkey
        if self._icon is not None:
            self.stop()
            self.start()

    def _quit(self) -> None:
        self.stop()
        self._on_quit()
