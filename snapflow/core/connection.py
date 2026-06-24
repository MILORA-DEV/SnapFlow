"""Server connectivity checks."""

from __future__ import annotations

import logging
import os
import traceback
from datetime import datetime
from pathlib import Path

import requests

from snapflow.core.config import get_server_config

logger = logging.getLogger(__name__)

HEALTH_TIMEOUT = 60  # Increased to handle Render free-tier cold starts

# Hardcoded gatekeeper fallbacks, mirroring snapflow.core.config — kept here
# too so a connection check never fails outright due to a missing .env.
SERVER_URL = "https://snapflow-yini.onrender.com"
API_KEY = "Sf9!kX27#mQ_vPz4"

APPDATA_SNAPFLOW = Path(os.environ.get("APPDATA", Path.home())) / "SnapFlow"
DEBUG_LOG = APPDATA_SNAPFLOW / "debug.txt"
CONNECTION_DEBUG_LOG = APPDATA_SNAPFLOW / "connection_debug.txt"


def _debug(msg: str) -> None:
    DEBUG_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(DEBUG_LOG, "a") as f:
        f.write(msg + "\n")


def _conn_debug(msg: str) -> None:
    """Dedicated connection-check log: URL, API key prefix, status, tracebacks."""
    CONNECTION_DEBUG_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(CONNECTION_DEBUG_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {msg}\n")


def check_server_connection() -> tuple[bool, str]:
    """
    Ping the SnapFlow server /health endpoint.
    Returns (connected, status_message).
    """
    server = get_server_config()
    url = f"{server.url or SERVER_URL}/health"
    key = server.api_key or API_KEY
    headers = {"X-API-Key": key}

    _debug(f"Checking connection: {url}")
    _conn_debug(f"URL: {url} | API key prefix: {key[:4]}")

    try:
        response = requests.get(url, headers=headers, timeout=HEALTH_TIMEOUT)
    except requests.ConnectionError:
        _debug("Connection failed: offline")
        _conn_debug(f"ConnectionError (offline):\n{traceback.format_exc()}")
        return False, "Offline"
    except requests.Timeout:
        _debug("Connection failed: timed out")
        _conn_debug(f"Timeout:\n{traceback.format_exc()}")
        return False, "Timed out"
    except requests.RequestException as exc:
        _debug(f"Connection failed: {exc}")
        _conn_debug(f"RequestException:\n{traceback.format_exc()}")
        logger.debug("Health check failed: %s", exc)
        return False, "Unreachable"

    _debug(f"Connection response: {response.status_code}")
    _conn_debug(f"Response status code: {response.status_code}")

    if response.status_code == 401:
        return False, "Unauthorized"

    if response.ok:
        return True, "Connected"

    return False, f"Error {response.status_code}"
