from typing import Optional

from pydantic import BaseModel

from app.truth.envelope import TruthEnvelope


class SearchRequest(BaseModel):
    category: Optional[str] = None
    constraints: dict = {}
    query: Optional[str] = None


class SearchMatch(BaseModel):
    listing_id: str
    similarity: float
    rationale: Optional[str] = None


class SearchResponse(BaseModel):
    matches: list[SearchMatch] = []
    truth: TruthEnvelope


class FinanceQuoteRequest(BaseModel):
    listing_id: str
    down_payment: Optional[float] = None
    term_months: Optional[int] = None


class FinanceQuoteResponse(BaseModel):
    listing_id: str
    options: list[dict] = []
    truth: TruthEnvelope


class LogisticsQuoteRequest(BaseModel):
    listing_id: str
    destination: Optional[str] = None


class LogisticsQuoteResponse(BaseModel):
    listing_id: str
    options: list[dict] = []
    truth: TruthEnvelope


class IntelResponse(BaseModel):
    entity_id: str
    signals: dict = {}
    truth: TruthEnvelope
