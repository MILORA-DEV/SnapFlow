"""SnapFlow desktop application views."""

from __future__ import annotations

from functools import partial
import customtkinter as ctk

from snapflow.core.config import AppSettings
from snapflow.ui.theme import (
    ACCENT,
    CARD_BG,
    ERROR,
    FONT_BODY,
    FONT_HEADING,
    FONT_SMALL,
    FONT_TITLE,
    SUCCESS,
    TEXT_MUTED,
)


class DashboardView(ctk.CTkFrame):
    def __init__(self, master, app) -> None:
        super().__init__(master, fg_color="transparent")
        self.app = app

        top_row = ctk.CTkFrame(self, fg_color="transparent")
        top_row.pack(fill="x", padx=32, pady=(28, 0))

        header_block = ctk.CTkFrame(top_row, fg_color="transparent")
        header_block.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            header_block,
            text="SnapFlow",
            font=FONT_TITLE,
            anchor="w",
        ).pack(fill="x")

        ctk.CTkLabel(
            header_block,
            text="Screenshot-to-Action",
            font=FONT_BODY,
            text_color=TEXT_MUTED,
            anchor="w",
        ).pack(fill="x", pady=(2, 0))

        self.connection_frame = ctk.CTkFrame(
            top_row,
            fg_color=CARD_BG,
            corner_radius=20,
            height=36,
        )
        self.connection_frame.pack(side="right", padx=(12, 0))
        self.connection_frame.pack_propagate(False)

        conn_inner = ctk.CTkFrame(self.connection_frame, fg_color="transparent")
        conn_inner.pack(padx=14, pady=6)

        self.conn_dot = ctk.CTkLabel(
            conn_inner,
            text="●",
            font=("Segoe UI", 14),
            text_color=TEXT_MUTED,
            width=16,
        )
        self.conn_dot.pack(side="left", padx=(0, 6))

        self.conn_label = ctk.CTkLabel(
            conn_inner,
            text="Checking…",
            font=FONT_SMALL,
            text_color=TEXT_MUTED,
        )
        self.conn_label.pack(side="left")

        card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=16)
        card.pack(fill="both", expand=True, padx=32, pady=(20, 24))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.place(relx=0.5, rely=0.45, anchor="center")

        self.status_label = ctk.CTkLabel(
            inner,
            text="Ready",
            font=FONT_HEADING,
            text_color=TEXT_MUTED,
        )
        self.status_label.pack(pady=(0, 8))

        self.hotkey_label = ctk.CTkLabel(
            inner,
            text="",
            font=FONT_SMALL,
            text_color=TEXT_MUTED,
        )
        self.hotkey_label.pack(pady=(0, 20))

        self.capture_btn = ctk.CTkButton(
            inner,
            text="Capture Region",
            width=220,
            height=48,
            font=FONT_BODY,
            fg_color=ACCENT,
            hover_color="#1084E0",
            command=self.app.request_capture,
        )
        self.capture_btn.pack(pady=(0, 12))

        ctk.CTkLabel(
            inner,
            text="Drag to select an area · Esc to cancel",
            font=FONT_SMALL,
            text_color=TEXT_MUTED,
        ).pack()

        self.last_action_frame = ctk.CTkFrame(card, fg_color="#1A1A1A", corner_radius=12)
        self.last_action_frame.pack(fill="x", padx=24, pady=24, side="bottom")

        ctk.CTkLabel(
            self.last_action_frame,
            text="Last action",
            font=FONT_SMALL,
            text_color=TEXT_MUTED,
            anchor="w",
        ).pack(fill="x", padx=16, pady=(12, 4))

        self.last_action_label = ctk.CTkLabel(
            self.last_action_frame,
            text="No captures yet.",
            font=FONT_BODY,
            anchor="w",
            justify="left",
            wraplength=560,
        )
        self.last_action_label.pack(fill="x", padx=16, pady=(0, 12))

    def on_show(self) -> None:
        settings = self.app.settings
        self.hotkey_label.configure(text=f"Global hotkey: {settings.hotkey.upper()}")
        self.app.check_connection()

    def set_status(self, status: str) -> None:
        self.status_label.configure(text=status)

    def set_connection_status(self, connected: bool, label: str) -> None:
        color = SUCCESS if connected else ERROR
        self.conn_dot.configure(text_color=color)
        self.conn_label.configure(text=label, text_color=color if not connected else TEXT_MUTED)

    def set_last_action(self, message: str, *, success: bool) -> None:
        prefix = "✓ " if success else "✗ "
        color = SUCCESS if success else ERROR
        self.last_action_label.configure(text=prefix + message, text_color=color)


class SettingsView(ctk.CTkFrame):
    def __init__(self, master, app) -> None:
        super().__init__(master, fg_color="transparent")
        self.app = app

        ctk.CTkLabel(
            self,
            text="Settings",
            font=FONT_HEADING,
            anchor="w",
        ).pack(fill="x", padx=32, pady=(28, 4))

        ctk.CTkLabel(
            self,
            text="Customize how you capture screenshots.",
            font=FONT_BODY,
            text_color=TEXT_MUTED,
            anchor="w",
        ).pack(fill="x", padx=32, pady=(0, 20))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=32)

        ctk.CTkLabel(form, text="Capture Hotkey", font=FONT_BODY, anchor="w").pack(
            fill="x", pady=(0, 4)
        )
        self.hotkey_entry = ctk.CTkEntry(
            form,
            placeholder_text="ctrl+shift+a",
            height=40,
        )
        self.hotkey_entry.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(
            form,
            text="Use keyboard library format, e.g. ctrl+shift+a or cmd+shift+a",
            font=FONT_SMALL,
            text_color=TEXT_MUTED,
            anchor="w",
        ).pack(fill="x", pady=(0, 20))

        btn_row = ctk.CTkFrame(form, fg_color="transparent")
        btn_row.pack(fill="x")

        self.save_btn = ctk.CTkButton(
            btn_row,
            text="Save",
            width=120,
            height=40,
            fg_color=ACCENT,
            hover_color="#1084E0",
            command=self._save,
        )
        self.save_btn.pack(side="left")

        self.feedback_label = ctk.CTkLabel(
            btn_row,
            text="",
            font=FONT_SMALL,
            anchor="w",
        )
        self.feedback_label.pack(side="left", padx=16)

    def on_show(self) -> None:
        settings = self.app.settings
        self.hotkey_entry.delete(0, "end")
        self.hotkey_entry.insert(0, settings.hotkey)
        self.feedback_label.configure(text="")

    def _save(self) -> None:
        settings = AppSettings(
            hotkey=self.hotkey_entry.get().strip().lower() or "ctrl+shift+a",
        )
        try:
            self.app.save_settings(settings)
        except Exception as exc:
            self.feedback_label.configure(text=str(exc), text_color="#F85149")
            return
        self.feedback_label.configure(text="Saved.", text_color="#3FB950")


# Note: Keep your existing HistoryView implementation below if it is in this same file.
