"""Implementasi repository data inventaris berbasis file JSON sintetis."""

import json
from pathlib import Path
from typing import List, Optional

from .base import BaseInventoryRepository
from ..core.config import resolve_inventory_path
from ..core.rules import StockStatus, evaluate_stock_status
from ..schemas.inventory import (
    InventoryItem,
    InventorySnapshot,
    TransactionRecord,
)


class MockInventoryRepository(BaseInventoryRepository):
    """Repository yang membaca data dummy dari synthetic_inventory.json.

    Menjamin status stok (SAFE, WARNING, CRITICAL) selalu konsisten dengan
    aturan bisnis yang didefinisikan di core.rules.
    """

    def __init__(self, file_path: Optional[str | Path] = None):
        if file_path:
            self.file_path = Path(file_path)
        else:
            self.file_path = resolve_inventory_path()

    def _load_data(self) -> dict:
        """Membaca isi file JSON lokal."""
        if not self.file_path.exists():
            raise FileNotFoundError(
                f"File data inventaris sintetis tidak ditemukan di path: {self.file_path}"
            )
        with open(self.file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_snapshot(self) -> InventorySnapshot:
        """Memuat snapshot lengkap dan melakukan validasi status konsisten."""
        raw_data = self._load_data()
        snapshot = InventorySnapshot.model_validate(raw_data)

        # Harmonisasi status konsisten berdasarkan formula aturan stok
        for item in snapshot.items:
            item.status = evaluate_stock_status(item.current_stock, item.minimum_stock)

        return snapshot

    def get_all_items(self) -> List[InventoryItem]:
        """Mengembalikan seluruh item dengan status yang terverifikasi."""
        return self.get_snapshot().items

    def get_items_by_status(self, status: StockStatus) -> List[InventoryItem]:
        """Menyaring barang berdasarkan status ketersediaan stok."""
        target = status if isinstance(status, StockStatus) else StockStatus(status)
        return [item for item in self.get_all_items() if item.status == target]

    def get_items_by_category(self, category: str) -> List[InventoryItem]:
        """Menyaring barang berdasarkan kategori tertentu (case-insensitive)."""
        target = category.strip().lower()
        return [
            item for item in self.get_all_items()
            if item.category.strip().lower() == target
        ]

    def get_item_by_id(self, item_id: str) -> Optional[InventoryItem]:
        """Mencari item spesifik berdasarkan ID."""
        target = item_id.strip().upper()
        for item in self.get_all_items():
            if item.id.strip().upper() == target:
                return item
        return None

    def get_recent_transactions(self, limit: int = 5) -> List[TransactionRecord]:
        """Mengambil transaksi terkini dengan batasan limit."""
        transactions = self.get_snapshot().recent_transactions
        return transactions[:limit]

