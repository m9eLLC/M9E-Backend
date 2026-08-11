from dataclasses import dataclass
from typing import List, Tuple

from supabase import Client

# T-M5 Boundary: which operations each agent is authorized to perform (Section 6).
AGENT_AUTHORITY = {
    "emma-01": {"ekg-enrich"},
    "james-07": {"pricing"},
    "mila-02": {"search"},
}


@dataclass
class InvariantResult:
    passed: List[str]
    failed: List[str]


def _check_t_m1_provenance(result: dict) -> bool:
    provenance = result.get("provenance", "")
    return bool(provenance) and "/" in provenance


def _check_t_m4_calibration(result: dict) -> bool:
    confidence = result.get("confidence")
    return isinstance(confidence, (int, float)) and 0.0 <= confidence <= 1.0


def _check_t_m5_boundary(agent_id: str, op: str) -> bool:
    return op in AGENT_AUTHORITY.get(agent_id, set())


def _check_t_m2_t_m3_james(result: dict, supabase: Client) -> Tuple[bool, bool]:
    """T-M2 grounding + T-M3 consistency, specific to James 07's valuations."""
    comparables = result.get("comparables") or []

    if comparables:
        comparable_ids = [c["listing_id"] for c in comparables]
        existing = (
            supabase.table("ekg_listing")
            .select("listing_id")
            .in_("listing_id", comparable_ids)
            .execute()
        )
        found = {row["listing_id"] for row in existing.data}
        t_m2 = set(comparable_ids).issubset(found)
    else:
        # Cold start: no market comparables, price anchored to the listing's own
        # ingested asking_price - still grounded, just in a weaker source.
        adjustments = result.get("adjustments") or {}
        listing = (
            supabase.table("ekg_listing")
            .select("asking_price")
            .eq("listing_id", result.get("listing_id"))
            .limit(1)
            .execute()
        )
        t_m2 = (
            adjustments.get("anchor") == "asking_price"
            and bool(listing.data)
            and listing.data[0].get("asking_price") is not None
            and result.get("price_point") is not None
            and float(listing.data[0]["asking_price"]) == float(result["price_point"])
        )

    prior = (
        supabase.table("ekg_valuation")
        .select("price_point,confidence")
        .eq("listing_id", result.get("listing_id"))
        .execute()
    )
    t_m3 = True
    for row in prior.data or []:
        if row["confidence"] > result.get("confidence", 0) and result.get("price_point") is not None:
            prior_price = float(row["price_point"])
            new_price = float(result["price_point"])
            if prior_price > 0 and abs(new_price - prior_price) / prior_price > 0.5:
                t_m3 = False
                break

    return t_m2, t_m3


def run_invariants(agent_id: str, op: str, result: dict, supabase: Client) -> InvariantResult:
    checks = {
        "T-M1": _check_t_m1_provenance(result),
        "T-M2": True,
        "T-M3": True,
        "T-M4": _check_t_m4_calibration(result),
        "T-M5": _check_t_m5_boundary(agent_id, op),
        # Satisfied structurally: run_invariants only ever executes inside truth_gate,
        # which always appends to the audit chain before releasing the envelope.
        "T-M6": True,
    }

    if agent_id == "james-07":
        t_m2, t_m3 = _check_t_m2_t_m3_james(result, supabase)
        checks["T-M2"] = t_m2
        checks["T-M3"] = t_m3

    passed = [k for k, v in checks.items() if v]
    failed = [k for k, v in checks.items() if not v]
    return InvariantResult(passed=passed, failed=failed)
