from typing import Literal

from pydantic import BaseModel


class HistoryItem(BaseModel):
    timestamp: str
    task: Literal["study", "thinking", "companion"]
    summary: str


class HistoryRecentResponse(BaseModel):
    items: list[HistoryItem]


class HistoryExportResponse(BaseModel):
    items: list[HistoryItem]
