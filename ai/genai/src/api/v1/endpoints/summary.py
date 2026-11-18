"""Endpoint untuk layanan Daily Stock Summary."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status

from ....core.config import settings
from ....schemas.summary import (
    DailyStockSummaryRequest,
    DailyStockSummaryResponse,
)
from ....services.summary_service import DailySummaryService
from ....services.summary_llm import MockSummaryLLMService
from ....services.gemini_summary_llm import GeminiSummaryLLMService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/summary", tags=["Summary"])


def get_summary_service() -> DailySummaryService:
    """Dependency provider untuk DailySummaryService dengan Factory Pattern.

    Memilih antara GeminiSummaryLLMService atau MockSummaryLLMService
    berdasarkan konfigurasi environment (LLM_PROVIDER).
    """
    if str(settings.LLM_PROVIDER).lower() == "gemini" and settings.GEMINI_API_KEY:
        try:
            gemini_llm = GeminiSummaryLLMService(
                api_key=settings.GEMINI_API_KEY,
                model_name=settings.GEMINI_MODEL_NAME,
                timeout_seconds=getattr(settings, "GEMINI_TIMEOUT_SECONDS", 10.0),
            )
            return DailySummaryService(llm_service=gemini_llm)
        except Exception as e:
            logger.warning(
                f"Gagal menginisialisasi GeminiSummaryLLMService: {e}. Menggunakan MockSummaryLLMService."
            )

    return DailySummaryService(llm_service=MockSummaryLLMService())


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

