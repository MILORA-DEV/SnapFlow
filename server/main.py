"""
Example backend server for SnapFlow desktop app.
This is a reference implementation for the Render backend.
Deploy this to Render or your preferred hosting service.
"""

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import logging

# Gatekeeper API key (must match desktop client)
GATEKEEPER_KEY = "Sf9!kX27#mQ_vPz4"

app = FastAPI(title="SnapFlow Server")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProcessRequest(BaseModel):
    """Request model matching desktop client payload."""
    image: str  # Base64 encoded PNG image


class ProcessResponse(BaseModel):
    """Response model matching desktop client expectations."""
    type: str  # Action type: "calendar", "code", "map_link", "markdown", etc.
    data: str  # Action data (URL, code snippet, etc.)


@app.get("/health")
async def health_check():
    """Health check endpoint for desktop client connection polling."""
    return {"status": "ok"}


@app.post("/process", response_model=ProcessResponse)
async def process_screenshot(
    request: ProcessRequest,
    x_api_key: str = Header(..., alias="X-API-Key")
):
    """
    Process screenshot and return action.
    
    Desktop client sends:
    - Header: X-API-Key: Sf9!kX27#mQ_vPz4
    - Body: {"image": "base64_encoded_png"}
    
    This endpoint should:
    1. Validate the API key
    2. Decode the base64 image
    3. Send to AI vision model (OpenAI GPT-4 Vision, etc.)
    4. Parse the response into an action type and data
    5. Return the action to the desktop client
    """
    # Validate API key
    if x_api_key != GATEKEEPER_KEY:
        logger.warning("Unauthorized access attempt with key: %s", x_api_key[:10] + "...")
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    logger.info("Processing screenshot request (image length: %d chars)", len(request.image))
    
    # TODO: Implement your AI vision logic here
    # 1. Decode base64 image
    # 2. Send to OpenAI GPT-4 Vision or similar
    # 3. Parse response to determine action type
    # 4. Return appropriate action
    
    # Example placeholder response
    # Replace this with your actual AI processing logic
    return ProcessResponse(
        type="markdown",
        data="# Example Response\n\nThis is where your AI analysis results go."
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
