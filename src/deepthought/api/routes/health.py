"""Health check endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter

from deepthought import __version__
from deepthought.models import HealthResponse

router = APIRouter()


@router.get(
    "",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns the health status of the service.",
)
async def health_check() -> HealthResponse:
    """Check service health."""
    return HealthResponse(
        status="healthy",
        version=__version__,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
