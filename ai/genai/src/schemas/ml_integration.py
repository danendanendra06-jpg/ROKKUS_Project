"""Skema DTO untuk integrasi Machine Learning (ML) ROKKUS (Tahap 6B).

Mengacu pada kontrak aktual endpoint POST /ml/predict-status milik tim ML Husain
di branch origin/feat/ml-mock (ai/ml/src/api.py).

PENTING - PEMISAHAN SEMANTIK:
- Status Stok Aktual (Data Science / GenAI): EMPTY, LOW, SAFE.
  Berbasis fakta inventaris akhir hari ini (current_stock = 0 → EMPTY, 1..5 → LOW, >5 → SAFE).
- Status Prediksi Risiko Stok (Machine Learning): habis, menipis, aman.
  Berbasis hasil inferensi model prediktif (forecasting / risk classification) dengan 11 fitur.
- Kedua domain ini TIDAK boleh dicampuradukkan agar tidak menimbulkan konflik semantik.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class MLItemFeatureInput(BaseModel):
    """Schema 11 fitur input per item sesuai Pydantic StokItemInput tim ML Husain."""

    stok_saat_ini: float = Field(..., ge=0, description="Stok akhir hari ini (unit), >= 0")
    batas_minimum: float = Field(..., ge=0, description="Batas stok minimum SKU, >= 0")
    barang_masuk: float = Field(..., ge=0, description="Unit masuk (produksi/resupply), >= 0")
    barang_keluar: float = Field(..., ge=0, description="Unit terjual/keluar, >= 0")
    avg_keluar_7h: float = Field(..., ge=0, description="Rata-rata keluar 7 hari terakhir, >= 0")
    days_of_cover: float = Field(..., ge=0, description="Stok cukup untuk berapa hari, >= 0")
    rasio_stok: float = Field(..., ge=0, description="stok_saat_ini / batas_minimum, >= 0")
    total_masuk_7h: float = Field(..., ge=0, description="Total masuk 7 hari terakhir, >= 0")
    total_keluar_7h: float = Field(..., ge=0, description="Total keluar 7 hari terakhir, >= 0")
    kategori: str = Field(..., min_length=1, description="Kategori: 'roti_kukus' atau 'roti_bakar'")
    rasa: str = Field(..., min_length=1, description="Varian rasa (mis. 'coklat', 'keju')")

    @field_validator("kategori", "rasa")
    @classmethod
    def tidak_boleh_kosong(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Nilai tidak boleh berupa string kosong atau spasi saja.")
        return v.strip()


class MLPredictRequest(BaseModel):
    """Body request untuk POST /ml/predict-status."""
    items: List[MLItemFeatureInput] = Field(
        ...,
        min_length=1,
        description="Daftar item stok yang ingin diprediksi (minimal 1)."
    )


class MLPrediksiItem(BaseModel):
    """Hasil prediksi risiko untuk satu item dari ML."""
    status: str = Field(..., description="'aman' | 'menipis' | 'habis'")
    probabilitas: Dict[str, float] = Field(..., description="Probabilitas per kelas")
    versi_model: str = Field(..., description="Versi model ML yang digunakan")


class MLPredictResponse(BaseModel):
    """Response dari POST /ml/predict-status."""
    total_items: int = Field(..., description="Jumlah item yang diprediksi")
    prediksi: List[MLPrediksiItem] = Field(..., description="Hasil prediksi per item")


class MLItemRiskEnrichment(BaseModel):
    """Hasil pengayaan risiko ML yang dipetakan kembali ke item GenAI."""
    item_name: str
    ml_predicted_risk: str = Field(..., description="Prediksi risiko dari ML ('aman', 'menipis', 'habis')")
    probabilities: Dict[str, float] = Field(default_factory=dict)
    model_version: str = Field(default="unknown")
    source: str = Field(default="ml_predict_status", description="Penanda asal prediksi")


# ===========================================================================
# Schemas untuk Endpoint Forecasting ML (POST /ml/forecast-stock) - Tahap 7B
# ===========================================================================

class MLForecastItemInput(BaseModel):
    """Schema input untuk peramalan stok satu SKU (POST /ml/forecast-stock).

    Mengacu langsung ke ForecastItemInput pada ai/ml/src/api.py.
    """
    id_barang: str = Field(..., description="SKU identifier")
    nama_barang: Optional[str] = Field(None, description="Nama produk (opsional)")
    batas_minimum: float = Field(..., ge=0, description="Batas minimum stok")
    stok_saat_ini: float = Field(..., ge=0, description="Stok akhir saat ini")
    barang_masuk: float = Field(..., ge=0, description="Jumlah barang masuk")
    barang_keluar: float = Field(..., ge=0, description="Jumlah barang keluar")
    avg_keluar_7h: float = Field(..., ge=0, description="Rata-rata keluar 7 hari terakhir")
    total_masuk_7h: float = Field(..., ge=0, description="Total masuk 7 hari terakhir")
    total_keluar_7h: float = Field(..., ge=0, description="Total keluar 7 hari terakhir")
    kategori: str = Field(..., min_length=1, description="Kategori produk")
    rasa: str = Field(..., min_length=1, description="Varian rasa")

    @field_validator("id_barang", "kategori", "rasa")
    @classmethod
    def tidak_boleh_kosong(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Nilai tidak boleh berupa string kosong atau spasi saja.")
        return v.strip()


class MLForecastRequest(BaseModel):
    """Batch request untuk peramalan stok (POST /ml/forecast-stock).

    Catatan Kontrak ML Husain:
    Meskipun skema Pydantic ML mendefinisikan ge=1, le=30, implementasi endpoint
    aktual di ai/ml/src/api.py secara ketat mewajibkan horizon_days == 7
    (HTTP 400: 'Only horizon_days=7 is supported').
    """
    items: List[MLForecastItemInput] = Field(
        ...,
        min_length=1,
        description="Daftar SKU untuk diprediksi"
    )
    horizon_days: int = Field(
        7,
        description="Horizon prediksi dalam hari (hanya horizon 7 hari yang didukung oleh model ML Husain)"
    )

    @field_validator("horizon_days")
    @classmethod
    def validate_horizon_supported(cls, v: int) -> int:
        if v != 7:
            raise ValueError(
                f"Horizon {v} hari tidak didukung. Model ML Husain saat ini hanya mendukung horizon_days=7."
            )
        return v


class MLForecastResultItem(BaseModel):
    """Hasil prediksi stok untuk satu SKU dari model forecasting."""
    id_barang: str = Field(..., description="SKU identifier")
    nama_barang: Optional[str] = Field(None, description="Nama produk")
    horizon_days: int = Field(..., description="Horizon yang diprediksi (hari)")
    predicted_stock: float = Field(..., description="Jumlah stok yang diprediksi")
    predicted_status: str = Field(..., description="'aman' | 'menipis' | 'habis'")
    batas_minimum: float = Field(..., description="Batas minimum stok")
    model_version: str = Field(..., description="Versi model forecasting")
    notes: Optional[str] = Field(None, description="Catatan teknis (mis. data tidak cukup)")


class MLForecastResponse(BaseModel):
    """Response dari POST /ml/forecast-stock."""
    total_items: int = Field(..., description="Jumlah item yang diprediksi")
    results: List[MLForecastResultItem] = Field(..., description="Daftar hasil prediksi")
    status: Optional[str] = Field(None, description="Status eksekusi API ML")
    model_ready: Optional[bool] = Field(None, description="Status kesiapan model")
    versi_model: Optional[str] = Field(None, description="Versi model")
    keterangan: Optional[str] = Field(None, description="Keterangan singkat respons")

