from fastapi import APIRouter

from app.core.dependencies.auth import CurrentUser
from app.modules.search.dependencies import SearchServiceDep
from app.modules.search.schemas import SearchRequest, SearchResponse

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
async def semantic_search(
    payload: SearchRequest,
    current_user: CurrentUser,
    service: SearchServiceDep,
) -> SearchResponse:
    return await service.semantic_search(current_user, payload)
