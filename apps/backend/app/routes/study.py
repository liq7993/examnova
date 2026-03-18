from fastapi import APIRouter

from app.schemas.study import StudyAnalyzeRequest, StudyAnalyzeResponse
from app.skills.learning import run_learning_skill

router = APIRouter(prefix="/api/study", tags=["study"])


@router.post("/analyze", response_model=StudyAnalyzeResponse)
def analyze_study(request: StudyAnalyzeRequest) -> StudyAnalyzeResponse:
    return run_learning_skill(request)
