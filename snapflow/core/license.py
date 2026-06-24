"""License verification against the SnapFlow gatekeeper server."""

from __future__ import annotations

import json
import logging

import requests

from snapflow.core.config import DATA_DIR, get_server_config

logger = logging.getLogger(__name__)

LICENSE_PATH = DATA_DIR / "license.json"
VERIFY_TIMEOUT = 30


def is_licensed() -> bool:
    """Check the locally cached license state (no network call)."""
    if not LICENSE_PATH.exists():
        return False
    try:
        data = json.loads(LICENSE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    return bool(data.get("licensed")) and bool(data.get("license_key"))


def get_saved_license_key() -> str:
    """Return the last license key entered, if any (for pre-filling the gate)."""
    if not LICENSE_PATH.exists():
        return ""
    try:
        data = json.loads(LICENSE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return ""
    return str(data.get("license_key", ""))


def save_license(license_key: str) -> None:
    LICENSE_PATH.parent.mkdir(parents=True, exist_ok=True)
    LICENSE_PATH.write_text(
        json.dumps({"licensed": True, "license_key": license_key}, indent=2),
        encoding="utf-8",
    )


def clear_license() -> None:
    if LICENSE_PATH.exists():
        LICENSE_PATH.unlink()


def verify_license(license_key: str) -> tuple[bool, str]:
    """
    Verify a license key against the SnapFlow gatekeeper server.
    On success, persists it locally so future launches skip the network check.
    Returns (success, message).
    """
    license_key = license_key.strip()
    if not license_key:
        return False, "Enter a license key."

    server = get_server_config()
    url = f"{server.url}/verify-license"
    headers = {"X-API-Key": server.api_key}

    try:
        response = requests.post(
            url,
            json={"license_key": license_key},
            headers=headers,
            timeout=VERIFY_TIMEOUT,
        )
    except requests.ConnectionError:
        return False, "Cannot reach the license server. Check your connection."
    except requests.Timeout:
        return False, "License check timed out. Please try again."
    except requests.RequestException as exc:
        logger.debug("License verification failed: %s", exc)
        return False, "License check failed."

    if response.status_code == 401:
        return False, "Invalid license key."

    if not response.ok:
        return False, f"License server error ({response.status_code})."

    try:
        payload = response.json()
    except ValueError:
        return False, "Invalid response from license server."

    if not payload.get("valid"):
        return False, str(payload.get("message", "Invalid license key."))

    save_license(license_key)
    return True, "License activated."
