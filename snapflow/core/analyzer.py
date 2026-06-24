"""Vision analysis via SnapFlow server."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

import requests

from snapflow.core.config import get_server_config

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 90  # Increased to handle Render free-tier cold starts


@dataclass
class AnalysisResult:
    type: str
    data: str


class AnalyzerError(Exception):
    """Raised when screenshot analysis fails."""


def analyze_screenshot(image_b64: str) -> AnalysisResult:
    """Send a base64 PNG to the SnapFlow server for processing."""
    server = get_server_config()
    # API key is now hardcoded via gatekeeper - no local check needed

    # Ensure clean URL construction (no double slashes)
    base_url = server.url.rstrip("/")
    url = f"{base_url}/process"
    headers = {"X-API-Key": server.api_key}

    logger.info("Sending analysis request to: %s", url)

    try:
        response = requests.post(
            url,
            json={"image": image_b64},
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
    except requests.ConnectionError as exc:
        raise AnalyzerError(
            "Cannot reach SnapFlow server. Check your connection and try again."
        ) from exc
    except requests.Timeout as exc:
        raise AnalyzerError("Server request timed out. Please try again.") from exc
    except requests.RequestException as exc:
        logger.exception("Server request failed")
        raise AnalyzerError(f"Server request failed: {exc}") from exc

    if response.status_code == 401:
        raise AnalyzerError("Authentication failed. This client is not authorized.")

    if not response.ok:
        detail = response.text
        try:
            detail = response.json().get("detail", detail)
        except ValueError:
            pass
        raise AnalyzerError(f"Server error ({response.status_code}): {detail}")

    try:
        payload = response.json()
    except ValueError as exc:
        raise AnalyzerError("Invalid response from server.") from exc

    action_type = str(payload.get("type", "")).strip().lower()
    data = payload.get("data", "")

    if isinstance(data, dict):
        data = json.dumps(data)
    else:
        data = str(data)

    if not action_type or not data.strip():
        raise AnalyzerError("Server returned an incomplete response.")

    return AnalysisResult(type=action_type, data=data)
