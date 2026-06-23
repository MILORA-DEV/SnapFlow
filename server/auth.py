"""API key authentication for SnapFlow clients."""

from fastapi import Header, HTTPException, status

from server.config import SNAPFLOW_API_KEY


async def verify_client_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> None:
    if not SNAPFLOW_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Server API key is not configured.",
        )
    if x_api_key != SNAPFLOW_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )
