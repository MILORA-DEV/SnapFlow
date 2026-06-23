"""Settings view — hotkey configuration only."""

from __future__ import annotations

import customtkinter as ctk

from snapflow.core.config import AppSettings
from snapflow.ui.theme import ACCENT, FONT_BODY, FONT_HEADING, FONT_SMALL, TEXT_MUTED


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
