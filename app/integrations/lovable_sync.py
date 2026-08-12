import logging
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

LOVABLE_HOOK_URL = "https://ai-m9e-vista.lovable.app/api/public/hooks/receive-agent-listing"
TIMEOUT_S = 15.0


def sync_listing(ekg_listing_id: str, raw: dict, entity: dict) -> None:
    """Best-effort push of a newly created listing into the Lovable marketplace UI's
    own browsable table, so it shows up alongside the rest of the inventory.

    Never raises - a sync failure shouldn't undo Emma's successful EKG write. Lovable's
    receive-agent-listing hook is idempotent on ekg_listing_id, so retrying is safe.
    """
    if not settings.internal_api_key:
        logger.warning("lovable sync skipped for %s: INTERNAL_API_KEY not configured", ekg_listing_id)
        return

    location = raw.get("location") or ""
    city, _, region = location.partition(",")
    city = city.strip() or None
    region = region.strip() or None

    price_cents: Optional[int] = None
    if raw.get("asking_price") is not None:
        price_cents = round(float(raw["asking_price"]) * 100)

    payload = {
        "ekg_listing_id": ekg_listing_id,
        "title": raw.get("title") or entity.get("model") or "Untitled listing",
        "manufacturer": entity.get("make") if entity.get("make") not in (None, "unknown") else None,
        "model": entity.get("model") if entity.get("model") not in (None, "unknown") else None,
        "year": entity.get("year"),
        "price_cents": price_cents,
        "location_city": city,
        "location_region": region,
        "description": raw.get("description"),
        "short_description": (raw.get("description") or "")[:280] or None,
        "category_slug": entity.get("category") or "industrial",
    }

    try:
        resp = httpx.post(
            LOVABLE_HOOK_URL,
            json=payload,
            headers={"X-Internal-Key": settings.internal_api_key},
            timeout=TIMEOUT_S,
        )
        if resp.status_code != 200:
            logger.warning("lovable sync failed for %s: HTTP %s %s", ekg_listing_id, resp.status_code, resp.text[:300])
    except Exception as exc:
        logger.warning("lovable sync failed for %s: %s", ekg_listing_id, exc)
