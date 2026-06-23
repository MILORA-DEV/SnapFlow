"""SnapFlow processing server."""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, status
from openai import OpenAI
from pydantic import BaseModel, Field

# Ensure these imports exist in your 'server' folder
from server.auth import verify_client_api_key
from server.config import (
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OPENROUTER_BASE_URL,
    OPENROUTER_REFERER,
    SYSTEM_PROMPT,
)

# GUI imports (customtkinter) have been removed to prevent 
# server-side crashes in a headless environment.

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SnapFlow Server", version="1.0.0")

class ProcessRequest(BaseModel):
    image: str = Field(..., description="Base64-encoded PNG screenshot")

class ProcessResponse(BaseModel):
    type: str
    data: str

@app.get("/health")
async def health(_: None = Depends(verify_client_api_key)) -> dict[str, str]:
    return {"status": "ok"}

@app.post("/process", response_model=ProcessResponse)
async def process_image(
    body: ProcessRequest,
    _: None = Depends(verify_client_api_key),
) -> ProcessResponse:
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OPENAI_API_KEY is not configured on the server.",
        )

    image_b64 = body.image.strip()
    if not image_b64:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image payload is empty.",
        )

    client = OpenAI(
        api_key=OPENAI_API_KEY,
        base_url=OPENROUTER_BASE_URL,
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
                        {"type": "text", "text": "Analyze this screenshot and return the JSON action."},
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
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Vision API call failed: {exc}",
        ) from exc

    raw = (response.choices[0].message.content or "").strip()
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Empty response from the vision model.",
        )

    try:
        payload: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Invalid JSON from vision model: {raw[:200]}",
        ) from exc

    action_type = str(payload.get("type", "")).strip().lower()
    data = payload.get("data", "")

    if isinstance(data, dict):
        data = json.dumps(data)
    else:
        data = str(data)

    if not action_type:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Vision model response missing 'type'.",
        )

    if action_type == "error":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=data or "No actionable content detected in screenshot.",
        )

    if not data.strip():
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Vision model response missing 'data'.",
        )

    return ProcessResponse(type=action_type, data=data)
