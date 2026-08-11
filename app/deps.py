from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import create_client, Client

from app.config import settings

bearer_scheme = HTTPBearer(auto_error=False)


def get_supabase() -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> dict:
    """Verifies the Supabase JWT against the Supabase Auth server and resolves the acting user.

    Per Section 3: 'All requests are authenticated with the Supabase JWT; the gateway
    verifies the token and resolves the acting user before routing.'
    """
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    client = create_client(settings.supabase_url, settings.supabase_publishable_key)
    try:
        resp = client.auth.get_user(credentials.credentials)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    if resp is None or resp.user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    return {"id": resp.user.id, "email": resp.user.email}


async def get_current_user_or_service(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    x_internal_api_key: Optional[str] = Header(default=None),
) -> dict:
    """Accepts either a Supabase user JWT (browser callers) or a shared internal API key
    (trusted server-to-server callers, e.g. the Lovable marketplace UI's own backend,
    which has no way to hold a Supabase user session for this project). The internal key
    is a coarse "trusted internal caller" credential, not a per-user identity - fine for
    read-mostly endpoints in this router, none of which expose anything beyond what's
    already meant to be shown to marketplace visitors.
    """
    if settings.internal_api_key and x_internal_api_key == settings.internal_api_key:
        return {"id": "service", "email": None}
    return await get_current_user(credentials)
