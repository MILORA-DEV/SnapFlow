"""Server connectivity checks."""
from __future__ import annotations
import logging
import os
from pathlib import Path
import requests

logger = logging.getLogger(__name__)

HEALTH_TIMEOUT = 8
SERVER_URL = "https://snapflow-yini.onrender.com"
API_KEY = "Sf9!kX27#mQ_vPz4"

LOG_FILE = Path(os.environ.get("APPDATA", Path.home())) / "SnapFlow" / "connection_debug.txt"

def _log(msg: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(msg + "\n")

def check_server_connection() -> tuple[bool, str]:
    _log("=== CONNECTION CHECK ===")
    _log(f"URL: {SERVER_URL}/health")
    _log(f"API Key: {API_KEY[:4]}...")
    
    url = f"{SERVER_URL}/health"
    headers = {"X-API-Key": API_KEY}
    
    try:
        _log("Sending request...")
        response = requests.get(url, headers=headers, timeout=HEALTH_TIMEOUT)
        _log(f"Response status: {response.status_code}")
        _log(f"Response body: {response.text[:200]}")
    except requests.ConnectionError as e:
        _log(f"ConnectionError: {e}")
        return False, "Offline"
    except requests.Timeout:
        _log("Timeout!")
        return False, "Timed out"
    except Exception as exc:
        _log(f"Exception: {type(exc).__name__}: {exc}")
        return False, "Unreachable"

    if response.status_code == 401:
        return False, "Unauthorized"
    if response.ok:
        return True, "Connected"
    return False, f"Error {response.status_code}"
