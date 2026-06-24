"""License verification against the SnapFlow gatekeeper server."""

from __future__ import annotations

import json
import logging
import time

import requests

from snapflow.core.config import DATA_DIR, get_server_config

logger = logging.getLogger(__name__)

LICENSE_PATH = DATA_DIR / "license.json"
VERIFY_TIMEOUT = 30
REVALIDATE_INTERVAL_SECONDS = 3 * 24 * 60 * 60  # re-check with Gumroad every 3 days


def _read_license_data() -> dict:
    if not LICENSE_PATH.exists():
        return {}
    try:
        return json.loads(LICENSE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def is_licensed() -> bool:
    """Check the locally cached license state (no network call)."""
    data = _read_license_data()
    return bool(data.get("licensed")) and bool(data.get("license_key"))


def get_saved_license_key() -> str:
    """Return the last license key entered, if any (for pre-filling the gate)."""
    return str(_read_license_data().get("license_key", ""))


def save_license(license_key: str) -> None:
    LICENSE_PATH.parent.mkdir(parents=True, exist_ok=True)
    LICENSE_PATH.write_text(
        json.dumps(
            {"licensed": True, "license_key": license_key, "last_verified": time.time()},
            indent=2,
        ),
        encoding="utf-8",
    )


def clear_license() -> None:
    if LICENSE_PATH.exists():
        LICENSE_PATH.unlink()


def _call_verify_endpoint(
    license_key: str, *, increment_uses_count: bool = True
) -> tuple[bool | None, str]:
    """
    Hit the SnapFlow server's /verify-license endpoint.

    Returns (True, msg) if Gumroad confirms the key is valid, (False, msg) if
    Gumroad explicitly rejects it (bad key, refunded, chargebacked), or
    (None, msg) if the result is inconclusive (network error, timeout,
    server error). Callers must treat None as "couldn't tell" — not as a
    rejection — so a flaky connection can never look like a revoked license.
    """
    server = get_server_config()
    url = f"{server.url}/verify-license"
    headers = {"X-API-Key": server.api_key}

    try:
        response = requests.post(
            url,
            json={
                "license_key": license_key,
                "increment_uses_count": increment_uses_count,
            },
            headers=headers,
            timeout=VERIFY_TIMEOUT,
        )
    except requests.ConnectionError:
        return None, "Cannot reach the license server. Check your connection."
    except requests.Timeout:
        return None, "License check timed out. Please try again."
    except requests.RequestException as exc:
        logger.debug("License verification failed: %s", exc)
        return None, "License check failed."

    if response.status_code == 401:
        return False, "Invalid license key."

    if not response.ok:
        return None, f"License server error ({response.status_code})."

    try:
        payload = response.json()
    except ValueError:
        return None, "Invalid response from license server."

    if not payload.get("valid"):
        return False, str(payload.get("message", "Invalid license key."))

    return True, str(payload.get("message", "License activated."))


def verify_license(license_key: str) -> tuple[bool, str]:
    """
    Verify a license key against the SnapFlow gatekeeper server (the
    interactive activation flow). On success, persists it locally so future
    launches skip the network call. Returns (success, message).
    """
    license_key = license_key.strip()
    if not license_key:
        return False, "Enter a license key."

    result, message = _call_verify_endpoint(license_key, increment_uses_count=True)
    if result is not True:
        return False, message

    save_license(license_key)
    return True, message


def revalidate_license(*, force: bool = False) -> bool:
    """
    Best-effort periodic re-check of the cached license against Gumroad.

    Only ever revokes the cached license on an explicit "invalid" answer
    (bad key, refunded, chargebacked) from the server — network errors and
    server hiccups are inconclusive and leave the cached license untouched,
    so a bad connection can never lock out an already-activated user.

    Returns True if the cached license should still be considered valid.
    """
    data = _read_license_data()
    license_key = data.get("license_key")
    if not (data.get("licensed") and license_key):
        return False

    last_verified = data.get("last_verified", 0)
    if not force and (time.time() - last_verified) < REVALIDATE_INTERVAL_SECONDS:
        return True

    result, message = _call_verify_endpoint(license_key, increment_uses_count=False)
    if result is False:
        logger.info("License revoked on revalidation: %s", message)
        clear_license()
        return False
    if result is True:
        save_license(license_key)  # refreshes last_verified
    # result is None (inconclusive): leave the cached license alone.
    return True
