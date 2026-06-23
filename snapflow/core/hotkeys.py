"""Global hotkey registration."""

from __future__ import annotations

import logging
from typing import Callable, Optional

import keyboard

logger = logging.getLogger(__name__)


class HotkeyManager:
    def __init__(self, callback: Callable[[], None]) -> None:
        self._callback = callback
        self._handle = None
        self._hotkey = ""

    def register(self, hotkey: str) -> None:
        self.unregister()
        hotkey = hotkey.strip().lower()
        if not hotkey:
            return
        try:
            self._handle = keyboard.add_hotkey(hotkey, self._callback, suppress=False)
            self._hotkey = hotkey
            logger.info("Registered hotkey: %s", hotkey)
        except Exception:
            logger.exception("Failed to register hotkey: %s", hotkey)
            raise

    def unregister(self) -> None:
        if self._handle is not None:
            try:
                keyboard.remove_hotkey(self._handle)
            except Exception:
                logger.debug("Hotkey removal failed", exc_info=True)
            self._handle = None
            self._hotkey = ""

    @property
    def hotkey(self) -> str:
        return self._hotkey
