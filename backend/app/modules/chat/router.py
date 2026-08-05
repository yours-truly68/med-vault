import asyncio
import logging
from fastapi import APIRouter, Request

from app.core.dependencies.auth import CurrentUser
from app.modules.chat.dependencies import ChatServiceDep
from app.modules.chat.schemas import ChatAskRequest, ChatAskResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


from fastapi.responses import StreamingResponse

@router.post("/ask", response_model=ChatAskResponse)
async def ask_question(
    payload: ChatAskRequest,
    current_user: CurrentUser,
    service: ChatServiceDep,
    request: Request,
) -> ChatAskResponse:
    try:
        return await service.ask(current_user, payload, request=request)
    except asyncio.CancelledError:
        logger.info(
            "[AI Stack Cancellation] Client disconnected. Aborting LLM request and releasing provider connections. (user_id=%s)",
            current_user.id,
        )
        raise


@router.post("/stream")
async def stream_question(
    payload: ChatAskRequest,
    current_user: CurrentUser,
    service: ChatServiceDep,
    request: Request,
) -> StreamingResponse:
    return StreamingResponse(
        service.stream_ask(current_user, payload, request=request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
