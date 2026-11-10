"""Pengujian aturan konsisten status stok SAFE, WARNING, dan CRITICAL."""

import sys
from pathlib import Path
import unittest

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.core.rules import (
    StockStatus,
    evaluate_stock_status,
    STOCK_STATUS_DESCRIPTIONS,
)


class TestStockRules(unittest.TestCase):
    """Memvalidasi formula penentuan status ketersediaan barang."""

    def test_critical_condition(self):
        """Stok <= batas minimum harus diklasifikasikan sebagai CRITICAL."""
        # Kasus 1: Stok sama persis dengan batas minimum
        self.assertEqual(evaluate_stock_status(10.0, 10.0), StockStatus.CRITICAL)
        # Kasus 2: Stok jauh di bawah batas minimum
        self.assertEqual(evaluate_stock_status(2.5, 10.0), StockStatus.CRITICAL)
        # Kasus 3: Stok habis (0)
        self.assertEqual(evaluate_stock_status(0.0, 5.0), StockStatus.CRITICAL)

    def test_warning_condition(self):
        """Batas minimum < Stok <= (Batas minimum * 1.5) harus berstatus WARNING."""
        # Batas minimum 10 -> rentang warning: > 10 dan <= 15
        self.assertEqual(evaluate_stock_status(10.1, 10.0), StockStatus.WARNING)
        self.assertEqual(evaluate_stock_status(12.5, 10.0), StockStatus.WARNING)
        self.assertEqual(evaluate_stock_status(15.0, 10.0), StockStatus.WARNING)

    def test_safe_condition(self):
        """Stok > (Batas minimum * 1.5) harus berstatus SAFE."""
        # Batas minimum 10 -> rentang safe: > 15
        self.assertEqual(evaluate_stock_status(15.1, 10.0), StockStatus.SAFE)
        self.assertEqual(evaluate_stock_status(25.0, 10.0), StockStatus.SAFE)
        self.assertEqual(evaluate_stock_status(100.0, 10.0), StockStatus.SAFE)

    def test_descriptions_registered(self):
        """Memastikan setiap status memiliki dokumentasi deskripsi."""
        for status in [StockStatus.SAFE, StockStatus.WARNING, StockStatus.CRITICAL]:
            self.assertIn(status, STOCK_STATUS_DESCRIPTIONS)
            self.assertTrue(len(STOCK_STATUS_DESCRIPTIONS[status]) > 10)


if __name__ == "__main__":
    unittest.main()

