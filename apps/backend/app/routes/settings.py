from fastapi import APIRouter

from app.schemas.settings import (
    SettingsLoadResponse,
    SettingsStatusResponse,
    SettingsTestRequest,
    SettingsTestResponse,
)
from app.services.llm_client import test_connection
from app.services.settings_store import (
    build_runtime_settings,
    get_status,
    load_public_settings,
    save_settings as persist_settings,
)

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.post("/test", response_model=SettingsTestResponse)
def test_settings(request: SettingsTestRequest) -> SettingsTestResponse:
    settings = build_runtime_settings(request)
    ok, message = test_connection(settings)
    return SettingsTestResponse(ok=ok, message=message)


@router.post("/save", response_model=SettingsTestResponse)
def save_settings(request: SettingsTestRequest) -> SettingsTestResponse:
    settings_path = persist_settings(request)
    mode_note = "demo" if request.demo_mode else "live"
    message = (
        "后端已接收设置。"
        f"Model={request.model}, base_url={request.base_url}, mode={mode_note}, saved_to={settings_path}"
    )
    return SettingsTestResponse(ok=True, message=message)


@router.get("/load", response_model=SettingsLoadResponse)
def load_saved_settings() -> SettingsLoadResponse:
    return SettingsLoadResponse(**load_public_settings())


@router.get("/status", response_model=SettingsStatusResponse)
def settings_status() -> SettingsStatusResponse:
    status = get_status()
    return SettingsStatusResponse(**status)
