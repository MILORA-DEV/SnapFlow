"""API key authentication for SnapFlow clients."""

import logging
from fastapi import Header, HTTPException, status
from server.config import SNAPFLOW_API_KEY

logger = logging.getLogger(__name__)

async def verify_client_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> None:
    """
    Validates the incoming X-API-Key header against the server's master key.
    Blocks unauthorized requests before they hit your AI endpoints.
    """
    # 1. Check if you forgot to set the password on Render
    if not SNAPFLOW_API_KEY:
        logger.error("Security Alert: SNAPFLOW_API_KEY is missing from server environment configurations.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Server API key authentication is unconfigured.",
        )
        
    # 2. Compare the client's password with your invented password
    if x_api_key != SNAPFLOW_API_KEY:
        logger.warning("Unauthorized Access Attempt: Invalid API key provided by client.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key. Access denied.",
        )
