import hashlib
import json
import re
import uuid
from typing import Optional

from anthropic import Anthropic
from openai import OpenAI
from supabase import Client

from app.config import settings

_anthropic_client: Optional[Anthropic] = None
_openai_client: Optional[OpenAI] = None

NORMALIZE_SYSTEM_PROMPT = """You are Emma 01, the M9E marketplace's listing-normalization agent.
Given a raw seller listing, extract the canonical equipment identity. Respond with ONLY a JSON object,
no other text, in this exact shape:

{"make": string, "model": string, "year": integer or null, "category": string (lowercase snake_case, e.g. "excavator", "wheel_loader", "skid_steer"), "confidence": float between 0 and 1}

Use your knowledge of industrial/construction equipment makes and models. If a field truly cannot be
determined from the input, use an empty string for make/model or null for year, and lower the
confidence accordingly."""


def _get_anthropic_client() -> Anthropic:
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = Anthropic(api_key=settings.anthropic_api_key)
    return _anthropic_client


def _get_openai_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=settings.openai_api_key)
    return _openai_client


def _slug(value: Optional[str]) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "na"


def entity_id_for(make: str, model: str, year: Optional[int], category: str, title: str = "") -> str:
    """Deterministic entity id so resolve-or-create is idempotent without a lookup race.

    When make, model, and category are all unidentified, falling back to a single shared
    bucket (e.g. ekg_unknown_na_na_na) would wrongly merge unrelated equipment that just
    happen to share "no info" - a freeze dryer and a spray gun are not the same entity.
    In that case, hash the raw title instead: still deterministic/idempotent for an exact
    re-submission of the same listing, but distinct listings stay distinct entities.
    """
    if not make and not model and (not category or category == "unknown"):
        title_hash = hashlib.sha1(title.strip().lower().encode()).hexdigest()[:12]
        return f"ekg_unident_{title_hash}"
    return f"ekg_{_slug(category)}_{_slug(make)}_{_slug(model)}_{year if year else 'na'}"


def normalize_listing(title: str, description: Optional[str]) -> dict:
    """Raw seller text -> canonical equipment identity, via Claude."""
    client = _get_anthropic_client()
    user_content = f"Title: {title}\nDescription: {description or ''}"
    resp = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=300,
        system=NORMALIZE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )
    text = "".join(block.text for block in resp.content if block.type == "text").strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    try:
        data = json.loads(text)
    except (ValueError, json.JSONDecodeError):
        data = {"make": "", "model": "", "year": None, "category": "unknown", "confidence": 0.0}

    return {
        "make": (data.get("make") or "").strip(),
        "model": (data.get("model") or "").strip(),
        "year": data.get("year"),
        "category": (data.get("category") or "unknown").strip().lower(),
        "confidence": float(data.get("confidence") or 0.0),
    }


def compute_embedding(text: str) -> list[float]:
    client = _get_openai_client()
    resp = client.embeddings.create(model=settings.embedding_model, input=text)
    return resp.data[0].embedding


def resolve_or_create_entity(
    supabase: Client, make: str, model: str, year: Optional[int], category: str, embedding: list[float], title: str = ""
) -> dict:
    entity_id = entity_id_for(make, model, year, category, title)

    existing = supabase.table("ekg_entity").select("*").eq("entity_id", entity_id).limit(1).execute()
    if existing.data:
        return existing.data[0]

    row = {
        "entity_id": entity_id,
        "make": make or "unknown",
        "model": model or "unknown",
        "year": year,
        "category": category or "unknown",
        "spec": {},
        "embedding": embedding,
    }
    supabase.table("ekg_entity").insert(row).execute()
    return row


def create_listing(supabase: Client, raw: dict) -> dict:
    """Emma 01 pipeline: normalize -> resolve/create entity -> embed -> insert listing.

    Section 4.2 EKG schema, Section 9 Session 2 acceptance criterion.
    """
    normalized = normalize_listing(raw.get("title", ""), raw.get("description"))

    embed_text = " ".join(
        str(v) for v in [normalized["make"], normalized["model"], normalized["year"], normalized["category"], raw.get("description")] if v
    ).strip()
    embedding = compute_embedding(embed_text or raw.get("title", ""))

    entity = resolve_or_create_entity(
        supabase,
        normalized["make"],
        normalized["model"],
        normalized["year"],
        normalized["category"],
        embedding,
        raw.get("title", ""),
    )

    listing_id = f"lst_{uuid.uuid4().hex[:12]}"
    listing_row = {
        "listing_id": listing_id,
        "entity_id": entity["entity_id"],
        "hours": raw.get("hours"),
        "location": raw.get("location"),
        "asking_price": raw.get("asking_price"),
        "raw": raw,
        "status": "active",
    }
    supabase.table("ekg_listing").insert(listing_row).execute()

    return {
        "listing_id": listing_id,
        "entity": entity,
        "confidence": normalized["confidence"],
        "provenance": "emma-01/ekg-enrich/v5.0",
    }


def get_listing(supabase: Client, listing_id: str) -> Optional[dict]:
    resp = (
        supabase.table("ekg_listing")
        .select("*, ekg_entity(*)")
        .eq("listing_id", listing_id)
        .limit(1)
        .execute()
    )
    if not resp.data:
        return None

    row = resp.data[0]
    entity = row.get("ekg_entity") or {}
    return {"listing_id": row["listing_id"], "entity": entity}
