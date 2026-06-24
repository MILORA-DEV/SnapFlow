"""Manual visual check for the toast slide animation (not part of the app)."""
from __future__ import annotations

import customtkinter as ctk

from snapflow.ui.theme import CONTENT_BG
from snapflow.ui.toast import ToastManager

root = ctk.CTk()
root.geometry("900x600")
root.configure(fg_color=CONTENT_BG)
toast = ToastManager(root)
root.after(500, lambda: toast.show_success("Copied to clipboard"))
root.after(2200, lambda: root.winfo_toplevel().update())
root.mainloop()
