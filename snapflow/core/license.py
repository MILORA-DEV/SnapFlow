"""License validation via Gumroad's built-in license API."""
from __future__ import annotations
import json
import os
from pathlib import Path
import requests

GUMROAD_PRODUCT_PERMALINK = "YOUR_PRODUCT_PERMALINK"  # e.g. "snapflow" from your Gumroad URL
LICENSE_PATH = Path(os.environ.get("APPDATA", Path.home())) / "SnapFlow" / "license.json"

def save_license(key: str) -> None:
    LICENSE_PATH.parent.mkdir(parents=True, exist_ok=True)
    LICENSE_PATH.write_text(json.dumps({"key": key}), encoding="utf-8")

def load_saved_license() -> str | None:
    try:
        if LICENSE_PATH.exists():
            data = json.loads(LICENSE_PATH.read_text(encoding="utf-8"))
            return data.get("key")
    except Exception:
        pass
    return None

def validate_license(key: str) -> tuple[bool, str]:
    """
    Validate a license key against Gumroad's API.
    Returns (is_valid, message).
    """
    if not key or not key.strip():
        return False, "Please enter a license key."
    try:
        response = requests.post(
            "https://api.gumroad.com/v2/licenses/verify",
            data={
                "product_permalink": GUMROAD_PRODUCT_PERMALINK,
                "license_key": key.strip(),
            },
            timeout=10,
        )
        data = response.json()
        if data.get("success"):
            # Check it hasn't been refunded or chargebacked
            purchase = data.get("purchase", {})
            if purchase.get("refunded") or purchase.get("chargebacked"):
                return False, "This license has been refunded and is no longer valid."
            return True, "License activated successfully."
        else:
            return False, data.get("message", "Invalid license key.")
    except requests.exceptions.Timeout:
        return False, "Connection timed out. Check your internet and try again."
    except requests.exceptions.ConnectionError:
        return False, "No internet connection. Please connect and try again."
    except Exception as e:
        return False, f"Verification failed: {str(e)}"

def is_licensed() -> bool:
    """Quick check — is there a saved license key?"""
    key = load_saved_license()
    return bool(key and key.strip())
