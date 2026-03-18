from pydantic import BaseModel, Field


class StudySessionStartRequest(BaseModel):
    course: str
    question_text: str
    topic_label: str
    knowledge_points: list[str] = Field(default_factory=list)
    mini_quiz: list[str] = Field(default_factory=list)
    memory_tips: list[str] = Field(default_factory=list)
    review_mode: str = "auto"
    explanation_mode: str = "concise"
    difficulty: str = "中"


class StudySessionHeartbeatRequest(BaseModel):
    session_key: str
    active_seconds: int = 60


class StudySessionAckRequest(BaseModel):
    session_key: str
    trigger_type: str = "curve"


class StudySessionStateResponse(BaseModel):
    session_key: str
    course: str
    question_text: str
    topic_label: str
    knowledge_points: list[str]
    mini_quiz: list[str]
    memory_tips: list[str]
    review_mode: str
    strategy_name: str
    started_at: str
    last_activity_at: str
    focused_seconds: int
    wall_elapsed_minutes: int
    focused_minutes: int
    curve_due_count: int
    focus_due_count: int
    curve_ack_stage: int
    focus_ack_stage: int
    next_curve_due_at: str | None = None
    next_focus_due_at: str | None = None
    next_curve_prompt: str | None = None
    next_focus_prompt: str | None = None


class DueSessionItem(BaseModel):
    session_key: str
    course: str
    topic_label: str
    question_text: str
    review_mode: str
    strategy_name: str
    wall_elapsed_minutes: int
    focused_minutes: int
    curve_due_count: int
    focus_due_count: int
    next_curve_prompt: str | None = None
    next_focus_prompt: str | None = None
    mini_quiz: list[str]
    memory_tips: list[str]


class DueSessionListResponse(BaseModel):
    items: list[DueSessionItem]

