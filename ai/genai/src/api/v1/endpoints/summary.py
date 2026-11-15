"""Endpoint untuk layanan Daily Stock Summary."""

from fastapi import APIRouter, Depends, HTTPException, status

from ....schemas.summary import (
    DailyStockSummaryRequest,
    DailyStockSummaryResponse,
)
from ....services.summary_service import DailySummaryService

router = APIRouter(prefix="/summary", tags=["Summary"])


def get_summary_service() -> DailySummaryService:
    """Dependency provider untuk DailySummaryService."""
    return DailySummaryService()


@router.post(
    "/daily",
    response_model=DailyStockSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Menghasilkan ringkasan stok harian UMKM",
    description=(
        "Menerima data stok sintetis harian melalui request JSON, mengklasifikasikan "
        "status barang (CRITICAL, WARNING, SAFE) sesuai aturan konsisten, dan "
        "menghasilkan narasi ringkasan stok dalam bahasa Indonesia berbasis Mock Service."
    ),
)
async def generate_daily_stock_summary(
    request: DailyStockSummaryRequest,
    service: DailySummaryService = Depends(get_summary_service),
) -> DailyStockSummaryResponse:
    """Endpoint untuk menghasilkan ringkasan stok harian."""
    try:
        return service.generate_summary(request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validasi data gagal: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan internal saat memproses ringkasan: {str(e)}",
        )

