"""Modal license-key gate shown on startup when the app isn't licensed."""

from __future__ import annotations

import threading
from collections.abc import Callable

import customtkinter as ctk

from snapflow.core.license import get_saved_license_key, verify_license
from snapflow.ui.theme import (
    ACCENT,
    ACCENT_HOVER,
    CARD_BG,
    CARD_BORDER,
    CONTENT_BG,
    ERROR,
    FONT_BODY,
    FONT_SMALL,
    RADIUS_LG,
    RADIUS_PILL,
    RADIUS_SM,
    SUCCESS,
    TEXT_MUTED,
    TEXT_PRIMARY,
)

GATE_WIDTH = 420
GATE_HEIGHT = 320


def show_license_gate(master: ctk.CTk, on_success: Callable[[], None]) -> None:
    """Show a modal window blocking app use until a valid license is entered."""
    LicenseGate(master, on_success)


class LicenseGate(ctk.CTkToplevel):
    def __init__(self, master: ctk.CTk, on_success: Callable[[], None]) -> None:
        super().__init__(master)
        self._master = master
        self._on_success = on_success

        self.title("Activate SnapFlow")
        self.geometry(f"{GATE_WIDTH}x{GATE_HEIGHT}")
        self.minsize(GATE_WIDTH, GATE_HEIGHT)
        self.resizable(False, False)
        self.configure(fg_color=CONTENT_BG)

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(10, self._center)

        card = ctk.CTkFrame(
            self,
            fg_color=CARD_BG,
            corner_radius=RADIUS_LG,
            border_width=1,
            border_color=CARD_BORDER,
        )
        card.pack(fill="both", expand=True, padx=18, pady=18)

        ctk.CTkLabel(
            card,
            text="⚡ SnapFlow",
            font=("Segoe UI Semibold", 20, "bold"),
            text_color=TEXT_PRIMARY,
        ).pack(pady=(28, 4))

        ctk.CTkLabel(
            card,
            text="Enter your license key to continue",
            font=FONT_SMALL,
            text_color=TEXT_MUTED,
        ).pack(pady=(0, 18))

        self._entry = ctk.CTkEntry(
            card,
            width=300,
            height=40,
            corner_radius=RADIUS_SM,
            border_width=1,
            border_color=CARD_BORDER,
            font=FONT_BODY,
            placeholder_text="XXXX-XXXX-XXXX-XXXX",
            justify="center",
        )
        self._entry.pack(pady=(0, 14))
        self._entry.insert(0, get_saved_license_key())
        self._entry.bind("<Return>", lambda _event: self._activate())
        self._entry.focus_set()

        self._status = ctk.CTkLabel(
            card,
            text="",
            font=FONT_SMALL,
            text_color=ERROR,
            wraplength=300,
        )
        self._status.pack(pady=(0, 10))

        self._button = ctk.CTkButton(
            card,
            text="Activate",
            width=300,
            height=40,
            corner_radius=RADIUS_PILL,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            font=FONT_BODY,
            command=self._activate,
        )
        self._button.pack(pady=(4, 0))

        self.transient(master)
        self.lift()
        self.focus_force()
        self.grab_set()

    def _center(self) -> None:
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - GATE_WIDTH) // 2
        y = (screen_h - GATE_HEIGHT) // 2
        self.geometry(f"{GATE_WIDTH}x{GATE_HEIGHT}+{x}+{y}")

    def _activate(self) -> None:
        key = self._entry.get().strip()
        if not key:
            self._set_status("Enter a license key.")
            return

        self._button.configure(state="disabled", text="Checking...")
        self._set_status("")
        threading.Thread(target=self._verify_async, args=(key,), daemon=True).start()

    def _verify_async(self, key: str) -> None:
        success, message = verify_license(key)
        self.after(0, lambda: self._on_verified(success, message))

    def _on_verified(self, success: bool, message: str) -> None:
        if success:
            self._set_status(f"✓ {message}", color=SUCCESS)
            self._button.configure(text="Activated")
            self.after(500, self._close_success)
            return

        self._button.configure(state="normal", text="Activate")
        self._set_status(f"✗ {message}", color=ERROR)

    def _close_success(self) -> None:
        self.grab_release()
        self.destroy()
        self._on_success()

    def _set_status(self, message: str, *, color: str = ERROR) -> None:
        self._status.configure(text=message, text_color=color)

    def _on_close(self) -> None:
        self._master.after(0, self._master.destroy)
        self.destroy()
