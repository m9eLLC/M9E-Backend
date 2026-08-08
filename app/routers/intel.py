from fastapi import APIRouter, Depends

from app.deps import get_current_user
from app.schemas.search import IntelResponse
from app.truth.envelope import stub_envelope

router = APIRouter(prefix="/v1/intel", tags=["intel"], dependencies=[Depends(get_current_user)])


@router.get("/{entity_id}", response_model=IntelResponse)
async def get_intel(entity_id: str):
    """Stub for Intelligence 06."""
    return IntelResponse(entity_id=entity_id, signals={}, truth=stub_envelope("intelligence-06/intel/stub"))
