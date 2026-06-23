"""Application settings and paths (client-side only)."""
from __future__ import annotations
import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from dotenv import dotenv_values, load_dotenv

def get_data_dir() -> Path:
    """Persistent app data directory."""
    if getattr(sys, "frozen", False):
        base = Path(os.environ.get("APPDATA", Path.home())) / "SnapFlow"
    else:
        base = Path(__file__).resolve().parent.parent.parent / ".snapflow"
    base.mkdir(parents=True, exist_ok=True)
    return base

DATA_DIR = get_data_dir()
SETTINGS_PATH = DATA_DIR / "settings.json"
HISTORY_PATH = DATA_DIR / "history.json"
OUTPUT_DIR = DATA_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ENV_PATH always lives in AppData so users never have to touch it
ENV_PATH = DATA_DIR / ".env"

# If no .env exists in AppData yet, seed it from the bundled one (dev) or leave blank
if not ENV_PATH.exists():
    if not getattr(sys, "frozen", False):
        # Dev mode: try project root .env
        project_env = Path(__file__).resolve().parent.parent.parent / ".env"
        if project_env.exists():
            import shutil
            shutil.copy(project_env, ENV_PATH)
    else:
        # Frozen: write a blank template so load_dotenv doesn't fail
        ENV_PATH.write_text(
            "SNAPFLOW_SERVER_URL=\nSNAPFLOW_API_KEY=\nSNAPFLOW_HOTKEY=ctrl+shift+a\n"
        )

load_dotenv(ENV_PATH)

@dataclass
class AppSettings:
    hotkey: str = "ctrl+shift+a"

@dataclass(frozen=True)
class ServerConfig:
    url: str
    api_key: str

class SettingsManager:
    """Loads and persists client settings."""
    def __init__(self) -> None:
        self._settings = AppSettings()
        self.load()

    @property
    def settings(self) -> AppSettings:
        return self._settings

    def load(self) -> AppSettings:
        env = dotenv_values(ENV_PATH) if ENV_PATH.exists() else {}
        if SETTINGS_PATH.exists():
            try:
                raw = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
                self._settings = AppSettings(
                    hotkey=raw.get("hotkey") or env.get("SNAPFLOW_HOTKEY", "ctrl+shift+a"),
                )
            except (json.JSONDecodeError, TypeError):
                self._settings = self._defaults_from_env(env)
        else:
            self._settings = self._defaults_from_env(env)
        self._apply_to_env()
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
            hotkey=env.get("SNAPFLOW_HOTKEY", "ctrl+shift+a") or "ctrl+shift+a",
        )

    def _apply_to_env(self) -> None:
        os.environ["SNAPFLOW_HOTKEY"] = self._settings.hotkey

    def _sync_env_file(self) -> None:
        existing = dotenv_values(ENV_PATH) if ENV_PATH.exists() else {}
        lines = [
            f"SNAPFLOW_HOTKEY={self._settings.hotkey}",
            f"SNAPFLOW_SERVER_URL={existing.get('SNAPFLOW_SERVER_URL', '')}",
            f"SNAPFLOW_API_KEY={existing.get('SNAPFLOW_API_KEY', '')}",
        ]
        ENV_PATH.write_text("\n".join(lines) + "\n")

_settings_manager: SettingsManager | None = None

def get_settings_manager() -> SettingsManager:
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager

def get_settings() -> AppSettings:
    return get_settings_manager().settings

def get_server_config() -> ServerConfig:
    """Read server config — checks settings.json first, then .env in AppData."""
    url = ""
    api_key = ""

    if SETTINGS_PATH.exists():
        try:
            raw = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            url = raw.get("server_url", url)
            api_key = raw.get("api_key", api_key)
        except (json.JSONDecodeError, TypeError):
            pass

    if not api_key or not url:
        env = dotenv_values(ENV_PATH) if ENV_PATH.exists() else {}
        url = env.get("SNAPFLOW_SERVER_URL", url)
        api_key = env.get("SNAPFLOW_API_KEY", api_key)

    return ServerConfig(
        url=url.rstrip("/") if url else "",
        api_key=api_key,
    )
