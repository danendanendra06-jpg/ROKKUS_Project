"""Interface abstrak untuk akses data inventaris."""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..core.rules import StockStatus
from ..schemas.inventory import InventoryItem, InventorySnapshot, TransactionRecord


class BaseInventoryRepository(ABC):
    """Kontrak abstrak untuk membaca data inventaris.

    Dapat diimplementasikan oleh MockInventoryRepository (JSON lokal)
    maupun BackendInventoryRepository (HTTP client ke backend utama masa depan).
    """

    @abstractmethod
    def get_snapshot(self) -> InventorySnapshot:
        """Mengambil seluruh snapshot data inventaris."""
        pass

    @abstractmethod
    def get_all_items(self) -> List[InventoryItem]:
        """Mengambil seluruh daftar item inventaris."""
        pass

    @abstractmethod
    def get_items_by_status(self, status: StockStatus) -> List[InventoryItem]:
        """Mengambil daftar item berdasarkan status stok (SAFE, WARNING, CRITICAL)."""
        pass

    @abstractmethod
    def get_items_by_category(self, category: str) -> List[InventoryItem]:
        """Mengambil daftar item berdasarkan kategori barang."""
        pass

    @abstractmethod
    def get_item_by_id(self, item_id: str) -> Optional[InventoryItem]:
        """Mengambil detail satu item berdasarkan kode ID unik."""
        pass

    @abstractmethod
    def get_recent_transactions(self, limit: int = 5) -> List[TransactionRecord]:
        """Mengambil catatan mutasi transaksi inventaris terkini."""
        pass

