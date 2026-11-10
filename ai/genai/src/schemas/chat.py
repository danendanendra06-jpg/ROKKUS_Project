"""Skema data untuk interaksi chat AI Inventory Assistant."""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field

from .inventory import InventoryItem
from ..core.rules import StockStatus


class ChatRequest(BaseModel):
    """Payload permintaan interaksi pengguna ke AI Assistant."""
    message: str = Field(
        ...,
        min_length=2,
        max_length=500,
        description="Pertanyaan atau perintah seputar stok inventaris ROKKUS.",
        examples=["Bahan baku apa saja yang stoknya kritis hari ini?"]
    )
    category_filter: Optional[str] = Field(
        default=None,
        description="Filter opsional untuk kategori barang (bahan_baku, topping_filling, produk_jadi, kemasan)."
    )
    status_filter: Optional[StockStatus] = Field(
        default=None,
        description="Filter opsional status stok (SAFE, WARNING, CRITICAL)."
    )
    session_id: Optional[str] = Field(
        default=None,
        description="ID sesi unik pengguna untuk tracking konteks."
    )


class AssistantMeta(BaseModel):
    """Metadata eksekusi respons asisten."""
    provider: Literal["mock", "gemini"] = Field(
        default="mock",
        description="Identitas penyedia model AI. Wajib bernilai 'mock' pada prototipe awal."
    )
    tokens_estimated: int = Field(default=0, description="Estimasi token (0 untuk mode mock).")
    processed_at: str = Field(..., description="Timestamp respons dalam format ISO-8601.")
    context_items_count: int = Field(default=0, description="Jumlah item data yang dijadikan konteks.")


class AssistantMessage(BaseModel):
    """Konten jawaban dari asisten inventaris."""
    reply: str = Field(..., description="Teks jawaban penjelasan dari asisten.")
    context_items: List[InventoryItem] = Field(
        default=[],
        description="Daftar item inventaris terkait yang digunakan sebagai landasan respons."
    )
    suggested_actions: List[str] = Field(
        default=[],
        description="Rekomendasi tindakan operasional untuk UMKM (misal restock, cek fisik)."
    )
    meta: AssistantMeta


class ChatResponse(BaseModel):
    """Respons standar API chat."""
    status: Literal["success", "error"] = "success"
    data: AssistantMessage

