from app.schemas.agent import AgentRunRequest, AgentRunResponse
from app.schemas.study import StudyAnalyzeRequest
from app.schemas.thinking import ThinkingExpandRequest
from app.skills.learning import run_learning_skill
from app.skills.thinking import run_thinking_skill
from app.services.history_store import append_history, build_entry


def _truncate(text: str, limit: int = 80) -> str:
    cleaned = " ".join(text.split()).strip()
    if not cleaned:
        return "No content"
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1] + "…"


def _build_summary(task: str, payload: dict) -> str:
    if task == "study":
        return _truncate(str(payload.get("input_text", "")))
    return _truncate(str(payload.get("idea", "")))


def _record_history(task: str, payload: dict) -> None:
    try:
        summary = _build_summary(task, payload)
        append_history(build_entry(task, summary))
    except Exception:
        return


def run_agent(request: AgentRunRequest) -> AgentRunResponse:
    if request.task == "study":
        result = run_learning_skill(StudyAnalyzeRequest(**request.payload))
        _record_history("study", request.payload)
        return AgentRunResponse(task="study", result=result)

    result = run_thinking_skill(ThinkingExpandRequest(**request.payload))
    _record_history("thinking", request.payload)
    return AgentRunResponse(task="thinking", result=result)
