from fastapi import APIRouter

from app.schemas.thinking import ThinkingExpandRequest, ThinkingExpandResponse
from app.skills.thinking import run_thinking_skill

router = APIRouter(prefix="/api/thinking", tags=["thinking"])


@router.post("/expand", response_model=ThinkingExpandResponse)
def expand_thinking(request: ThinkingExpandRequest) -> ThinkingExpandResponse:
    return run_thinking_skill(request)
