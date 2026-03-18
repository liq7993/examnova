from __future__ import annotations

import json
from pathlib import Path

from app.schemas.settings import SettingsTestRequest
from app.services.app_paths import ensure_data_dir, migrate_legacy_file

SETTINGS_FILE = migrate_legacy_file("settings.json")


def _normalize_settings_payload(payload: SettingsTestRequest) -> dict:
    existing = load_settings() or {}
    current = payload.model_dump()
    merged = existing | current

    if current.get("reuse_saved_credentials"):
        merged["api_key"] = current.get("api_key") or existing.get("api_key", "")
        merged["mathpix_app_key"] = current.get("mathpix_app_key") or existing.get("mathpix_app_key")
    else:
        merged["api_key"] = current.get("api_key", "")
        merged["mathpix_app_key"] = current.get("mathpix_app_key")

    return merged


def save_settings(payload: SettingsTestRequest) -> Path:
    ensure_data_dir()
    normalized = _normalize_settings_payload(payload)
    SETTINGS_FILE.write_text(
        json.dumps(normalized, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return SETTINGS_FILE


def load_settings() -> dict | None:
    if not SETTINGS_FILE.exists():
        return None
    try:
        return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None


def build_runtime_settings(payload: SettingsTestRequest) -> dict:
    return _normalize_settings_payload(payload)


def load_public_settings() -> dict:
    settings = load_settings() or {}
    return {
        "provider": settings.get("provider"),
        "base_url": settings.get("base_url"),
        "model": settings.get("model"),
        "demo_mode": settings.get("demo_mode", True),
        "mathpix_enabled": settings.get("mathpix_enabled", False),
        "mathpix_app_id": settings.get("mathpix_app_id"),
        "mathpix_endpoint": settings.get("mathpix_endpoint") or "https://api.mathpix.com/v3/text",
        "has_api_key": bool(settings.get("api_key")),
        "has_mathpix_app_key": bool(settings.get("mathpix_app_key")),
    }


def get_status() -> dict:
    settings = load_settings() or {}
    provider = settings.get("provider")
    base_url = settings.get("base_url")
    model = settings.get("model")
    api_key = settings.get("api_key")
    demo_mode = settings.get("demo_mode", True)

    missing: list[str] = []
    if not demo_mode:
        if not provider:
            missing.append("provider")
        if not base_url:
            missing.append("base_url")
        if not model:
            missing.append("model")
        if not api_key:
            missing.append("api_key")

    return {
        "ready": len(missing) == 0,
        "missing": missing,
        "provider": provider,
        "base_url": base_url,
        "model": model,
        "demo_mode": demo_mode,
        "has_api_key": bool(api_key),
        "has_mathpix_app_key": bool(settings.get("mathpix_app_key")),
    }
