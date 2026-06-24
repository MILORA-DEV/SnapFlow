"""Server connectivity checks."""
from __future__ import annotations
import logging
import sys
import requests

logger = logging.getLogger(__name__)

HEALTH_TIMEOUT = 8
SERVER_URL = "https://snapflow-yini.onrender.com"
API_KEY = "Sf9!kX27#mQ_vPz4"

def check_server_connection() -> tuple[bool, str]:
    print("=== CONNECTION CHECK ===", flush=True)
    print(f"URL: {SERVER_URL}/health", flush=True)
    print(f"API Key: {API_KEY[:4]}...", flush=True)
    
    url = f"{SERVER_URL}/health"
    headers = {"X-API-Key": API_KEY}
    
    try:
        print("Sending request...", flush=True)
        response = requests.get(url, headers=headers, timeout=HEALTH_TIMEOUT)
        print(f"Response status: {response.status_code}", flush=True)
        print(f"Response body: {response.text[:200]}", flush=True)
    except requests.ConnectionError as e:
        print(f"ConnectionError: {e}", flush=True)
        return False, "Offline"
    except requests.Timeout:
        print("Timeout!", flush=True)
        return False, "Timed out"
    except Exception as exc:
        print(f"Exception: {exc}", flush=True)
        return False, "Unreachable"

    if response.status_code == 401:
        return False, "Unauthorized"
    if response.ok:
        return True, "Connected"
    return False, f"Error {response.status_code}"
