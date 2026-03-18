from fastapi import APIRouter, Query

from app.schemas.wrongbook import WrongbookAddRequest, WrongbookRecentResponse
from app.services.wrongbook_store import append_wrongbook, build_entry, load_wrongbook

router = APIRouter(prefix="/api/wrongbook", tags=["wrongbook"])


@router.post("/add")
def add_wrongbook(request: WrongbookAddRequest) -> dict:
    entry = build_entry(
        question_text=request.question_text,
        summary=request.summary,
        course=request.course,
        difficulty=request.difficulty,
        knowledge_points=request.knowledge_points,
    )
    append_wrongbook(entry)
    return {"ok": True}


@router.get("/recent", response_model=WrongbookRecentResponse)
def recent_wrongbook(limit: int = Query(default=6, ge=1, le=50)) -> WrongbookRecentResponse:
    items = load_wrongbook(limit)
    return WrongbookRecentResponse(items=items)
