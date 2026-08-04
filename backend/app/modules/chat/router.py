from fastapi import APIRouter

from app.core.dependencies.auth import CurrentUser
from app.modules.chat.dependencies import ChatServiceDep
from app.modules.chat.schemas import ChatAskRequest, ChatAskResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/ask", response_model=ChatAskResponse)
async def ask_question(
    payload: ChatAskRequest,
    current_user: CurrentUser,
    service: ChatServiceDep,
) -> ChatAskResponse:
    return await service.ask(current_user, payload)
