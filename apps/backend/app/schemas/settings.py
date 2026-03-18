from pydantic import BaseModel, Field


class SettingsTestRequest(BaseModel):
    provider: str = Field(default="minimax")
    base_url: str
    model: str
    api_key: str = Field(default="")
    demo_mode: bool = Field(default=True)
    reuse_saved_credentials: bool = Field(default=False)
    mathpix_enabled: bool = Field(default=False)
    mathpix_app_id: str | None = None
    mathpix_app_key: str | None = None
    mathpix_endpoint: str = Field(default="https://api.mathpix.com/v3/text")


class SettingsTestResponse(BaseModel):
    ok: bool
    message: str


class SettingsStatusResponse(BaseModel):
    ready: bool
    missing: list[str]
    provider: str | None
    base_url: str | None
    model: str | None
    demo_mode: bool
    has_api_key: bool
    has_mathpix_app_key: bool


class SettingsLoadResponse(BaseModel):
    provider: str | None
    base_url: str | None
    model: str | None
    demo_mode: bool
    mathpix_enabled: bool
    mathpix_app_id: str | None
    mathpix_endpoint: str
    has_api_key: bool
    has_mathpix_app_key: bool
