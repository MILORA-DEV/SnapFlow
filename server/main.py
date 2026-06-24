"""SnapFlow processing server."""
from __future__ import annotations

import json
import logging
import os
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from openai import OpenAI
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ENV CONFIG
SNAPFLOW_API_KEY = os.getenv("SNAPFLOW_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "openai/gpt-4o")
OPENROUTER_REFERER = os.getenv("OPENROUTER_REFERER", "https://snapflow-yini.onrender.com")

# 🔑 NEW: LICENSE SYSTEM
PRODUCT_ID = os.getenv("PRODUCT_ID", "vmc8y0u9wfnT4MLlAX1jUQ==")

SYSTEM_PROMPT = """Analyze this screenshot. If it contains a date/time, return a calendar event.
If it contains an address, return a map link. If it contains text, return clean markdown.
If it contains code, return a code block.
Output must be valid JSON with exactly this shape:
{"type": "action_type", "data": "the_processed_content"}"""

app = FastAPI(title="SnapFlow Server", version="1.1.0")


class ProcessRequest(BaseModel):
    image: str = Field(..., description="Base64-encoded PNG screenshot")


class ProcessResponse(BaseModel):
    type: str
    data: str


# ---------------------------
# AUTH + LICENSE CHECK
# ---------------------------
async def verify_access(
    x_api_key: str = Header(..., alias="X-API-Key"),
    x_license_key: str = Header(..., alias="X-License-Key"),
    x_product_id: str = Header(None, alias="X-Product-Id"),
) -> None:
    # Server API key check
    if not SNAPFLOW_API_KEY:
        raise HTTPException(status_code=503, detail="Server API key not configured.")

    if x_api_key != SNAPFLOW_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key.")

    # License key check (basic version)
    if not x_license_key:
        raise HTTPException(status_code=401, detail="Missing license key.")

    # Optional product lock
    if x_product_id and x_product_id != PRODUCT_ID:
        raise HTTPException(status_code=403, detail="Invalid product ID.")

    # Placeholder license validation (replace later with Gumroad/Stripe API)
    if len(x_license_key) < 10:
        raise HTTPException(status_code=401, detail="Invalid license key.")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/process", response_model=ProcessResponse)
async def process_screenshot(
    request: ProcessRequest,
    x_api_key: str = Header(..., alias="X-API-Key"),
    x_license_key: str = Header(..., alias="X-License-Key"),
    x_product_id: str = Header(None, alias="X-Product-Id"),
):
    await verify_access(x_api_key, x_license_key, x_product_id)

    if not OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY not configured.")

    image_b64 = request.image.strip()
    if not image_b64:
        raise HTTPException(status_code=400, detail="Image payload is empty.")

    client = OpenAI(
        api_key=OPENAI_API_KEY,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": OPENROUTER_REFERER,
            "X-Title": "SnapFlow",
        },
    )

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analyze this screenshot and return JSON."},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                        },
                    ],
                },
            ],
            max_tokens=2048,
        )
    except Exception as exc:
        logger.exception("Vision API call failed")
        raise HTTPException(status_code=502, detail=str(exc))

    raw = (response.choices[0].message.content or "").strip()

    try:
        payload: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail=f"Bad JSON: {raw[:200]}")

    action_type = str(payload.get("type", "")).lower()
    data = payload.get("data", "")

    data = json.dumps(data) if isinstance(data, dict) else str(data)

    if action_type == "error":
        raise HTTPException(status_code=422, detail=data)

    return ProcessResponse(type=action_type, data=data)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
