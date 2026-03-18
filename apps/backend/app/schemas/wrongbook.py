from pydantic import BaseModel


class WrongbookAddRequest(BaseModel):
    question_text: str
    summary: str
    course: str | None = None
    difficulty: str | None = None
    knowledge_points: list[str] = []


class WrongbookItem(BaseModel):
    timestamp: str
    question_text: str
    summary: str
    course: str | None
    difficulty: str | None
    knowledge_points: list[str]


class WrongbookRecentResponse(BaseModel):
    items: list[WrongbookItem]
