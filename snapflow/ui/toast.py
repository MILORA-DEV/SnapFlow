"""Animated toast notifications."""

from __future__ import annotations

from functools import partial

import customtkinter as ctk

from snapflow.ui.theme import ACCENT, CARD_BG_RAISED, CARD_BORDER, FONT_BODY, RADIUS_MD, SUCCESS, TEXT_PRIMARY


class ToastManager:
    """Slide-in toast anchored to the bottom of the main window."""

    SLIDE_MS = 14
    SLIDE_STEPS = 16
    DISPLAY_MS = 3400
    MARGIN = 28
    HEIGHT = 58

    # tkinter's place() with rely=1.0 anchors relative to the bottom edge —
    # positive y pushes *below* that edge (off-screen), negative y pulls
    # *up* into the visible area. VISIBLE_Y must be negative or the toast
    # ends up mostly clipped by the window's bottom edge.
    HIDDEN_Y = HEIGHT + MARGIN + 24
    VISIBLE_Y = -MARGIN

    def __init__(self, root: ctk.CTk) -> None:
        self._root = root
        self._toast: ctk.CTkFrame | None = None
        self._animating = False

    def show_success(self, message: str) -> None:
        self._root.after(0, partial(self._show, message, accent=SUCCESS))

    def show_info(self, message: str) -> None:
        self._root.after(0, partial(self._show, message, accent=ACCENT))

    def _show(self, message: str, *, accent: str) -> None:
        self._dismiss()

        toast = ctk.CTkFrame(
            self._root,
            fg_color=CARD_BG_RAISED,
            corner_radius=RADIUS_MD,
            border_width=1,
            border_color=CARD_BORDER,
            height=self.HEIGHT,
        )
        toast.place(relx=0.5, rely=1.0, anchor="s", y=self.HIDDEN_Y)

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
            text_color=TEXT_PRIMARY,
            anchor="w",
            justify="left",
            wraplength=420,
        ).pack(side="left", fill="x", expand=True)

        self._toast = toast
        self._animating = True
        self._slide_in(toast, 0)

    def _slide_in(self, toast: ctk.CTkFrame, step: int) -> None:
        start_y = self.HIDDEN_Y
        end_y = self.VISIBLE_Y
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
        start_y = self.VISIBLE_Y
        end_y = self.HIDDEN_Y
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
