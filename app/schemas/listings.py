from typing import Optional

from pydantic import BaseModel

from app.truth.envelope import TruthEnvelope


class RawListingInput(BaseModel):
    title: str
    hours: Optional[int] = None
    location: Optional[str] = None
    asking_price: Optional[float] = None
    description: Optional[str] = None


class ListingCreateRequest(BaseModel):
    raw: RawListingInput


class EkgEntity(BaseModel):
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    category: Optional[str] = None
    ekg_entity_id: Optional[str] = None


class ListingResponse(BaseModel):
    listing_id: str
    entity: EkgEntity
    truth: TruthEnvelope


class ValuationResponse(BaseModel):
    listing_id: str
    price_point: Optional[float] = None
    comparables: list[dict] = []
    adjustments: dict = {}
    truth: TruthEnvelope


class InspectionRequest(BaseModel):
    notes: Optional[str] = None


class InspectionResponse(BaseModel):
    listing_id: str
    condition: Optional[str] = None
    findings: list[str] = []
    truth: TruthEnvelope
