from fastapi import APIRouter, Query

from app.schemas.study_note import StudyNoteCreateRequest, StudyNoteItem, StudyNoteListResponse
from app.services.study_note_store import add_study_note, recent_study_notes

router = APIRouter(prefix="/api/study-notes", tags=["study-notes"])


@router.post("", response_model=dict)
def create_study_note(request: StudyNoteCreateRequest) -> dict:
    add_study_note(
        course=request.course,
        question_text=request.question_text,
        session_key=request.session_key,
        result=request.result.model_dump(),
    )
    return {"ok": True}


@router.get("/recent", response_model=StudyNoteListResponse)
def get_recent_study_notes(limit: int = Query(default=10, ge=1, le=50)) -> StudyNoteListResponse:
    items = [StudyNoteItem(**item) for item in recent_study_notes(limit=limit)]
    return StudyNoteListResponse(items=items)

