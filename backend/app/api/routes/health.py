from fastapi import APIRouter, status
from app.schemas.health import HealthResponse
from app.services.health import HealthService

router = APIRouter()

@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="System Health Check",
    description="Probes API readiness, PostgreSQL database connection, and Redis key-value store."
)
async def get_health() -> HealthResponse:
    """
    Returns system status and verifies infrastructure connectivity.
    """
    return await HealthService.check_health()
