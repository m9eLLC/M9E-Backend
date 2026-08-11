from fastapi import APIRouter

from app.config import settings

router = APIRouter(tags=["health"])


@router.get("/v1/health")
async def health():
    return {"status": "ok"}


@router.get("/v1/health/env-check")
async def env_check():
    """Temporary diagnostic: presence/length only, never actual values. Remove once resolved."""
    return {
        "internal_api_key": {
            "set": bool(settings.internal_api_key),
            "length": len(settings.internal_api_key),
        }
    }
