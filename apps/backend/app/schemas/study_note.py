from pydantic import BaseModel

from app.schemas.study import StudyAnalyzeResponse


class StudyNoteCreateRequest(BaseModel):
    course: str
    question_text: str
    session_key: str | None = None
    result: StudyAnalyzeResponse


class StudyNoteItem(BaseModel):
    timestamp: str
    course: str
    question_text: str
    session_key: str | None = None
    result: StudyAnalyzeResponse


class StudyNoteListResponse(BaseModel):
    items: list[StudyNoteItem]

