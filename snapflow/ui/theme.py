"""Premium macOS-style dark/light theme tokens for SnapFlow."""

from __future__ import annotations

import tkinter.font as tkfont

# --- Surfaces -----------------------------------------------------------
WINDOW_BG = "#0d0d0d"
SIDEBAR_BG = "#0a0a0b"
SIDEBAR_BORDER = "#1f1f22"
CONTENT_BG = "#0d0d0d"

# "Frosted glass" card — a lighter translucent-looking panel with a visible
# hairline border to fake the blur/elevation you'd get from a real backdrop
# filter (customtkinter has no real alpha blending for frames). Contrast
# against WINDOW_BG is deliberately pronounced, or the elevation disappears.
CARD_BG = "#1e1e22"
CARD_BG_RAISED = "#26262b"
CARD_BORDER = "#3a3a40"
CARD_BORDER_SOFT = "#2c2c31"
DIVIDER = "#1f1f22"

# --- Accents (macOS system palette) -------------------------------------
ACCENT = "#0A84FF"
ACCENT_HOVER = "#3aa0ff"
ACCENT_SOFT = "#15294a"
SUCCESS = "#30D158"
ERROR = "#FF453A"
WARNING = "#FF9F0A"

# --- Text -----------------------------------------------------------------
TEXT_PRIMARY = "#F5F5F7"
TEXT_MUTED = "#8E8E93"
TEXT_FAINT = "#5b5b60"

# Backwards-compat alias used by older view code.
SIDEBAR_WIDTH = 192
WINDOW_WIDTH = 940
WINDOW_HEIGHT = 640

# --- Corner radii ----------------------------------------------------------
RADIUS_LG = 22
RADIUS_MD = 16
RADIUS_SM = 12
RADIUS_PILL = 999


def _resolve_font_family() -> str:
    """Prefer Inter; fall back to the macOS-adjacent Segoe UI Variable/Segoe UI."""
    try:
        installed = set(tkfont.families())
    except RuntimeError:
        # No Tk root yet — Tk will silently substitute a default if "Inter"
        # turns out to be unavailable, so this is a safe fallback either way.
        return "Inter"
    for candidate in ("Inter", "Segoe UI Variable Text", "Segoe UI"):
        if candidate in installed:
            return candidate
    return "Segoe UI"


FONT_FAMILY = _resolve_font_family()

FONT_TITLE = (FONT_FAMILY, 25, "bold")
FONT_HEADING = (FONT_FAMILY, 16, "bold")
FONT_BODY = (FONT_FAMILY, 13)
FONT_BODY_MEDIUM = (FONT_FAMILY, 13, "bold")
FONT_SMALL = (FONT_FAMILY, 11)
FONT_MONO = ("Cascadia Code", 12)
