"""Application settings and paths (client-side only)."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from dotenv import dotenv_values, load_dotenv

# Hardcoded gatekeeper defaults (Gumroad-licensed SnapFlow server). Used as
# fallbacks when no .env override is present, so a frozen build always has
# a working server to talk to.
GUMROAD_SERVER_URL = "https://snapflow-yini.onrender.com"
GUMROAD_API_KEY = "Sf9!kX27#mQ_vPz4"
DEFAULT_HOTKEY = "ctrl+shift+a"

DEBUG_LOG = Path(os.environ.get("APPDATA", Path.home())) / "SnapFlow" / "debug.txt"


def _debug(msg: str) -> None:
    DEBUG_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(DEBUG_LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\n")


if getattr(sys, "frozen", False):
    # Running as PyInstaller executable
    PROJECT_ROOT = Path(sys._MEIPASS)
else:
    # Running from source
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def get_data_dir() -> Path:
    """Persistent app data directory (portable when running from source)."""
    if getattr(sys, "frozen", False):
        base = Path(os.environ.get("APPDATA", Path.home())) / "SnapFlow"
    else:
        base = PROJECT_ROOT / ".snapflow"
    base.mkdir(parents=True, exist_ok=True)
    return base


DATA_DIR = get_data_dir()
SETTINGS_PATH = DATA_DIR / "settings.json"
HISTORY_PATH = DATA_DIR / "history.json"
OUTPUT_DIR = DATA_DIR / "output"
ENV_PATH = DATA_DIR / ".env"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _ensure_env_file() -> None:
    """On first launch (esp. frozen), seed .env with working defaults."""
    if ENV_PATH.exists():
        _debug(f"config: .env already exists at {ENV_PATH}")
        return
    _debug(f"config: .env missing, writing defaults to {ENV_PATH}")
    ENV_PATH.write_text(
        "\n".join(
            [
                f"SNAPFLOW_SERVER_URL={GUMROAD_SERVER_URL}",
                f"SNAPFLOW_API_KEY={GUMROAD_API_KEY}",
                f"SNAPFLOW_HOTKEY={DEFAULT_HOTKEY}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


_debug(f"config: frozen={getattr(sys, 'frozen', False)} DATA_DIR={DATA_DIR} ENV_PATH={ENV_PATH}")
_ensure_env_file()


@dataclass
class AppSettings:
    hotkey: str = "ctrl+shift+a"


@dataclass(frozen=True)
class ServerConfig:
    url: str
    api_key: str


class SettingsManager:
    """Loads and persists client settings (hotkey only)."""

    def __init__(self) -> None:
        self._settings = AppSettings()
        load_dotenv(ENV_PATH)
        self.load()

    @property
    def settings(self) -> AppSettings:
        return self._settings

    def load(self) -> AppSettings:
        _debug(f"config: loading settings, SETTINGS_PATH exists={SETTINGS_PATH.exists()}")
        env = dotenv_values(ENV_PATH) if ENV_PATH.exists() else {}

        if SETTINGS_PATH.exists():
            try:
                raw = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
                self._settings = AppSettings(
                    hotkey=raw.get("hotkey") or env.get("SNAPFLOW_HOTKEY", DEFAULT_HOTKEY),
                )
            except (json.JSONDecodeError, TypeError):
                self._settings = self._defaults_from_env(env)
        else:
            self._settings = self._defaults_from_env(env)

        self._apply_to_env()
        _debug(f"config: settings loaded, hotkey={self._settings.hotkey}")
        return self._settings

    def save(self, settings: AppSettings) -> None:
        self._settings = settings
        SETTINGS_PATH.write_text(
            json.dumps(asdict(settings), indent=2),
            encoding="utf-8",
        )
        self._sync_env_file()
        self._apply_to_env()

    def _defaults_from_env(self, env: dict) -> AppSettings:
        return AppSettings(
            hotkey=env.get("SNAPFLOW_HOTKEY", DEFAULT_HOTKEY) or DEFAULT_HOTKEY,
        )

    def _apply_to_env(self) -> None:
        os.environ["SNAPFLOW_HOTKEY"] = self._settings.hotkey

    def _sync_env_file(self) -> None:
        # Never let a save() overwrite the server URL/API key with an empty
        # value — always fall back to whatever's on disk, then the hardcoded
        # gatekeeper defaults, so a frozen build can't end up "Offline".
        existing = dotenv_values(ENV_PATH) if ENV_PATH.exists() else {}
        server_url = existing.get("SNAPFLOW_SERVER_URL") or GUMROAD_SERVER_URL
        api_key = existing.get("SNAPFLOW_API_KEY") or GUMROAD_API_KEY
        lines = [
            f"SNAPFLOW_HOTKEY={self._settings.hotkey}",
            f"SNAPFLOW_SERVER_URL={server_url}",
            f"SNAPFLOW_API_KEY={api_key}",
        ]
        ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
        _debug(f"config: synced .env (hotkey={self._settings.hotkey}, url={server_url})")


_settings_manager: SettingsManager | None = None


def get_settings_manager() -> SettingsManager:
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager


def get_settings() -> AppSettings:
    return get_settings_manager().settings


def get_server_config() -> ServerConfig:
    """Server URL and client auth key — hardcoded gatekeeper, not exposed in UI."""
    load_dotenv(ENV_PATH, override=True)
    url = (os.getenv("SNAPFLOW_SERVER_URL") or GUMROAD_SERVER_URL).rstrip("/")
    api_key = os.getenv("SNAPFLOW_API_KEY") or GUMROAD_API_KEY
    _debug(f"config: get_server_config -> url={url} api_key_prefix={api_key[:4]}")
    return ServerConfig(url=url, api_key=api_key)
