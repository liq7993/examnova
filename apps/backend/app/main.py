from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.agent import router as agent_router
from app.routes.health import router as health_router
from app.routes.history import router as history_router
from app.routes.ocr import router as ocr_router
from app.routes.settings import router as settings_router
from app.routes.study import router as study_router
from app.routes.study_notes import router as study_notes_router
from app.routes.study_state import router as study_state_router
from app.routes.thinking import router as thinking_router
from app.routes.wrongbook import router as wrongbook_router


def create_app() -> FastAPI:
    app = FastAPI(title="ExamNova API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["null"],
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$|^file://.*$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router)
    app.include_router(agent_router)
    app.include_router(settings_router)
    app.include_router(history_router)
    app.include_router(wrongbook_router)
    app.include_router(ocr_router)
    app.include_router(study_router)
    app.include_router(study_notes_router)
    app.include_router(study_state_router)
    app.include_router(thinking_router)
    return app


app = create_app()
