"""Server connectivity checks."""

from __future__ import annotations

import logging

import requests

from snapflow.core.config import get_server_config

logger = logging.getLogger(__name__)

HEALTH_TIMEOUT = 8


def check_server_connection() -> tuple[bool, str]:
    """
    Ping the SnapFlow server /health endpoint.
    Returns (connected, status_message).
    """
    server = get_server_config()
    if not server.api_key:
        return False, "Not configured"

    url = f"{server.url}/health"
    headers = {"X-API-Key": server.api_key}

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
