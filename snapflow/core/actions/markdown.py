"""Copy clean markdown to the clipboard."""

import pyperclip

from snapflow.core.actions.base import BaseAction


class MarkdownAction(BaseAction):
    action_type = "markdown"

    def execute(self, data: str) -> str:
        pyperclip.copy(data)
        return "Markdown copied to clipboard."


class TextAction(MarkdownAction):
    action_type = "text"
