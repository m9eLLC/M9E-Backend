from fastapi import APIRouter, Depends

from app.deps import get_current_user
from app.schemas.search import SearchRequest, SearchResponse
from app.truth.envelope import stub_envelope

router = APIRouter(prefix="/v1/search", tags=["search"], dependencies=[Depends(get_current_user)])


@router.post("", response_model=SearchResponse)
async def search(body: SearchRequest):
    """Stub for Mila 02: embed intent -> semantic comparable retrieval -> rank."""
    return SearchResponse(matches=[], truth=stub_envelope("mila-02/search/stub"))
