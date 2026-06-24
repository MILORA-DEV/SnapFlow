"""SnapFlow processing server."""
from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from openai import OpenAI
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SNAPFLOW_API_KEY = os.getenv("SNAPFLOW_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "openai/gpt-4o")
OPENROUTER_REFERER = os.getenv("OPENROUTER_REFERER", "https://snapflow-yini.onrender.com")

# Gumroad product identifier used for license verification. Not a secret —
# safe to ship a default here, but can be overridden via env if the product
# is ever recreated under a different id.
GUMROAD_PRODUCT_ID = os.getenv("GUMROAD_PRODUCT_ID", "vmc8y0u9wfnT4MLlAX1jUQ==")
GUMROAD_VERIFY_URL = "https://api.gumroad.com/v2/licenses/verify"

SYSTEM_PROMPT = """Analyze this screenshot. If it contains a date/time, return a calendar event. If it contains an address, return a map link. If it contains text, return clean markdown. If it contains code, return a code block. Output must be valid JSON: {"type": "action_type", "data": "content"}. Types: calendar, map, markdown, code. If nothing useful, use type error."""

app = FastAPI(title="SnapFlow Server", version="1.0.0")

class ProcessRequest(BaseModel):
    image: str = Field(..., description="Base64-encoded PNG screenshot")

class ProcessResponse(BaseModel):
    type: str
    data: str

class VerifyLicenseRequest(BaseModel):
    license_key: str = Field(..., description="License key entered by the user")
    increment_uses_count: bool = Field(
        True, description="Whether this check should count as a Gumroad license use"
    )

class VerifyLicenseResponse(BaseModel):
    valid: bool
    message: str

async def verify_key(x_api_key: str) -> None:
    if not SNAPFLOW_API_KEY or x_api_key != SNAPFLOW_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key.")

@app.get("/health")
async def health(x_api_key: str = Header(..., alias="X-API-Key")):
    await verify_key(x_api_key)
    return {"status": "ok"}

@app.post("/verify-license", response_model=VerifyLicenseResponse)
async def verify_license(request: VerifyLicenseRequest, x_api_key: str = Header(..., alias="X-API-Key")):
    await verify_key(x_api_key)

    license_key = request.license_key.strip()
    if not license_key:
        return VerifyLicenseResponse(valid=False, message="License key is required.")

    body = urllib.parse.urlencode(
        {
            "product_id": GUMROAD_PRODUCT_ID,
            "license_key": license_key,
            "increment_uses_count": "true" if request.increment_uses_count else "false",
        }
    ).encode()

    try:
        req = urllib.request.Request(GUMROAD_VERIFY_URL, data=body, method="POST")
        with urllib.request.urlopen(req, timeout=15) as resp:
            payload: dict[str, Any] = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode())
        except (json.JSONDecodeError, ValueError):
            payload = {"success": False, "message": "Gumroad rejected the verification request."}
    except Exception as exc:
        logger.error("Gumroad license verification failed: %s", exc)
        raise HTTPException(status_code=502, detail="Could not reach the license server.") from exc

    if not payload.get("success"):
        message = payload.get("message", "Invalid license key.")
        logger.info("License rejected: %s", message)
        return VerifyLicenseResponse(valid=False, message=message)

    purchase = payload.get("purchase", {}) or {}
    if purchase.get("refunded") or purchase.get("chargebacked"):
        return VerifyLicenseResponse(valid=False, message="This license has been refunded or charged back.")

    logger.info("License verified for purchase id=%s", purchase.get("id", "?"))
    return VerifyLicenseResponse(valid=True, message="License activated.")

@app.post("/process", response_model=ProcessResponse)
async def process_screenshot(request: ProcessRequest, x_api_key: str = Header(..., alias="X-API-Key")):
    await verify_key(x_api_key)
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY not configured.")
    client = OpenAI(
        api_key=OPENAI_API_KEY,
        base_url="https://openrouter.ai/api/v1",
        default_headers={"HTTP-Referer": OPENROUTER_REFERER, "X-Title": "SnapFlow"},
    )
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": [
                    {"type": "text", "text": "Analyze this screenshot and return the JSON action."},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{request.image.strip()}"}},
                ]},
            ],
            max_tokens=2048,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Vision API failed: {exc}") from exc
    raw = (response.choices[0].message.content or "").strip()
    try:
        payload: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail=f"Invalid JSON: {raw[:200]}") from exc
    action_type = str(payload.get("type", "")).strip().lower()
    data = payload.get("data", "")
    if isinstance(data, dict):
        data = json.dumps(data)
    else:
        data = str(data)
    if not action_type or action_type == "error":
        raise HTTPException(status_code=422, detail=data or "No actionable content.")
    logger.info("Processed: type=%s", action_type)
    return ProcessResponse(type=action_type, data=data)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
