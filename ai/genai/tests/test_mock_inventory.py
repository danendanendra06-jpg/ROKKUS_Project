"""Pengujian Mock Inventory Repository dan dataset sintetis."""

import sys
from pathlib import Path
import unittest

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.core.rules import StockStatus
from src.repositories.mock_inventory import MockInventoryRepository


class TestMockInventoryRepository(unittest.TestCase):
    """Pengujian modul repository pembaca dataset sintetis."""

    def setUp(self):
        data_path = BASE_DIR / "data" / "synthetic_inventory.json"
        self.repo = MockInventoryRepository(file_path=data_path)

    def test_load_snapshot_and_disclaimer(self):
        """Memastikan dataset memuat disclaimer bahwa data bersifat ilustratif."""
        snapshot = self.repo.get_snapshot()
        self.assertIsNotNone(snapshot.metadata.disclaimer)
        self.assertIn("ILUSTRATIF", snapshot.metadata.disclaimer)
        self.assertIn("BUKAN", snapshot.metadata.disclaimer)

    def test_get_all_items(self):
        """Memastikan daftar barang tidak kosong dan memiliki nama ilustratif."""
        items = self.repo.get_all_items()
        self.assertGreater(len(items), 0)
        for item in items:
            self.assertTrue(item.name.startswith("[Ilustratif]"))
            self.assertIn(item.status, [StockStatus.SAFE, StockStatus.WARNING, StockStatus.CRITICAL])

    def test_get_items_by_status(self):
        """Memastikan pemfilteran status CRITICAL akurat."""
        critical_items = self.repo.get_items_by_status(StockStatus.CRITICAL)
        self.assertGreater(len(critical_items), 0)
        for item in critical_items:
            self.assertEqual(item.status, StockStatus.CRITICAL)
            # Pastikan sesuai aturan: current_stock <= minimum_stock
            self.assertLessEqual(item.current_stock, item.minimum_stock)

    def test_get_items_by_category(self):
        """Memastikan pemfilteran kategori bahan_baku bekerja."""
        bahan_baku = self.repo.get_items_by_category("bahan_baku")
        self.assertGreater(len(bahan_baku), 0)
        for item in bahan_baku:
            self.assertEqual(item.category, "bahan_baku")

    def test_get_item_by_id(self):
        """Memastikan pencarian item berdasarkan ID unik."""
        item = self.repo.get_item_by_id("BB-001")
        self.assertIsNotNone(item)
        self.assertEqual(item.id, "BB-001")

        # Item yang tidak ada harus mengembalikan None
        non_existent = self.repo.get_item_by_id("NON-EXISTENT-999")
        self.assertIsNone(non_existent)


if __name__ == "__main__":
    unittest.main()

