"""Screen region selection and capture using mss."""

from __future__ import annotations

import base64
import io
import tkinter as tk
from dataclasses import dataclass
from typing import Callable, Optional

import mss
from PIL import Image


@dataclass
class Region:
    left: int
    top: int
    width: int
    height: int

    def to_mss_dict(self) -> dict:
        return {
            "left": self.left,
            "top": self.top,
            "width": max(self.width, 1),
            "height": max(self.height, 1),
        }


class SelectionOverlay:
    """Fullscreen overlay for drag-to-select capture."""

    MIN_SIZE = 5

    def __init__(self, root: tk.Misc, on_complete: Callable[[Optional[Region]], None]):
        self._on_complete = on_complete
        self._start_x = 0
        self._start_y = 0
        self._start_x_root = 0
        self._start_y_root = 0
        self._rect_id: Optional[int] = None

        self._overlay = tk.Toplevel(root)
        self._overlay.attributes("-fullscreen", True)
        self._overlay.attributes("-topmost", True)
        self._overlay.attributes("-alpha", 0.25)
        self._overlay.configure(bg="black")
        self._overlay.overrideredirect(True)

        self._canvas = tk.Canvas(
            self._overlay,
            cursor="cross",
            highlightthickness=0,
            bg="black",
        )
        self._canvas.pack(fill=tk.BOTH, expand=True)

        self._canvas.bind("<ButtonPress-1>", self._on_press)
        self._canvas.bind("<B1-Motion>", self._on_drag)
        self._canvas.bind("<ButtonRelease-1>", self._on_release)
        self._overlay.bind("<Escape>", self._on_cancel)
        self._overlay.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _on_press(self, event: tk.Event) -> None:
        self._start_x = event.x
        self._start_y = event.y
        self._start_x_root = event.x_root
        self._start_y_root = event.y_root
        if self._rect_id is not None:
            self._canvas.delete(self._rect_id)
        self._rect_id = self._canvas.create_rectangle(
            self._start_x,
            self._start_y,
            self._start_x,
            self._start_y,
            outline="#00aaff",
            width=2,
        )

    def _on_drag(self, event: tk.Event) -> None:
        if self._rect_id is None:
            return
        self._canvas.coords(
            self._rect_id,
            self._start_x,
            self._start_y,
            event.x,
            event.y,
        )

    def _on_release(self, event: tk.Event) -> None:
        left = min(self._start_x_root, event.x_root)
        top = min(self._start_y_root, event.y_root)
        width = abs(event.x_root - self._start_x_root)
        height = abs(event.y_root - self._start_y_root)
        self._close()

        if width < self.MIN_SIZE or height < self.MIN_SIZE:
            self._on_complete(None)
            return

        self._on_complete(Region(left=left, top=top, width=width, height=height))

    def _on_cancel(self, _event=None) -> None:
        self._close()
        self._on_complete(None)

    def _close(self) -> None:
        self._overlay.destroy()


def capture_region(region: Region) -> Image.Image:
    """Capture a screen region as a PIL Image."""
    with mss.mss() as sct:
        shot = sct.grab(region.to_mss_dict())
        return Image.frombytes("RGB", shot.size, shot.rgb)


def image_to_base64(image: Image.Image, fmt: str = "PNG") -> str:
    """Encode a PIL image as a base64 string."""
    buffer = io.BytesIO()
    image.save(buffer, format=fmt)
    return base64.b64encode(buffer.getvalue()).decode("ascii")
