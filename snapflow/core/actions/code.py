"""Copy code to the clipboard, wrapped in a fenced block."""

import pyperclip

from snapflow.core.actions.base import BaseAction


class CodeAction(BaseAction):
    action_type = "code"

    def execute(self, data: str) -> str:
        content = data.strip()
        if not content.startswith("```"):
            content = f"```\n{content}\n```"
        pyperclip.copy(content)
        return "Code block copied to clipboard."
