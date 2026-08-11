from fastapi import APIRouter, Depends, HTTPException

from app.agents import emma
from app.deps import get_current_user, get_supabase
from app.schemas.listings import (
    EkgEntity,
    InspectionRequest,
    InspectionResponse,
    ListingCreateRequest,
    ListingResponse,
    ValuationResponse,
)
from app.truth.envelope import envelope_with_confidence, stub_envelope

router = APIRouter(prefix="/v1/listings", tags=["listings"], dependencies=[Depends(get_current_user)])


@router.post("", status_code=201, response_model=ListingResponse)
async def create_listing(body: ListingCreateRequest):
    """Emma 01: normalize -> resolve/create entity -> embed -> insert listing (Section 4.2 EKG)."""
    try:
        result = emma.create_listing(get_supabase(), body.raw.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Emma 01 pipeline failed: {exc}") from exc

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
        truth=envelope_with_confidence("emma-01/ekg-enrich/v5.0", result["confidence"]),
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
    """Stub for James 07. Real pricing lands in Session 3 (Truth Layer + James 07)."""
    return ValuationResponse(
        listing_id=listing_id,
        truth=stub_envelope("james-07/pricing/stub"),
    )


@router.post("/{listing_id}/inspection", response_model=InspectionResponse)
async def request_inspection(listing_id: str, body: InspectionRequest):
    return InspectionResponse(
        listing_id=listing_id,
        truth=stub_envelope("inspection-03/assess/stub"),
    )
