"""Server connectivity checks."""
from __future__ import annotations
import logging
import requests

logger = logging.getLogger(__name__)

HEALTH_TIMEOUT = 8
SERVER_URL = "https://snapflow-yini.onrender.com"
API_KEY = "Sf9!kX27#mQ_vPz4"

def check_server_connection() -> tuple[bool, str]:
    url = f"{SERVER_URL}/health"
    headers = {"X-API-Key": API_KEY}
    try:
        response = requests.get(url, headers=headers, timeout=HEALTH_TIMEOUT)
    except requests.ConnectionError:
        return False, "Offline"
    except requests.Timeout:
        return False, "Timed out"
    except requests.RequestException as exc:
        logger.debug("Health check failed: %s", exc)
        return False, "Unreachable"
    if response.status_code == 401:
        return False, "Unauthorized"
    if response.ok:
        return True, "Connected"
    return False, f"Error {response.status_code}"
