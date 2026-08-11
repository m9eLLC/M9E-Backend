from fastapi import APIRouter, Depends, HTTPException

from app.agents import emma, james
from app.deps import get_current_user, get_supabase
from app.schemas.listings import (
    EkgEntity,
    InspectionRequest,
    InspectionResponse,
    ListingCreateRequest,
    ListingResponse,
    ValuationResponse,
)
from app.truth.envelope import stub_envelope
from app.truth.gate import TruthViolation, truth_gate

router = APIRouter(prefix="/v1/listings", tags=["listings"], dependencies=[Depends(get_current_user)])


@router.post("", status_code=201, response_model=ListingResponse)
async def create_listing(body: ListingCreateRequest):
    """Emma 01: normalize -> resolve/create entity -> embed -> insert listing (Section 4.2 EKG)."""
    supabase = get_supabase()
    raw = body.raw.model_dump()
    try:
        result = emma.create_listing(supabase, raw)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Emma 01 pipeline failed: {exc}") from exc

    try:
        truth = truth_gate(supabase, "emma-01", "ekg-enrich", raw, result)
    except TruthViolation as tv:
        raise HTTPException(
            status_code=422,
            detail=f"Truth Layer rejected Emma 01 output: failed={tv.failed} audit_ref={tv.audit_ref}",
        ) from tv

    entity = result["entity"]
    return ListingResponse(
        listing_id=result["listing_id"],
        entity=EkgEntity(
            make=entity.get("make"),
            model=entity.get("model"),
            year=entity.get("year"),
            category=entity.get("category"),
            ekg_entity_id=entity.get("entity_id"),
        ),
        truth=truth,
    )


@router.get("/{listing_id}", response_model=ListingResponse)
async def get_listing(listing_id: str):
    result = emma.get_listing(get_supabase(), listing_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Listing not found")

    entity = result["entity"]
    return ListingResponse(
        listing_id=result["listing_id"],
        entity=EkgEntity(
            make=entity.get("make"),
            model=entity.get("model"),
            year=entity.get("year"),
            category=entity.get("category"),
            ekg_entity_id=entity.get("entity_id"),
        ),
        truth=stub_envelope("gateway/listings-read/v1"),
    )


@router.get("/{listing_id}/valuation", response_model=ValuationResponse)
async def get_valuation(listing_id: str):
    """James 07: retrieve comparables -> adjust -> derive price -> record lineage (Section 6.2)."""
    supabase = get_supabase()
    try:
        result = james.price_listing(supabase, listing_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"James 07 pipeline failed: {exc}") from exc

    try:
        truth = truth_gate(supabase, "james-07", "pricing", {"listing_id": listing_id}, result)
    except TruthViolation as tv:
        raise HTTPException(
            status_code=422,
            detail=f"Truth Layer rejected James 07 output: failed={tv.failed} audit_ref={tv.audit_ref}",
        ) from tv

    return ValuationResponse(
        listing_id=result["listing_id"],
        price_point=result["price_point"],
        comparables=result["comparables"],
        adjustments=result["adjustments"],
        truth=truth,
    )


@router.post("/{listing_id}/inspection", response_model=InspectionResponse)
async def request_inspection(listing_id: str, body: InspectionRequest):
    return InspectionResponse(
        listing_id=listing_id,
        truth=stub_envelope("inspection-03/assess/stub"),
    )
