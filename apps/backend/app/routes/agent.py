from fastapi import APIRouter

from app.agent.router import run_agent
from app.schemas.agent import AgentRunRequest, AgentRunResponse

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/run", response_model=AgentRunResponse)
def run_agent_route(request: AgentRunRequest) -> AgentRunResponse:
    return run_agent(request)
