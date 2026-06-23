"""SnapFlow processing server."""
from __future__ import annotations

import json
import logging
import os
from typing import Any

from fastapi import FastAPI, Header, HTTPException, status
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

SYSTEM_PROMPT = """Analyze this screenshot. If it contains a date/time, return a calendar event.
If it contains an address, return a map link. If it contains text, return clean markdown.
If it contains code, return a code block.
Output must be valid JSON with exactly this shape:
{"type": "action_type", "data": "the_processed_content"}
Use these action_type values:
- "calendar" — data is JSON string with keys: title, start (ISO 8601), end (ISO 8601, optional), location (optional), description (optional)
- "map" — data is a full Google Maps URL for the address
- "markdown" — data is clean markdown text
- "code" — data is the code content (no markdown fences)
If nothing useful is detected, use type "error" and data with a short explanation."""

app = FastAPI(title="SnapFlow Server", version="1.0.0")


class ProcessRequest(BaseModel):
    image: str = Field(..., description="Base64-encoded PNG screenshot")


class ProcessResponse(BaseModel):
    type: str
    data: str


async def verify_key(x_api_key: str = Header(..., alias="X-API-Key")) -> None:
    if not SNAPFLOW_API_KEY:
        raise HTTPException(status_code=503, detail="Server API key not configured.")
    if x_api_key != SNAPFLOW_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key.")


@app.get("/health")
async def health(x_api_key: str = Header(..., alias="X-API-Key")):
    await verify_key(x_api_key)
    return {"status": "ok"}


@app.post("/process", response_model=ProcessResponse)
async def process_screenshot(
    request: ProcessRequest,
    x_api_key: str = Header(..., alias="X-API-Key"),
):
    await verify_key(x_api_key)

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
        raise HTTPException(status_code=502, detail=f"Vision API call failed: {exc}") from exc

    raw = (response.choices[0].message.content or "").strip()
    if not raw:
        raise HTTPException(status_code=502, detail="Empty response from vision model.")

    try:
        payload: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail=f"Invalid JSON from vision model: {raw[:200]}") from exc

    action_type = str(payload.get("type", "")).strip().lower()
    data = payload.get("data", "")

    if isinstance(data, dict):
        data = json.dumps(data)
    else:
        data = str(data)

    if not action_type:
        raise HTTPException(status_code=502, detail="Vision model response missing 'type'.")

    if action_type == "error":
        raise HTTPException(status_code=422, detail=data or "No actionable content detected.")

    if not data.strip():
        raise HTTPException(status_code=502, detail="Vision model response missing 'data'.")

    logger.info("Processed screenshot: type=%s", action_type)
    return ProcessResponse(type=action_type, data=data)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
