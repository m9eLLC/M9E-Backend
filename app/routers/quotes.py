from fastapi import APIRouter, Depends

from app.deps import get_current_user
from app.schemas.search import (
    FinanceQuoteRequest,
    FinanceQuoteResponse,
    LogisticsQuoteRequest,
    LogisticsQuoteResponse,
)
from app.truth.envelope import stub_envelope

router = APIRouter(prefix="/v1/quotes", tags=["quotes"], dependencies=[Depends(get_current_user)])


@router.post("/finance", response_model=FinanceQuoteResponse)
async def finance_quote(body: FinanceQuoteRequest):
    """Stub for Finance 04."""
    return FinanceQuoteResponse(
        listing_id=body.listing_id, options=[], truth=stub_envelope("finance-04/quote/stub")
    )


@router.post("/logistics", response_model=LogisticsQuoteResponse)
async def logistics_quote(body: LogisticsQuoteRequest):
    """Stub for Logistics 05."""
    return LogisticsQuoteResponse(
        listing_id=body.listing_id, options=[], truth=stub_envelope("logistics-05/quote/stub")
    )
