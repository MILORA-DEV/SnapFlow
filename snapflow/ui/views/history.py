"""History view showing the last 5 actions."""

from __future__ import annotations

from datetime import datetime

import customtkinter as ctk

from snapflow.core.history import HistoryEntry
from snapflow.ui.theme import CARD_BG, FONT_BODY, FONT_HEADING, FONT_SMALL, TEXT_MUTED


class HistoryView(ctk.CTkFrame):
    def __init__(self, master, app) -> None:
        super().__init__(master, fg_color="transparent")
        self.app = app

        ctk.CTkLabel(
            self,
            text="History",
            font=FONT_HEADING,
            anchor="w",
        ).pack(fill="x", padx=32, pady=(28, 4))

        ctk.CTkLabel(
            self,
            text="Your five most recent captures.",
            font=FONT_BODY,
            text_color=TEXT_MUTED,
            anchor="w",
        ).pack(fill="x", padx=32, pady=(0, 16))

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=32, pady=(0, 24))

        self.empty_label = ctk.CTkLabel(
            self.scroll,
            text="No history yet. Capture a region to get started.",
            font=FONT_BODY,
            text_color=TEXT_MUTED,
        )

    def on_show(self) -> None:
        self._render(self.app.history.get_all())

    def refresh(self) -> None:
        if self.winfo_ismapped():
            self._render(self.app.history.get_all())

    def _render(self, entries: list[HistoryEntry]) -> None:
        for child in self.scroll.winfo_children():
            child.destroy()

        if not entries:
            self.empty_label = ctk.CTkLabel(
                self.scroll,
                text="No history yet. Capture a region to get started.",
                font=FONT_BODY,
                text_color=TEXT_MUTED,
            )
            self.empty_label.pack(anchor="w", pady=8)
            return

        for entry in entries:
            self._add_card(entry)

    def _add_card(self, entry: HistoryEntry) -> None:
        card = ctk.CTkFrame(self.scroll, fg_color=CARD_BG, corner_radius=12)
        card.pack(fill="x", pady=6)

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(12, 4))

        badge_color = "#3FB950" if entry.success else "#F85149"
        badge_text = entry.action_type.upper() if entry.action_type else "INFO"

        ctk.CTkLabel(
            top,
            text=badge_text,
            font=FONT_SMALL,
            text_color=badge_color,
            anchor="w",
        ).pack(side="left")

        ctk.CTkLabel(
            top,
            text=self._format_time(entry.timestamp),
            font=FONT_SMALL,
            text_color=TEXT_MUTED,
            anchor="e",
        ).pack(side="right")

        ctk.CTkLabel(
            card,
            text=entry.message,
            font=FONT_BODY,
            anchor="w",
            justify="left",
            wraplength=620,
        ).pack(fill="x", padx=16, pady=(0, 4))

        if entry.preview:
            ctk.CTkLabel(
                card,
                text=entry.preview,
                font=FONT_SMALL,
                text_color=TEXT_MUTED,
                anchor="w",
                justify="left",
                wraplength=620,
            ).pack(fill="x", padx=16, pady=(0, 12))

    @staticmethod
    def _format_time(timestamp: str) -> str:
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return dt.strftime("%b %d, %Y · %H:%M")
        except ValueError:
            return timestamp
