import secrets

from fastapi import Header, HTTPException, status

from app.config import settings


async def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    supplied = x_api_key or ""
    if not secrets.compare_digest(supplied.encode("utf-8"), settings.api_key.encode("utf-8")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "unauthorized", "message": "Invalid API key."},
            headers={"WWW-Authenticate": "ApiKey"},
        )
