from fastapi import APIRouter

from app.config import settings

router = APIRouter(tags=["health"])


@router.get("/v1/health")
async def health():
    return {"status": "ok"}


@router.get("/v1/health/env-check")
async def env_check():
    """Temporary diagnostic: reports presence/length only, never actual values.
    Remove once the Render env var issue is resolved.
    """
    fields = [
        "supabase_url",
        "supabase_publishable_key",
        "supabase_service_role_key",
        "allowed_origins",
        "anthropic_api_key",
        "openai_api_key",
    ]
    return {f: {"set": bool(getattr(settings, f)), "length": len(getattr(settings, f))} for f in fields}
