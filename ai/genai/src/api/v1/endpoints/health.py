"""Endpoint untuk health check dan readiness probe."""

from fastapi import APIRouter
from pydantic import BaseModel

from ....core.config import settings, resolve_inventory_path
from ....repositories.mock_inventory import MockInventoryRepository

router = APIRouter()


class HealthResponse(BaseModel):
    """Skema respon status kesehatan layanan."""
    status: str
    service: str
    version: str
    environment: str
    active_provider: str
    data_source: str
    inventory_items_loaded: int
    gemini_configured: bool


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check dan verifikasi konfigurasi AI Assistant",
)
async def check_health() -> HealthResponse:
    """Memeriksa kesiapan layanan, membaca status file dataset dan provider aktif."""
    inv_path = resolve_inventory_path()
    file_exists = inv_path.exists()
    items_count = 0

    if file_exists:
        try:
            repo = MockInventoryRepository(inv_path)
            items_count = len(repo.get_all_items())
        except Exception:
            items_count = 0

    return HealthResponse(
        status="healthy" if file_exists else "degraded",
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        active_provider="mock",
        data_source=str(inv_path) if file_exists else "not_found",
        inventory_items_loaded=items_count,
        gemini_configured=bool(settings.GEMINI_API_KEY),
    )

