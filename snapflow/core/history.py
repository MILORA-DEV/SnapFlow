"""Persistent action history (last 5 entries)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Callable

from snapflow.core.config import HISTORY_PATH

MAX_HISTORY = 5


@dataclass
class HistoryEntry:
    timestamp: str
    action_type: str
    message: str
    success: bool
    preview: str = ""

    @classmethod
    def now(
        cls,
        *,
        action_type: str,
        message: str,
        success: bool,
        preview: str = "",
    ) -> HistoryEntry:
        return cls(
            timestamp=datetime.now(timezone.utc).isoformat(),
            action_type=action_type,
            message=message,
            success=success,
            preview=preview[:200],
        )


class HistoryStore:
    def __init__(self, path=HISTORY_PATH) -> None:
        self._path = path
        self._entries: list[HistoryEntry] = []
        self._listeners: list[Callable[[], None]] = []
        self.load()

    def add(
        self,
        *,
        action_type: str,
        message: str,
        success: bool,
        preview: str = "",
    ) -> None:
        entry = HistoryEntry.now(
            action_type=action_type,
            message=message,
            success=success,
            preview=preview,
        )
        self._entries.insert(0, entry)
        self._entries = self._entries[:MAX_HISTORY]
        self.save()
        self._notify()

    def get_all(self) -> list[HistoryEntry]:
        return list(self._entries)

    def load(self) -> None:
        if not self._path.exists():
            self._entries = []
            return
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            self._entries = [HistoryEntry(**item) for item in raw[:MAX_HISTORY]]
        except (json.JSONDecodeError, TypeError, ValueError):
            self._entries = []

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = [asdict(entry) for entry in self._entries]
        self._path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def subscribe(self, callback: Callable[[], None]) -> None:
        self._listeners.append(callback)

    def _notify(self) -> None:
        for listener in self._listeners:
            listener()
