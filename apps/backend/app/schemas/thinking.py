from pydantic import BaseModel


class ThinkingExpandRequest(BaseModel):
    idea: str
    mode: str = "essay"
    rewrite_style: str | None = None


class ThinkingExpandResponse(BaseModel):
    mode: str
    title: str
    outline: list[str]
    content: str
    rewrite_options: list[str]
    key_points: list[str]
    tone_tags: list[str]
    export_title: str
    summary: str
    confidence_note: str
    reflection_prompt: str
    review_bridge: list[str]
    action_list: list[str]
