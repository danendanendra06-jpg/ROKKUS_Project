"""Skema data inventaris (DTO) untuk inventaris UMKM ROKKUS."""

from typing import List, Optional
from pydantic import BaseModel, Field

from ..core.rules import StockStatus, evaluate_stock_status


class InventoryMetadata(BaseModel):
    """Metadata dataset sintetis."""
    project: str
    dataset_type: str
    disclaimer: str
    version: str = "1.0.0"
    generated_at: str


class StoreInfo(BaseModel):
    """Informasi unit usaha (ilustratif)."""
    id: str
    name: str
    address: Optional[str] = None
    business_unit: str = "Kuliner Roti Kukus"


class InventoryItem(BaseModel):
    """Item barang inventaris."""
    id: str = Field(..., description="Kode unik item, misal BB-001, PJ-001")
    name: str = Field(..., description="Nama barang (ilustratif)")
    category: str = Field(..., description="Kategori: bahan_baku, topping_filling, produk_jadi, kemasan")
    current_stock: float = Field(..., ge=0, description="Jumlah stok fisik saat ini")
    minimum_stock: float = Field(..., ge=0, description="Ambang batas minimum stok")
    unit: str = Field(..., description="Satuan unit (kg, porsi, pcs, dll.)")
    unit_cost: Optional[float] = Field(default=None, description="Estimasi biaya per unit (IDR)")
    status: StockStatus = Field(..., description="Status stok: SAFE, WARNING, atau CRITICAL")
    last_restocked: Optional[str] = None
    notes: Optional[str] = None

    def refresh_status(self) -> StockStatus:
        """Memperbarui nilai status berdasarkan aturan konsisten."""
        calculated = evaluate_stock_status(self.current_stock, self.minimum_stock)
        self.status = calculated
        return calculated


class TransactionRecord(BaseModel):
    """Catatan riwayat transaksi stok masuk/keluar."""
    transaction_id: str
    item_id: str
    item_name: str
    type: str = Field(..., description="Tipe mutasi: IN atau OUT")
    quantity: float = Field(..., gt=0)
    unit: str
    reason: Optional[str] = None
    timestamp: str


class InventorySnapshot(BaseModel):
    """Snapshot keseluruhan inventaris ROKKUS."""
    metadata: InventoryMetadata
    store: StoreInfo
    items: List[InventoryItem]
    recent_transactions: List[TransactionRecord] = []

