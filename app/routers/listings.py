import uuid

from fastapi import APIRouter, Depends

from app.deps import get_current_user
from app.schemas.listings import (
    EkgEntity,
    InspectionRequest,
    InspectionResponse,
    ListingCreateRequest,
    ListingResponse,
    ValuationResponse,
)
from app.truth.envelope import stub_envelope

router = APIRouter(prefix="/v1/listings", tags=["listings"], dependencies=[Depends(get_current_user)])


@router.post("", status_code=201, response_model=ListingResponse)
async def create_listing(body: ListingCreateRequest):
    """Stub for Emma 01: normalize -> resolve/create entity -> embed -> insert listing.
    Real implementation lands in Session 2 against the EKG schema (Section 4.2).
    """
    listing_id = f"lst_{uuid.uuid4().hex[:12]}"
    return ListingResponse(
        listing_id=listing_id,
        entity=EkgEntity(),
        truth=stub_envelope("emma-01/ekg-enrich/stub"),
    )


@router.get("/{listing_id}", response_model=ListingResponse)
async def get_listing(listing_id: str):
    return ListingResponse(
        listing_id=listing_id,
        entity=EkgEntity(),
        truth=stub_envelope("gateway/listings-read/stub"),
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
