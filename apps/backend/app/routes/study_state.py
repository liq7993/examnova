from fastapi import APIRouter, HTTPException, Query

from app.schemas.study_state import (
    DueSessionItem,
    DueSessionListResponse,
    StudySessionAckRequest,
    StudySessionHeartbeatRequest,
    StudySessionStartRequest,
    StudySessionStateResponse,
)
from app.services.study_state_store import (
    acknowledge_review,
    get_session,
    heartbeat_session,
    list_due_sessions,
    start_or_resume_session,
)

router = APIRouter(prefix="/api/study-state", tags=["study-state"])


def _to_response(session) -> StudySessionStateResponse:
    return StudySessionStateResponse(**session.__dict__)


@router.post("/session", response_model=StudySessionStateResponse)
def start_session(request: StudySessionStartRequest) -> StudySessionStateResponse:
    session = start_or_resume_session(
        course=request.course,
        question_text=request.question_text,
        topic_label=request.topic_label,
        knowledge_points=request.knowledge_points,
        mini_quiz=request.mini_quiz,
        memory_tips=request.memory_tips,
        review_mode=request.review_mode,
        explanation_mode=request.explanation_mode,
        difficulty=request.difficulty,
    )
    return _to_response(session)


@router.get("/session/{session_key}", response_model=StudySessionStateResponse)
def read_session(session_key: str) -> StudySessionStateResponse:
    try:
        return _to_response(get_session(session_key))
    except KeyError as error:
        raise HTTPException(status_code=404, detail="session not found") from error


@router.post("/heartbeat", response_model=StudySessionStateResponse)
def heartbeat(request: StudySessionHeartbeatRequest) -> StudySessionStateResponse:
    try:
        return _to_response(heartbeat_session(request.session_key, request.active_seconds))
    except KeyError as error:
        raise HTTPException(status_code=404, detail="session not found") from error


@router.post("/ack", response_model=StudySessionStateResponse)
def ack_review(request: StudySessionAckRequest) -> StudySessionStateResponse:
    try:
        return _to_response(acknowledge_review(request.session_key, request.trigger_type))
    except KeyError as error:
        raise HTTPException(status_code=404, detail="session not found") from error


@router.get("/due", response_model=DueSessionListResponse)
def due_sessions(limit: int = Query(default=10, ge=1, le=50)) -> DueSessionListResponse:
    sessions = list_due_sessions(limit=limit)
    items = [
        DueSessionItem(
            session_key=session.session_key,
            course=session.course,
            topic_label=session.topic_label,
            question_text=session.question_text,
            review_mode=session.review_mode,
            strategy_name=session.strategy_name,
            wall_elapsed_minutes=session.wall_elapsed_minutes,
            focused_minutes=session.focused_minutes,
            curve_due_count=session.curve_due_count,
            focus_due_count=session.focus_due_count,
            next_curve_prompt=session.next_curve_prompt,
            next_focus_prompt=session.next_focus_prompt,
            mini_quiz=session.mini_quiz,
            memory_tips=session.memory_tips,
        )
        for session in sessions
    ]
    return DueSessionListResponse(items=items)

