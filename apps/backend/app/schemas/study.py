from pydantic import BaseModel


class StudyAnalyzeRequest(BaseModel):
    input_text: str
    explanation_mode: str = "concise"
    course: str = "advanced mathematics"
    detail_level: str = "full"


class StudyAnalyzeResponse(BaseModel):
    knowledge_points: list[str]
    difficulty: str
    explanation_mode: str
    explanation: str
    solution_steps: list[str]
    formula_notes: list[str]
    novice_explain: str
    review_schedule: list[str]
    time_plan: list[str]
    memory_tips: list[str]
    exam_tricks: list[str]
    diagram_hint: str
    variant_questions: list[str]
    mini_quiz: list[str]
    self_questions: list[str]
    practice_set: list[str]
    examples: list[str]
    exam_focus_prediction: list[str]
    next_action: str
    confidence_note: str
    risk_notice: str
    score_breakdown: list[str]
