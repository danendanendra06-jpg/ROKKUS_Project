"""Skema data DTO untuk fitur Daily Stock Summary."""

from datetime import date as date_type, datetime, timezone
import math
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator

from ..core.rules import StockStatus, STOCK_STATUS_DESCRIPTIONS


class DailyStockItemInput(BaseModel):
    """Input data barang stok harian yang dikirim ke endpoint summary."""
    name: str = Field(..., description="Nama barang inventaris (tidak boleh kosong)")
    current_stock: float = Field(..., ge=0, allow_inf_nan=False, description="Jumlah stok saat ini (angka finite non-negatif)")
    minimum_stock: float = Field(..., ge=0, allow_inf_nan=False, description="Batas stok minimum (angka finite non-negatif)")
    unit: str = Field(..., description="Satuan unit barang, misal kg, porsi, pcs")
    category: Optional[str] = Field(default="umum", description="Kategori barang opsional")
    id: Optional[str] = Field(default=None, description="Kode unik item jika ada")

    @field_validator("name", "unit", mode="before")
    @classmethod
    def validate_non_empty_strings(cls, v: str, info) -> str:
        """Memastikan field teks wajib tidak kosong atau hanya terdiri dari spasi."""
        if not isinstance(v, str) or not v.strip():
            field_name = info.field_name
            raise ValueError(f"Field '{field_name}' wajib diisi dan tidak boleh hanya berisi spasi.")
        return v.strip()

    @field_validator("current_stock", "minimum_stock")
    @classmethod
    def validate_finite_numbers(cls, v: float, info) -> float:
        """Memastikan nilai stok merupakan angka berhingga (finite) dan bukan NaN / Infinity."""
        if math.isnan(v) or math.isinf(v):
            field_name = info.field_name
            raise ValueError(f"Nilai '{field_name}' harus berupa angka berhingga (finite), tidak boleh NaN atau Infinity.")
        if v < 0:
            field_name = info.field_name
            raise ValueError(f"Nilai '{field_name}' tidak boleh bernilai negatif.")
        return float(v)


class DailyStockSummaryRequest(BaseModel):
    """Payload permintaan pembuatan ringkasan stok harian."""
    date: date_type = Field(..., description="Tanggal data stok kalender valid (format YYYY-MM-DD)")
    store_name: Optional[str] = Field(default="UMKM ROKKUS Mardani Raya", description="Nama gerai/unit usaha ROKKUS")
    items: List[DailyStockItemInput] = Field(..., min_length=1, description="Daftar item stok harian (minimal 1 barang)")

    @field_validator("store_name", mode="before")
    @classmethod
    def validate_store_name(cls, v: Optional[str]) -> str:
        if v is not None and isinstance(v, str):
            stripped = v.strip()
            if not stripped:
                return "UMKM ROKKUS Mardani Raya"
            return stripped
        return "UMKM ROKKUS Mardani Raya"


class ProcessedStockItem(BaseModel):
    """Item barang yang telah dievaluasi status ketersediaannya."""
    id: Optional[str] = None
    name: str
    category: Optional[str] = None
    current_stock: float
    minimum_stock: float
    unit: str
    status: StockStatus
    status_description: str


class StockStatusCounts(BaseModel):
    """Agregasi kuantitas barang berdasarkan status stok."""
    critical: int = Field(default=0, ge=0, description="Jumlah item berstatus CRITICAL")
    warning: int = Field(default=0, ge=0, description="Jumlah item berstatus WARNING")
    safe: int = Field(default=0, ge=0, description="Jumlah item berstatus SAFE")
    total_items: int = Field(default=0, ge=0, description="Total keseluruhan barang yang diproses")


class DailySummaryMeta(BaseModel):
    """Metadata eksekusi dan penanda sumber data ringkasan."""
    provider: str = Field(default="mock", description="Identitas penyedia ringkasan ('mock' untuk tahap ini)")
    is_synthetic: bool = Field(default=True, description="Penanda apakah data berasal dari sumber sintetis/ilustratif")
    source: str = Field(default="synthetic_input", description="Sumber masukan data (dapat disesuaikan pada integrasi database)")
    disclaimer: str = Field(
        default="PERINGATAN: Ringkasan ini dihasilkan oleh Mock Service menggunakan data sintetis/ilustratif untuk prototipe ROKKUS, bukan data operasional nyata UMKM.",
        description="Pernyataan resmi sifat data ilustratif"
    )
    generated_at: str = Field(..., description="Timestamp ISO-8601 pembuatan ringkasan")


class DailySummaryData(BaseModel):
    """Data hasil olahan ringkasan stok harian."""
    date: str = Field(..., description="Tanggal ringkasan stok dalam format ISO (YYYY-MM-DD)")
    store_name: str
    summary: str = Field(..., description="Narasi ringkasan stok harian dalam bahasa Indonesia")
    status_counts: StockStatusCounts
    items: List[ProcessedStockItem]
    suggested_actions: List[str]
    meta: DailySummaryMeta


class DailyStockSummaryResponse(BaseModel):
    """Kontrak respons standar API untuk Daily Stock Summary."""
    status: Literal["success", "error"] = "success"
    data: DailySummaryData
