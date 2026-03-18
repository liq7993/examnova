from typing import Literal

from pydantic import BaseModel

from app.schemas.study import StudyAnalyzeResponse
from app.schemas.thinking import ThinkingExpandResponse


class AgentRunRequest(BaseModel):
    task: Literal["study", "thinking"]
    payload: dict


class AgentRunResponse(BaseModel):
    task: str
    result: StudyAnalyzeResponse | ThinkingExpandResponse
