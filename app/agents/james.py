import uuid
from typing import Optional

from supabase import Client

# Comparables must fall within this many years of the subject listing (Section 4.3).
YEAR_BAND = 2
# Simple, explainable hours adjustment: price moves this fraction per 100 hours of
# difference from the comparable set's average (fewer hours than average -> higher price).
HOURS_ADJUSTMENT_RATE_PER_100 = 0.005


def _fetch_listing_with_entity(supabase: Client, listing_id: str) -> Optional[dict]:
    resp = (
        supabase.table("ekg_listing")
        .select("*, ekg_entity(*)")
        .eq("listing_id", listing_id)
        .limit(1)
        .execute()
    )
    if not resp.data:
        return None
    return resp.data[0]


def _find_comparables(supabase: Client, entity: dict, exclude_listing_id: str) -> list:
    embedding = entity.get("embedding")
    if not embedding:
        return []
    year = entity.get("year")
    resp = supabase.rpc(
        "match_comparables",
        {
            "query_embedding": embedding,
            "filter_category": entity.get("category"),
            "filter_year_lo": (year - YEAR_BAND) if year else None,
            "filter_year_hi": (year + YEAR_BAND) if year else None,
            "exclude_listing_id": exclude_listing_id,
            "match_count": 25,
        },
    ).execute()
    return resp.data or []


def price_listing(supabase: Client, listing_id: str) -> dict:
    """James 07: retrieve comparables -> adjust -> derive price -> record lineage.

    Authority (Section 6.2, T-M5): writes ekg_valuation only. Never touches
    ekg_listing and never executes a transaction.
    """
    listing = _fetch_listing_with_entity(supabase, listing_id)
    if listing is None:
        raise ValueError(f"listing not found: {listing_id}")

    entity = listing.get("ekg_entity") or {}
    comparables = _find_comparables(supabase, entity, listing_id)

    subject_hours = listing.get("hours")
    subject_asking = float(listing["asking_price"]) if listing.get("asking_price") is not None else None

    if comparables:
        priced = [c for c in comparables if c.get("asking_price") is not None]
        total_weight = sum(c["similarity"] for c in priced) or 1.0
        base_price = sum(c["similarity"] * float(c["asking_price"]) for c in priced) / total_weight

        comp_hours = [c["hours"] for c in comparables if c.get("hours") is not None]
        avg_comp_hours = sum(comp_hours) / len(comp_hours) if comp_hours else None

        hours_adjustment_pct = 0.0
        if subject_hours is not None and avg_comp_hours is not None:
            hours_delta = avg_comp_hours - subject_hours
            hours_adjustment_pct = (hours_delta / 100) * HOURS_ADJUSTMENT_RATE_PER_100

        price_point = round(base_price * (1 + hours_adjustment_pct), 2)

        avg_similarity = total_weight / len(priced) if priced else 0.0
        confidence = round(min(1.0, avg_similarity * min(len(comparables), 5) / 5), 3)

        adjustments = {
            "method": "similarity_weighted_average",
            "hours_adjustment_pct": round(hours_adjustment_pct, 4),
            "avg_comparable_hours": avg_comp_hours,
            "subject_hours": subject_hours,
        }
        ordered_comparables = [
            {
                "listing_id": c["listing_id"],
                "similarity": round(c["similarity"], 4),
                "asking_price": c.get("asking_price"),
                "basis": "semantic+category+year_band",
            }
            for c in sorted(comparables, key=lambda c: c["similarity"], reverse=True)
        ]
    else:
        price_point = subject_asking
        confidence = 0.15
        adjustments = {
            "anchor": "asking_price",
            "note": "no comparables found in EKG; price anchored to seller's asking price",
        }
        ordered_comparables = []

    valuation_id = f"val_{uuid.uuid4().hex[:12]}"
    provenance = "james-07/pricing/v5.0"
    supabase.table("ekg_valuation").insert(
        {
            "valuation_id": valuation_id,
            "listing_id": listing_id,
            "price_point": price_point,
            "comparables": ordered_comparables,
            "adjustments": adjustments,
            "confidence": confidence,
            "provenance": provenance,
        }
    ).execute()

    return {
        "listing_id": listing_id,
        "price_point": price_point,
        "comparables": ordered_comparables,
        "adjustments": adjustments,
        "confidence": confidence,
        "provenance": provenance,
    }
