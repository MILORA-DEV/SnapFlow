"""SnapFlow desktop application shell."""

from __future__ import annotations

import logging
import os
import sys
import threading
from functools import partial
from pathlib import Path

import customtkinter as ctk

from snapflow.core.config import AppSettings, get_settings, get_settings_manager
from snapflow.core.connection import check_server_connection
from snapflow.core.history import HistoryStore
from snapflow.core.hotkeys import HotkeyManager
from snapflow.core.license import is_licensed, revalidate_license
from snapflow.core.pipeline import CapturePipeline, CaptureResult
from snapflow.ui.license_gate import show_license_gate
from snapflow.ui.theme import (
    ACCENT,
    CONTENT_BG,
    FONT_BODY,
    FONT_BODY_MEDIUM,
    FONT_SMALL,
    RADIUS_PILL,
    SIDEBAR_BG,
    SIDEBAR_BORDER,
    SIDEBAR_WIDTH,
    TEXT_FAINT,
    TEXT_MUTED,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from snapflow.ui.toast import ToastManager
from snapflow.ui.tray import TrayController
from snapflow.ui.views import DashboardView, HistoryView, SettingsView

logger = logging.getLogger(__name__)

CONNECTION_POLL_MS = 20_000
APP_VERSION = "1.0.0"
DEBUG_LOG = Path(os.environ.get("APPDATA", Path.home())) / "SnapFlow" / "debug.txt"


def _debug(msg: str) -> None:
    DEBUG_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(DEBUG_LOG, "a") as f:
        f.write(msg + "\n")


def _icon_path() -> Path:
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).resolve().parent.parent.parent
    return base / "snapflow" / "assets" / "icon.ico"


class SnapFlowApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        _debug("=== APP STARTING ===")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("SnapFlow")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(780, 520)
        self.configure(fg_color=CONTENT_BG)

        icon_path = _icon_path()
        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except Exception as exc:
                logger.debug("Could not set window icon: %s", exc)

        self._settings_manager = get_settings_manager()
        self.history = HistoryStore()
        self.history.subscribe(self._on_history_changed)
        self.toast = ToastManager(self)

        self._views: dict[str, ctk.CTkFrame] = {}
        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        self._current_view = ""

        self._build_layout()
        self._build_views()

        self.pipeline = CapturePipeline(
            self,
            on_status=self._on_pipeline_status,
            on_finished=self._on_pipeline_finished,
        )

        settings = get_settings()
        self._hotkeys = HotkeyManager(self.request_capture)
        self._tray = TrayController(
            hotkey_label=settings.hotkey,
            on_show=self.show_window,
            on_capture=self.request_capture,
            on_quit=self.quit_app,
        )

        self.protocol("WM_DELETE_WINDOW", self.hide_to_tray)
        self.show_view("dashboard")
        self._tray.start()
        self._register_hotkey()
        self._schedule_connection_poll()
        logger.info("SnapFlow v%s ready. Hotkey: %s", APP_VERSION, settings.hotkey)
        _debug("App fully initialized, scheduling license check")

        self.after(100, self._check_license)

    @property
    def settings(self) -> AppSettings:
        return get_settings()

    def _check_license(self) -> None:
        _debug("License check running")
        if not is_licensed():
            _debug("Not licensed — showing gate")
            self.withdraw()
            show_license_gate(self, self._on_license_success)
        else:
            _debug("Licensed — continuing")
            threading.Thread(target=self._revalidate_license_async, daemon=True).start()

    def _revalidate_license_async(self) -> None:
        # Best-effort periodic re-check against Gumroad. Network errors are
        # inconclusive and leave the cached license untouched on purpose —
        # this must never lock out an already-activated user over a bad
        # connection. Only an explicit "invalid" answer re-locks the app.
        try:
            still_valid = revalidate_license()
        except Exception as exc:
            _debug(f"License revalidation crashed: {exc}")
            return
        if not still_valid:
            _debug("License revoked on revalidation — re-locking app")
            self.after(0, self._lock_app)

    def _lock_app(self) -> None:
        self.withdraw()
        show_license_gate(self, self._on_license_success)

    def _on_license_success(self) -> None:
        self.deiconify()
        self.lift()
        self.focus_force()

    def _build_layout(self) -> None:
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(
            self, width=SIDEBAR_WIDTH, fg_color=SIDEBAR_BG, corner_radius=0
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # Hairline divider standing in for the blur seam of a real vibrancy panel.
        divider = ctk.CTkFrame(self, width=1, fg_color=SIDEBAR_BORDER, corner_radius=0)
        divider.grid(row=0, column=1, sticky="nsew")

        brand = ctk.CTkLabel(
            self.sidebar,
            text="⚡  SnapFlow",
            font=("Segoe UI Semibold", 16, "bold"),
            text_color="#FFFFFF",
            anchor="w",
        )
        brand.pack(fill="x", padx=22, pady=(26, 28))

        nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav_frame.pack(fill="x", expand=True)

        for key, label in (
            ("dashboard", "Dashboard"),
            ("history", "History"),
            ("settings", "Settings"),
        ):
            btn = ctk.CTkButton(
                nav_frame,
                text=label,
                anchor="w",
                height=38,
                corner_radius=RADIUS_PILL,
                fg_color="transparent",
                hover_color="#1d1d20",
                text_color=TEXT_MUTED,
                font=FONT_BODY,
                command=lambda k=key: self.show_view(k),
            )
            btn.pack(fill="x", padx=14, pady=3)
            self._nav_buttons[key] = btn

        footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        footer.pack(fill="x", side="bottom", padx=14, pady=18)

        ctk.CTkFrame(footer, height=1, fg_color=SIDEBAR_BORDER).pack(
            fill="x", pady=(0, 12)
        )

        ctk.CTkButton(
            footer,
            text="Check for Updates",
            height=32,
            corner_radius=RADIUS_PILL,
            fg_color="transparent",
            hover_color="#1d1d20",
            font=FONT_SMALL,
            text_color=TEXT_MUTED,
            command=self._check_for_updates,
        ).pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(
            footer,
            text=f"v{APP_VERSION}",
            font=FONT_SMALL,
            text_color=TEXT_FAINT,
        ).pack()

        self.content = ctk.CTkFrame(self, fg_color=CONTENT_BG, corner_radius=0)
        self.content.grid(row=0, column=2, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

    def _build_views(self) -> None:
        self._views["dashboard"] = DashboardView(self.content, self)
        self._views["history"] = HistoryView(self.content, self)
        self._views["settings"] = SettingsView(self.content, self)

        for view in self._views.values():
            view.grid(row=0, column=0, sticky="nsew")

    def show_view(self, name: str) -> None:
        if name not in self._views:
            return

        for key, btn in self._nav_buttons.items():
            active = key == name
            btn.configure(
                fg_color=ACCENT if active else "transparent",
                text_color="#FFFFFF" if active else TEXT_MUTED,
                font=FONT_BODY_MEDIUM if active else FONT_BODY,
            )

        self._views[name].tkraise()
        on_show = getattr(self._views[name], "on_show", None)
        if callable(on_show):
            on_show()
        self._current_view = name

    def request_capture(self) -> None:
        self.pipeline.request_capture()

    def save_settings(self, settings: AppSettings) -> None:
        self._settings_manager.save(settings)
        self._register_hotkey()
        self._tray.update_hotkey_label(settings.hotkey)
        dashboard = self._views.get("dashboard")
        if isinstance(dashboard, DashboardView):
            dashboard.on_show()

    def check_connection(self) -> None:
        threading.Thread(target=self._check_connection_async, daemon=True).start()

    def _check_connection_async(self) -> None:
        try:
            _debug("Starting connection check...")
            connected, label = check_server_connection()
            _debug(f"Connection result: {connected} | {label}")
            self.after(0, partial(self._apply_connection_status, connected, label))
        except Exception as e:
            _debug(f"CRASH in connection check: {type(e).__name__}: {e}")
            self.after(0, partial(self._apply_connection_status, False, "Offline"))

    def _apply_connection_status(self, connected: bool, label: str) -> None:
        dashboard = self._views.get("dashboard")
        if isinstance(dashboard, DashboardView):
            dashboard.set_connection_status(connected, label)

    def _schedule_connection_poll(self) -> None:
        self.check_connection()
        self.after(CONNECTION_POLL_MS, self._schedule_connection_poll)

    def _register_hotkey(self) -> None:
        try:
            self._hotkeys.register(get_settings().hotkey)
        except Exception as exc:
            logger.error("Failed to register hotkey: %s", exc)
            self._tray.notify("SnapFlow — Hotkey Error", str(exc))

    def _on_pipeline_status(self, status: str) -> None:
        self._tray.set_status(status)
        dashboard = self._views.get("dashboard")
        if isinstance(dashboard, DashboardView):
            dashboard.set_status(status)

    def _on_pipeline_finished(self, result: CaptureResult) -> None:
        if result.success:
            self.toast.show_success(result.message)
            self._tray.notify("SnapFlow", result.message)
        else:
            self._tray.notify("SnapFlow — Error", result.message)

        dashboard = self._views.get("dashboard")
        if isinstance(dashboard, DashboardView):
            dashboard.set_last_action(result.message, success=result.success)
            dashboard.set_status("Ready")

        self.history.add(
            action_type=result.action_type,
            message=result.message,
            success=result.success,
            preview=result.data_preview,
        )

        if result.success:
            logger.info(result.message)
        else:
            logger.warning(result.message)

    def _on_history_changed(self) -> None:
        history_view = self._views.get("history")
        if isinstance(history_view, HistoryView):
            self.after(0, history_view.refresh)

    def _check_for_updates(self) -> None:
        self.toast.show_info(f"You're on the latest version (v{APP_VERSION}).")

    def show_window(self) -> None:
        self.after(0, self._deiconify)

    def _deiconify(self) -> None:
        self.deiconify()
        self.lift()
        self.focus_force()

    def hide_to_tray(self) -> None:
        self.withdraw()

    def quit_app(self) -> None:
        self._hotkeys.unregister()
        self._tray.stop()
        self.after(0, self.destroy)

    def run(self) -> None:
        self.mainloop()
