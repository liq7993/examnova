from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

APP_NAME = "ExamNova"
LEGACY_REPO_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
REPO_ROOT = Path(__file__).resolve().parents[4]
REPO_DATA_DIR = REPO_ROOT / ".examnova-data"


def _packaged_base_dir() -> Path | None:
    if not getattr(sys, "frozen", False):
        return None
    return Path(sys.executable).resolve().parent


def get_user_data_dir() -> Path:
    env_dir = os.environ.get("EXAMNOVA_DATA_DIR")
    if env_dir:
        return Path(env_dir).expanduser().resolve()

    packaged_base_dir = _packaged_base_dir()
    if packaged_base_dir is not None:
        return packaged_base_dir / "data"

    if REPO_ROOT.exists():
        return REPO_DATA_DIR

    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / APP_NAME

    if os.name == "nt":
        return Path.home() / "AppData" / "Local" / APP_NAME

    xdg_data_home = os.environ.get("XDG_DATA_HOME")
    if xdg_data_home:
        return Path(xdg_data_home) / APP_NAME

    return Path.home() / ".local" / "share" / APP_NAME


DATA_DIR = get_user_data_dir()


def ensure_data_dir() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR


def migrate_legacy_file(filename: str) -> Path:
    ensure_data_dir()
    target = DATA_DIR / filename
    legacy = LEGACY_REPO_DATA_DIR / filename
    if not target.exists() and legacy.exists():
        shutil.copy2(legacy, target)
    return target
