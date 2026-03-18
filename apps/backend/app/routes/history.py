from fastapi import APIRouter, Query

from app.schemas.history import HistoryExportResponse, HistoryRecentResponse
from app.services.history_store import clear_history, load_all, load_recent

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("/recent", response_model=HistoryRecentResponse)
def recent_history(limit: int = Query(default=6, ge=1, le=50)) -> HistoryRecentResponse:
    items = load_recent(limit)
    return HistoryRecentResponse(items=items)


@router.get("/export", response_model=HistoryExportResponse)
def export_history() -> HistoryExportResponse:
    items = load_all()
    return HistoryExportResponse(items=items)


@router.delete("/clear")
def clear_history_route() -> dict:
    cleared = clear_history()
    return {"cleared": cleared}
