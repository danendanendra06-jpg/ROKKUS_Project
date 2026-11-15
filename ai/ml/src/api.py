"""
api.py – FastAPI Endpoint untuk Inferensi Model ROKKUS ML
==========================================================
Capstone Asah 2026 | Tim A26-CS159

Endpoint:
  POST /ml/predict-status    → Prediksi status stok (aman/menipis/habis)
  GET  /ml/health            → Health check

Skema input/output menggunakan Pydantic v2.

Penggunaan sebagai standalone:
  cd ai/ml
  uvicorn src.api:app --reload --port 8001

Penggunaan sebagai APIRouter (untuk integrasi backend FastAPI):
  from src.api import router as ml_router
  app.include_router(ml_router)

CATATAN INTEGRASI:
  - Lihat ai/ml/README.md § Catatan Integrasi untuk instruksi mendaftarkan
    router ini ke backend FastAPI tanpa mengubah file di backend/.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter
from pydantic import BaseModel, Field, field_validator, model_validator

logger = logging.getLogger(__name__)

# Lazy import predict untuk menghindari error saat model belum ada
_ML_DIR     = Path(__file__).parent.parent
_CONFIG_PATH = _ML_DIR / "configs" / "config.yaml"
_MODEL_PATH  = _ML_DIR / "models" / "best_model.joblib"
_META_PATH   = _ML_DIR / "models" / "metadata.json"


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------

class StokItemInput(BaseModel):
    """Schema input untuk satu item stok."""

    stok_saat_ini:   float = Field(..., ge=0, description="Stok akhir hari ini (unit), ≥ 0")
    batas_minimum:   float = Field(..., ge=0, description="Batas stok minimum SKU, ≥ 0")
    barang_masuk:    float = Field(..., ge=0, description="Unit masuk (produksi/resupply), ≥ 0")
    barang_keluar:   float = Field(..., ge=0, description="Unit terjual/keluar, ≥ 0")
    avg_keluar_7h:   float = Field(..., ge=0, description="Rata-rata keluar 7 hari terakhir, ≥ 0")
    days_of_cover:   float = Field(..., ge=0, description="Stok cukup untuk berapa hari, ≥ 0")
    rasio_stok:      float = Field(..., ge=0, description="stok_saat_ini / batas_minimum, ≥ 0")
    total_masuk_7h:  float = Field(..., ge=0, description="Total masuk 7 hari terakhir, ≥ 0")
    total_keluar_7h: float = Field(..., ge=0, description="Total keluar 7 hari terakhir, ≥ 0")
    kategori:        str   = Field(..., min_length=1, description="Kategori: 'roti_kukus' atau 'roti_bakar'")
    rasa:            str   = Field(..., min_length=1, description="Varian rasa (mis. 'coklat', 'keju')")

    @field_validator("kategori", "rasa")
    @classmethod
    def tidak_boleh_kosong(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Nilai tidak boleh berupa string kosong atau spasi saja.")
        return v.strip()

    model_config = {
        "json_schema_extra": {
            "example": {
                "stok_saat_ini":   5.0,
                "batas_minimum":  15.0,
                "barang_masuk":   20.0,
                "barang_keluar":  30.0,
                "avg_keluar_7h":  28.0,
                "days_of_cover":   0.18,
                "rasio_stok":      0.33,
                "total_masuk_7h": 140.0,
                "total_keluar_7h": 196.0,
                "kategori":        "roti_kukus",
                "rasa":            "coklat",
            }
        }
    }


class PredictRequest(BaseModel):
    """Body request untuk POST /ml/predict-status."""
    items: List[StokItemInput] = Field(
        ...,
        min_length=1,
        description="Daftar item stok yang ingin diprediksi (minimal 1)."
    )


class PrediksiItem(BaseModel):
    """Hasil prediksi untuk satu item."""
    status:       str              = Field(..., description="'aman' | 'menipis' | 'habis'")
    probabilitas: Dict[str, float] = Field(..., description="Probabilitas per kelas")
    versi_model:  str              = Field(..., description="Versi model yang digunakan")


class PredictResponse(BaseModel):
    """Response POST /ml/predict-status."""
    total_items: int                = Field(..., description="Jumlah item yang diprediksi")
    prediksi:    List[PrediksiItem] = Field(..., description="Hasil prediksi per item")


class HealthResponse(BaseModel):
    """Response GET /ml/health."""
    status:      str           = Field(..., description="'ok' atau 'degraded'")
    model_ready: bool          = Field(..., description="True jika model terdapat dan bisa dimuat")
    versi_model: Optional[str] = Field(None,  description="Versi model (jika tersedia)")
    keterangan:  str           = Field(..., description="Pesan singkat")


# ---------------------------------------------------------------------------
# Router (untuk integrasi sebagai sub-router)
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/ml", tags=["ROKKUS ML – Status Stok"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check – ROKKUS ML",
    description="Cek apakah service ML berjalan dan model tersedia.",
)
async def health_check() -> HealthResponse:
    model_ok = _MODEL_PATH.exists()
    versi = None

    if model_ok and _META_PATH.exists():
        try:
            import json
            with open(_META_PATH, "r") as f:
                meta = json.load(f)
            versi = meta.get("versi", "unknown")
        except Exception:
            pass

    return HealthResponse(
        status      = "ok" if model_ok else "degraded",
        model_ready = model_ok,
        versi_model = versi,
        keterangan  = (
            "Model siap digunakan." if model_ok
            else "Model belum tersedia. Jalankan: python src/train.py"
        ),
    )


@router.post(
    "/predict-status",
    response_model=PredictResponse,
    summary="Prediksi Status Stok",
    description=(
        "Prediksi status stok (aman / menipis / habis) untuk satu atau beberapa item. "
        "Semua fitur numerik wajib ≥ 0. Kolom kategorik tidak boleh kosong."
    ),
    responses={
        200: {"description": "Prediksi berhasil"},
        400: {"description": "Input tidak valid (stok negatif, dll.)"},
        422: {"description": "Validasi Pydantic gagal (kolom hilang/tipe salah)"},
        503: {"description": "Model belum tersedia"},
    },
)
async def predict_status_endpoint(request: PredictRequest) -> PredictResponse:
    # Cek model tersedia
    if not _MODEL_PATH.exists():
        raise HTTPException(
            status_code=503,
            detail={
                "error":    "model_not_found",
                "pesan":    "Model belum tersedia.",
                "solusi":   "Jalankan: python src/train.py",
            },
        )

    # Import predict (lazy, hindari circular import)
    try:
        from predict import predict_status, PredictInputError
    except ImportError:
        from src.predict import predict_status, PredictInputError

    # Konversi ke list dict
    input_list = [item.model_dump() for item in request.items]

    try:
        hasil_list = predict_status(
            input_data  = input_list,
            model_path  = _MODEL_PATH,
            config_path = _CONFIG_PATH,
            meta_path   = _META_PATH,
        )
    except PredictInputError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_input",
                "pesan": str(e),
            },
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=503,
            detail={"error": "model_not_found", "pesan": str(e)},
        )
    except Exception as e:
        logger.exception("Unexpected error saat predict_status")
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "pesan": str(e)},
        )

    prediksi = [
        PrediksiItem(
            status      = r["status"],
            probabilitas = r["probabilitas"],
            versi_model = r["versi_model"],
        )
        for r in hasil_list
    ]

    return PredictResponse(
        total_items = len(prediksi),
        prediksi    = prediksi,
    )


# ---------------------------------------------------------------------------
# Standalone app (jalankan langsung: uvicorn src.api:app)
# ---------------------------------------------------------------------------

app = FastAPI(
    title       = "ROKKUS ML – Stock Status Predictor",
    description = (
        "API inferensi model Machine Learning untuk klasifikasi status stok harian UMKM ROKKUS. "
        "Capstone Asah 2026 | Tim A26-CS159"
    ),
    version     = "1.0.0",
    docs_url    = "/ml/docs",
    redoc_url   = "/ml/redoc",
)

app.include_router(router)


@app.exception_handler(422)
async def validation_exception_handler(request: Request, exc) -> JSONResponse:
    """Override 422 untuk pesan error yang lebih deskriptif."""
    return JSONResponse(
        status_code=422,
        content={
            "error":  "validation_error",
            "pesan":  "Input tidak valid. Periksa tipe dan nilai semua kolom.",
            "detail": exc.errors() if hasattr(exc, "errors") else str(exc),
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8001, reload=True, app_dir=str(Path(__file__).parent))
