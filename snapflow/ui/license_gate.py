"""License gate — shown on launch if no valid license is saved."""
from __future__ import annotations
import threading
import customtkinter as ctk
from snapflow.core.license import validate_license, save_license, load_saved_license

class LicenseGate(ctk.CTkToplevel):
    def __init__(self, parent, on_success):
        super().__init__(parent)
        self.on_success = on_success
        self.validated = False

        # Window setup
        self.title("")
        self.resizable(False, False)
        self.geometry("420x320")
        self.configure(fg_color="#0d0d0d")
        self.overrideredirect(False)

        # Center on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 210
        y = (self.winfo_screenheight() // 2) - 160
        self.geometry(f"420x320+{x}+{y}")

        # Block interaction with parent
        self.grab_set()
        self.lift()
        self.focus_force()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()

    def _build_ui(self):
        # Logo / title
        ctk.CTkLabel(
            self,
            text="⚡ SnapFlow",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#ffffff",
        ).pack(pady=(36, 4))

        ctk.CTkLabel(
            self,
            text="Enter your license key to continue",
            font=ctk.CTkFont(size=12),
            text_color="#666666",
        ).pack(pady=(0, 24))

        # Key input
        self.key_entry = ctk.CTkEntry(
            self,
            width=320,
            height=42,
            placeholder_text="XXXX-XXXX-XXXX-XXXX",
            font=ctk.CTkFont(size=13),
            fg_color="#1a1a1a",
            border_color="#2a2a2a",
            border_width=1,
            text_color="#ffffff",
            corner_radius=8,
            justify="center",
        )
        self.key_entry.pack(pady=(0, 8))
        self.key_entry.bind("<Return>", lambda e: self._verify())

        # Status label
        self.status_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#666666",
            height=18,
        )
        self.status_label.pack(pady=(0, 12))

        # Activate button
        self.activate_btn = ctk.CTkButton(
            self,
            text="Activate",
            width=320,
            height=42,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            corner_radius=8,
            command=self._verify,
        )
        self.activate_btn.pack(pady=(0, 16))

        # Gumroad link
        ctk.CTkLabel(
            self,
            text="Don't have a license? Get one at gumroad.com",
            font=ctk.CTkFont(size=10),
            text_color="#444444",
            cursor="hand2",
        ).pack()

    def _set_status(self, text: str, color: str = "#666666"):
        self.status_label.configure(text=text, text_color=color)
        self.update()

    def _set_loading(self, loading: bool):
        if loading:
            self.activate_btn.configure(text="Verifying...", state="disabled")
            self.key_entry.configure(state="disabled")
        else:
            self.activate_btn.configure(text="Activate", state="normal")
            self.key_entry.configure(state="normal")
        self.update()

    def _verify(self):
        key = self.key_entry.get().strip()
        if not key:
            self._set_status("Please enter your license key.", "#ef4444")
            return

        self._set_loading(True)
        self._set_status("Verifying...", "#666666")

        def do_verify():
            valid, message = validate_license(key)
            self.after(0, lambda: self._handle_result(valid, message, key))

        threading.Thread(target=do_verify, daemon=True).start()

    def _handle_result(self, valid: bool, message: str, key: str):
        self._set_loading(False)
        if valid:
            self._set_status("✓ " + message, "#22c55e")
            save_license(key)
            self.after(800, self._succeed)
        else:
            self._set_status("✗ " + message, "#ef4444")

    def _succeed(self):
        self.validated = True
        self.grab_release()
        self.destroy()
        self.on_success()

    def _on_close(self):
        # Don't allow closing without a valid license
        import sys
        sys.exit(0)


def show_license_gate(parent, on_success):
    gate = LicenseGate(parent, on_success)
    return gate
