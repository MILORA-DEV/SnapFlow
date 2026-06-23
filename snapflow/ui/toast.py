"""Animated toast notifications."""

from __future__ import annotations

from functools import partial

import customtkinter as ctk

from snapflow.ui.theme import FONT_BODY, SUCCESS


class ToastManager:
    """Slide-in toast anchored to the bottom of the main window."""

    SLIDE_MS = 14
    SLIDE_STEPS = 16
    DISPLAY_MS = 3400
    MARGIN = 28
    HEIGHT = 58

    def __init__(self, root: ctk.CTk) -> None:
        self._root = root
        self._toast: ctk.CTkFrame | None = None
        self._animating = False

    def show_success(self, message: str) -> None:
        self._root.after(0, partial(self._show, message, accent=SUCCESS))

    def show_info(self, message: str) -> None:
        self._root.after(0, partial(self._show, message, accent="#0078D4"))

    def _show(self, message: str, *, accent: str) -> None:
        self._dismiss()

        toast = ctk.CTkFrame(
            self._root,
            fg_color="#2A2A2A",
            corner_radius=16,
            border_width=1,
            border_color=accent,
            height=self.HEIGHT,
        )
        toast.place(relx=0.5, rely=1.0, anchor="s", y=self.MARGIN + self.HEIGHT + 24)

        inner = ctk.CTkFrame(toast, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=18, pady=12)

        ctk.CTkLabel(
            inner,
            text="✓",
            font=("Segoe UI", 16, "bold"),
            text_color=accent,
            width=24,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            inner,
            text=message,
            font=FONT_BODY,
            text_color="#F0F0F0",
            anchor="w",
            justify="left",
            wraplength=420,
        ).pack(side="left", fill="x", expand=True)

        self._toast = toast
        self._animating = True
        self._slide_in(toast, 0)

    def _slide_in(self, toast: ctk.CTkFrame, step: int) -> None:
        start_y = self.MARGIN + self.HEIGHT + 24
        end_y = self.MARGIN
        progress = step / self.SLIDE_STEPS
        eased = 1 - (1 - progress) ** 3
        y = int(start_y - (start_y - end_y) * eased)
        toast.place(relx=0.5, rely=1.0, anchor="s", y=y)

        if step < self.SLIDE_STEPS:
            self._root.after(
                self.SLIDE_MS,
                partial(self._slide_in, toast, step + 1),
            )
        else:
            self._animating = False
            self._root.after(self.DISPLAY_MS, partial(self._slide_out, toast))

    def _slide_out(self, toast: ctk.CTkFrame) -> None:
        self._animating = True
        self._slide_out_step(toast, 0)

    def _slide_out_step(self, toast: ctk.CTkFrame, step: int) -> None:
        start_y = self.MARGIN
        end_y = self.MARGIN + self.HEIGHT + 24
        progress = step / self.SLIDE_STEPS
        eased = progress ** 2
        y = int(start_y + (end_y - start_y) * eased)
        toast.place(relx=0.5, rely=1.0, anchor="s", y=y)

        if step < self.SLIDE_STEPS:
            self._root.after(
                self.SLIDE_MS,
                partial(self._slide_out_step, toast, step + 1),
            )
        else:
            toast.destroy()
            if self._toast is toast:
                self._toast = None
            self._animating = False

    def _dismiss(self) -> None:
        if self._toast is not None:
            try:
                self._toast.destroy()
            except Exception:
                pass
            self._toast = None
