"""Dashboard home view."""

from __future__ import annotations

import customtkinter as ctk

from snapflow.ui.theme import (
    ACCENT,
    ACCENT_HOVER,
    CARD_BG,
    CARD_BG_RAISED,
    CARD_BORDER,
    CARD_BORDER_SOFT,
    ERROR,
    FONT_BODY,
    FONT_HEADING,
    FONT_SMALL,
    FONT_TITLE,
    RADIUS_LG,
    RADIUS_MD,
    RADIUS_PILL,
    SUCCESS,
    TEXT_MUTED,
    TEXT_PRIMARY,
)


class DashboardView(ctk.CTkFrame):
    def __init__(self, master, app) -> None:
        super().__init__(master, fg_color="transparent")
        self.app = app

        top_row = ctk.CTkFrame(self, fg_color="transparent")
        top_row.pack(fill="x", padx=36, pady=(30, 0))

        header_block = ctk.CTkFrame(top_row, fg_color="transparent")
        header_block.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            header_block,
            text="SnapFlow",
            font=FONT_TITLE,
            text_color=TEXT_PRIMARY,
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
            corner_radius=RADIUS_PILL,
            border_width=1,
            border_color=CARD_BORDER_SOFT,
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

        card = ctk.CTkFrame(
            self,
            fg_color=CARD_BG,
            corner_radius=RADIUS_LG,
            border_width=1,
            border_color=CARD_BORDER,
        )
        card.pack(fill="both", expand=True, padx=36, pady=(22, 28))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.place(relx=0.5, rely=0.42, anchor="center")

        self.status_label = ctk.CTkLabel(
            inner,
            text="Ready",
            font=FONT_HEADING,
            text_color=TEXT_PRIMARY,
        )
        self.status_label.pack(pady=(0, 8))

        self.hotkey_label = ctk.CTkLabel(
            inner,
            text="",
            font=FONT_SMALL,
            text_color=TEXT_MUTED,
        )
        self.hotkey_label.pack(pady=(0, 22))

        self.capture_btn = ctk.CTkButton(
            inner,
            text="Capture Region",
            width=230,
            height=48,
            corner_radius=RADIUS_PILL,
            font=FONT_BODY,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            command=self.app.request_capture,
        )
        self.capture_btn.pack(pady=(0, 12))

        ctk.CTkLabel(
            inner,
            text="Drag to select an area · Esc to cancel",
            font=FONT_SMALL,
            text_color=TEXT_MUTED,
        ).pack()

        self.last_action_frame = ctk.CTkFrame(
            card,
            fg_color=CARD_BG_RAISED,
            corner_radius=RADIUS_MD,
            border_width=1,
            border_color=CARD_BORDER_SOFT,
        )
        self.last_action_frame.pack(fill="x", padx=26, pady=26, side="bottom")

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
