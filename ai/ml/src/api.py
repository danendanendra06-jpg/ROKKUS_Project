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
    """Body request untuk POST /ml/predict-status (Model ML legacy)."""
    items: List[StokItemInput] = Field(
        ...,
        min_length=1,
        description="Daftar item stok yang ingin diprediksi (minimal 1)."
    )


class PrediksiItem(BaseModel):
    """Hasil prediksi untuk satu item (Model ML legacy)."""
    status:       str              = Field(..., description="'aman' | 'menipis' | 'habis'")
    probabilitas: Dict[str, float] = Field(..., description="Probabilitas per kelas")
    versi_model:  str              = Field(..., description="Versi model yang digunakan")


class PredictResponse(BaseModel):
    """Response POST /ml/predict-status (Model ML legacy)."""
    total_items: int                = Field(..., description="Jumlah item yang diprediksi")
    prediksi:    List[PrediksiItem] = Field(..., description="Hasil prediksi per item")


# --- Schema untuk Rule-Based Stock Status Classification ---

class StockStatusItemInput(BaseModel):
    """Schema input minimal untuk klasifikasi status stok aktual per barang."""
    stok_saat_ini: float = Field(..., ge=0, description="Stok fisik saat ini (unit), ≥ 0")
    batas_minimum: float = Field(..., ge=0, description="Batas stok minimum SKU, ≥ 0")
    days_of_cover: Optional[float] = Field(None, ge=0, description="Estimasi sisa hari stok (opsional), ≥ 0")
    id_barang:     Optional[str]   = Field(None, description="ID produk/SKU (opsional)")
    nama_barang:   Optional[str]   = Field(None, description="Nama produk/SKU (opsional)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "stok_saat_ini": 4.0,
                "batas_minimum": 5.0,
                "days_of_cover": 0.8,
                "id_barang":     "PR001",
                "nama_barang":   "Lotus Biscoff"
            }
        }
    }


class StockStatusRequest(BaseModel):
    """Body request untuk POST /ml/status (Rule-Based)."""
    items: List[StockStatusItemInput] = Field(
        ...,
        min_length=1,
        description="Daftar item stok yang ingin dicek statusnya (minimal 1)."
    )


class StockStatusResultItem(BaseModel):
    """Hasil klasifikasi status stok aktual untuk satu item."""
    id_barang:   Optional[str] = Field(None, description="ID produk (jika diberikan)")
    nama_barang: Optional[str] = Field(None, description="Nama produk (jika diberikan)")
    status:      str           = Field(..., description="'aman' | 'menipis' | 'habis'")
    is_menipis:  bool          = Field(..., description="True jika stok menipis")
    is_habis:    bool          = Field(..., description="True jika stok habis (0)")
    alasan:      str           = Field(..., description="Penjelasan teknis status")
    saran:       str           = Field(..., description="Rekomendasi tindakan operasional")
    metode:      str           = Field("rule_based", description="Metode evaluasi ('rule_based')")


class StockStatusResponse(BaseModel):
    """Response POST /ml/status (Rule-Based)."""
    total_items: int                        = Field(..., description="Jumlah item yang dievaluasi")
    hasil:       List[StockStatusResultItem] = Field(..., description="Daftar hasil evaluasi status stok")



class HealthResponse(BaseModel):
    """Response GET /ml/health."""
    status:      str   = Field(..., description='"ok" atau "degraded"')
    model_ready: bool  = Field(..., description='True jika model terdapat dan bisa dimuat')
    versi_model: Optional[str] = Field(None, description='Versi model (jika tersedia)')
    keterangan:  str   = Field(..., description='Pesan singkat')

# ---------------------------------------------------------------------------
# Forecasting schemas (new)
# ---------------------------------------------------------------------------

class ForecastItemInput(BaseModel):
    """Input schema for a single SKU to be forecasted."""
    id_barang:      str   = Field(..., description='SKU identifier')
    nama_barang:    Optional[str] = Field(None, description='Nama produk (opsional)')
    batas_minimum:  float = Field(..., ge=0, description='Batas minimum stok')
    # Required numeric & categorical features (same as classification but without leaking ones)
    stok_saat_ini:  float = Field(..., ge=0, description='Stok akhir saat ini')
    barang_masuk:   float = Field(..., ge=0, description='Jumlah barang masuk')
    barang_keluar:  float = Field(..., ge=0, description='Jumlah barang keluar')
    avg_keluar_7h:  float = Field(..., ge=0, description='Rata-rata keluar 7 hari terakhir')
    total_masuk_7h: float = Field(..., ge=0, description='Total masuk 7 hari terakhir')
    total_keluar_7h:float = Field(..., ge=0, description='Total keluar 7 hari terakhir')
    kategori:       str   = Field(..., min_length=1, description='Kategori produk')
    rasa:           str   = Field(..., min_length=1, description='Varian rasa')

class ForecastRequest(BaseModel):
    """Batch request for stock forecasting."""
    items: List[ForecastItemInput] = Field(..., min_length=1, description='Daftar SKU untuk diprediksi')
    horizon_days: int = Field(7, ge=1, le=30, description='Horizon prediksi (hari)')

class ForecastResultItem(BaseModel):
    id_barang:        str   = Field(..., description='SKU identifier')
    nama_barang:      Optional[str] = Field(None, description='Nama produk')
    horizon_days:     int   = Field(..., description='Horizon yang diprediksi (hari)')
    predicted_stock:  float = Field(..., description='Jumlah stok yang diprediksi')
    predicted_status: str   = Field(..., description='"aman" | "menipis" | "habis"')
    batas_minimum:    float = Field(..., description='Batas minimum stok')
    model_version:    str   = Field(..., description='Versi model forecasting')
    notes:            Optional[str] = Field(None, description='Catatan (mis. data tidak cukup)')

class ForecastResponse(BaseModel):
    total_items: int = Field(..., description='Jumlah item yang diprediksi')
    results: List[ForecastResultItem] = Field(..., description='Daftar hasil prediksi')
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


@router.post(
    "/status",
    response_model=StockStatusResponse,
    summary="Klasifikasi Status Stok Aktual (Rule-Based)",
    description=(
        "Klasifikasi status stok aktual per barang ('aman', 'menipis', 'habis') "
        "berdasarkan aturan bisnis deterministik tanpa memerlukan model Machine Learning (.joblib). "
        "Input minimal hanya memerlukan 'stok_saat_ini' dan 'batas_minimum'."
    ),
    responses={
        200: {"description": "Evaluasi status stok berhasil"},
        400: {"description": "Input tidak valid (stok negatif, dll.)"},
        422: {"description": "Validasi Pydantic gagal (tipe data salah/field hilang)"},
    },
)
async def stock_status_endpoint(request: StockStatusRequest) -> StockStatusResponse:
    try:
        from predict import classify_stock_status, PredictInputError
    except ImportError:
        from src.predict import classify_stock_status, PredictInputError

    hasil_items: List[StockStatusResultItem] = []

    for item in request.items:
        try:
            res = classify_stock_status(
                stok_saat_ini=item.stok_saat_ini,
                batas_minimum=item.batas_minimum,
                days_of_cover=item.days_of_cover,
                config_path=_CONFIG_PATH,
            )
            hasil_items.append(
                StockStatusResultItem(
                    id_barang=item.id_barang,
                    nama_barang=item.nama_barang,
                    status=res["status"],
                    is_menipis=res["is_menipis"],
                    is_habis=res["is_habis"],
                    alasan=res["alasan"],
                    saran=res["saran"],
                    metode=res["metode"],
                )
            )
        except PredictInputError as e:
            raise HTTPException(
                status_code=400,
                detail={"error": "invalid_input", "pesan": str(e)},
            )
        except Exception as e:
            logger.exception("Unexpected error saat classify_stock_status")
            raise HTTPException(
                status_code=500,
                detail={"error": "internal_error", "pesan": str(e)},
            )

    return StockStatusResponse(
        total_items=len(hasil_items),
        hasil=hasil_items,
    )



# ---------------------------------------------------------------------------
# Forecasting endpoint (new)
# ---------------------------------------------------------------------------

@router.post(
    "/forecast-stock",
    response_model=ForecastResponse,
    summary="Forecast Stock Levels",
    description=(
        "Prediksi jumlah stok di masa mendatang untuk satu atau beberapa SKU. "
        "Horizon dapat diatur hingga 30 hari, namun saat ini hanya horizon_days=7 didukung. "
        "Fitur yang digunakan tidak mengandung kebocoran data – semua dihitung hanya dari data historis yang tersedia."
    ),
    responses={
        200: {"description": "Forecast berhasil"},
        400: {"description": "Input tidak valid atau horizon tidak didukung"},
        503: {"description": "Model forecasting belum tersedia"},
        500: {"description": "Kesalahan internal server"},
    },
)
async def forecast_stock_endpoint(request: ForecastRequest) -> ForecastResponse:
    # Validate horizon (currently only 7‑day horizon is trained)
    if request.horizon_days != 7:
        raise HTTPException(
            status_code=400,
            detail={"error": "unsupported_horizon", "pesan": "Only horizon_days=7 is supported"},
        )

    # Load config
    import yaml
    from src import forecast as forecast_mod
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "config_error", "pesan": str(e)})

    # Load or train forecasting model
    try:
        model = forecast_mod.load_forecast_model()
    except Exception as e:
        raise HTTPException(status_code=503, detail={"error": "model_not_found", "pesan": str(e)})

    results: List[ForecastResultItem] = []
    for item in request.items:
        try:
            pred = forecast_mod.predict_future_stock(
                item=item.model_dump(),
                horizon=request.horizon_days,
                model=model,
                cfg=cfg,
            )
        except Exception as e:
            # Insufficient history or other error – return a note but keep processing
            results.append(ForecastResultItem(
                id_barang=item.id_barang,
                nama_barang=item.nama_barang,
                horizon_days=request.horizon_days,
                predicted_stock=0.0,
                predicted_status="menipis",
                batas_minimum=item.batas_minimum,
                model_version="na",
                notes=str(e),
            ))
            continue
        results.append(ForecastResultItem(
            id_barang=item.id_barang,
            nama_barang=item.nama_barang,
            horizon_days=request.horizon_days,
            predicted_stock=pred["predicted_stock"],
            predicted_status=pred["predicted_status"],
            batas_minimum=item.batas_minimum,
            model_version="forecast_v1",
            notes=None,
        ))
    return ForecastResponse(
        total_items=len(results),
        results=results,
        status="ok",
        model_ready=True,
        versi_model="forecast_v1",
        keterangan="Forecast berhasil"
    )

# ---------------------------------------------------------------------------

@router.post(
    "/forecast-stock",
    response_model=ForecastResponse,
    summary="Forecast Stock Levels",
    description=(
        "Prediksi jumlah stok di masa mendatang untuk satu atau beberapa SKU. "
        "Horizon dapat diatur hingga 30 hari. "
        "Fitur yang digunakan tidak mengandung kebocoran data – semua dihitung hanya dari data historis yang tersedia."
    ),
    responses={
        200: {"description": "Forecast berhasil"},
        400: {"description": "Input tidak valid atau data historis tidak cukup"},
        503: {"description": "Model forecasting belum tersedia"},
        500: {"description": "Kesalahan internal server"},
    },
)
async def forecast_stock_endpoint(request: ForecastRequest) -> ForecastResponse:
    # Load config
    import yaml
    from src import forecast as forecast_mod
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "config_error", "pesan": str(e)})

    # Load or train forecasting model
    try:
        model = forecast_mod.load_forecast_model()
    except Exception as e:
        raise HTTPException(status_code=503, detail={"error": "model_not_found", "pesan": str(e)})

    results: List[ForecastResultItem] = []
    for item in request.items:
        try:
            pred = forecast_mod.predict_future_stock(
                item=item.model_dump(),
                horizon=request.horizon_days,
                model=model,
                cfg=cfg,
            )
        except Exception as e:
            # If we cannot compute because of insufficient history, return note but continue
            results.append(ForecastResultItem(
                id_barang=item.id_barang,
                nama_barang=item.nama_barang,
                horizon_days=request.horizon_days,
                predicted_stock=0.0,
                predicted_status="menipis",
                batas_minimum=item.batas_minimum,
                model_version="na",
                notes=str(e),
            ))
            continue
        results.append(ForecastResultItem(
            id_barang=item.id_barang,
            nama_barang=item.nama_barang,
            horizon_days=request.horizon_days,
            predicted_stock=pred["predicted_stock"],
            predicted_status=pred["predicted_status"],
            batas_minimum=item.batas_minimum,
            model_version="forecast_v1",
            notes=None,
        ))
    # Enforce supported horizons (only 7 days for now)
    if request.horizon_days != 7:
        raise HTTPException(
            status_code=400,
            detail={"error": "unsupported_horizon", "pesan": "Only horizon_days=7 is supported"},
        )
    return ForecastResponse(
        total_items=len(results),
        results=results,
        status="ok",
        model_ready=True,
        versi_model="forecast_v1",
        keterangan="Forecast berhasil"
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
