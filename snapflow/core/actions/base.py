"""Modular action handler registry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict

_REGISTRY: Dict[str, "BaseAction"] = {}


class BaseAction(ABC):
    """Base class for all SnapFlow actions."""

    action_type: str = ""

    @abstractmethod
    def execute(self, data: str) -> str:
        """
        Perform the action and return a short user-facing status message.
        Raise ActionError on failure.
        """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.action_type and not getattr(cls, "__abstractmethods__", None):
            _REGISTRY[cls.action_type] = cls()


class ActionError(Exception):
    """Raised when an action cannot be completed."""


def get_action(action_type: str) -> BaseAction:
    """Look up a registered action handler by type."""
    normalized = action_type.strip().lower()
    handler = _REGISTRY.get(normalized)
    if handler is None:
        known = ", ".join(sorted(_REGISTRY)) or "(none registered)"
        raise ActionError(f"Unknown action type '{action_type}'. Known types: {known}")
    return handler


def execute_action(action_type: str, data: str) -> str:
    """Run the handler for action_type and return its status message."""
    return get_action(action_type).execute(data)


def registered_types() -> list[str]:
    return sorted(_REGISTRY)
