"""Pengujian aturan konsisten status stok EMPTY, LOW, dan SAFE.

Diselaraskan dengan dataset Data Science ROKKUS (origin/main):
- EMPTY: stok habis (current_stock == 0)
- LOW:   stok menipis (0 < current_stock <= 5)
- SAFE:  stok aman (current_stock > 5)

Catatan: parameter minimum_stock dipertahankan pada signature
evaluate_stock_status() untuk kompatibilitas API, namun tidak lagi
memengaruhi penentuan status (threshold absolut yang berlaku).
"""

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
    STOCK_THRESHOLD_EMPTY,
    STOCK_THRESHOLD_LOW,
)


class TestStockRules(unittest.TestCase):
    """Memvalidasi formula penentuan status ketersediaan barang (threshold absolut)."""

    # -------------------------------------------------------------------
    # Pengujian status EMPTY (stok = 0)
    # -------------------------------------------------------------------
    def test_empty_condition_zero_stock(self):
        """Stok == 0 harus diklasifikasikan sebagai EMPTY."""
        self.assertEqual(evaluate_stock_status(0.0, 5.0), StockStatus.EMPTY)

    def test_empty_condition_zero_stock_zero_minimum(self):
        """Stok == 0 dengan minimum 0 tetap EMPTY."""
        self.assertEqual(evaluate_stock_status(0.0, 0.0), StockStatus.EMPTY)

    def test_empty_condition_various_minimums(self):
        """Stok == 0 harus EMPTY tanpa memandang nilai minimum_stock."""
        for min_stock in [0.0, 1.0, 5.0, 10.0, 100.0]:
            with self.subTest(minimum_stock=min_stock):
                self.assertEqual(evaluate_stock_status(0.0, min_stock), StockStatus.EMPTY)

    # -------------------------------------------------------------------
    # Pengujian status LOW (0 < stok <= 5)
    # -------------------------------------------------------------------
    def test_low_condition_stock_one(self):
        """Stok == 1 harus diklasifikasikan sebagai LOW."""
        self.assertEqual(evaluate_stock_status(1.0, 5.0), StockStatus.LOW)

    def test_low_condition_stock_exactly_at_threshold(self):
        """Stok == 5 (threshold STOCK_THRESHOLD_LOW) harus masih LOW."""
        self.assertEqual(evaluate_stock_status(5.0, 5.0), StockStatus.LOW)
        self.assertEqual(evaluate_stock_status(5.0, 0.0), StockStatus.LOW)
        self.assertEqual(evaluate_stock_status(5.0, 100.0), StockStatus.LOW)

    def test_low_condition_stock_in_range(self):
        """Stok dalam rentang 1–5 harus LOW tanpa memandang minimum_stock."""
        for stock in [1.0, 2.0, 3.0, 4.0, 4.9, 5.0]:
            with self.subTest(current_stock=stock):
                result = evaluate_stock_status(stock, 10.0)
                self.assertEqual(result, StockStatus.LOW, f"Stok {stock} harus LOW")

    # -------------------------------------------------------------------
    # Pengujian status SAFE (stok > 5)
    # -------------------------------------------------------------------
    def test_safe_condition_stock_just_above_threshold(self):
        """Stok == 5.1 (di atas threshold 5) harus SAFE."""
        self.assertEqual(evaluate_stock_status(5.1, 5.0), StockStatus.SAFE)
        self.assertEqual(evaluate_stock_status(5.1, 10.0), StockStatus.SAFE)

    def test_safe_condition_large_stock(self):
        """Stok besar harus SAFE tanpa memandang nilai minimum_stock."""
        self.assertEqual(evaluate_stock_status(100.0, 10.0), StockStatus.SAFE)
        self.assertEqual(evaluate_stock_status(50.0, 100.0), StockStatus.SAFE)
        self.assertEqual(evaluate_stock_status(6.0, 0.0), StockStatus.SAFE)

    def test_safe_condition_stock_in_range(self):
        """Stok > 5 harus SAFE tanpa memandang minimum_stock."""
        for stock in [6.0, 10.0, 25.0, 100.0]:
            with self.subTest(current_stock=stock):
                result = evaluate_stock_status(stock, 5.0)
                self.assertEqual(result, StockStatus.SAFE, f"Stok {stock} harus SAFE")

    # -------------------------------------------------------------------
    # Pengujian threshold constants
    # -------------------------------------------------------------------
    def test_threshold_values_aligned_with_ds_dataset(self):
        """Nilai threshold harus selaras dengan aturan klasifikasi dataset Data Science."""
        self.assertEqual(STOCK_THRESHOLD_EMPTY, 0)
        self.assertEqual(STOCK_THRESHOLD_LOW, 5)

    # -------------------------------------------------------------------
    # Pengujian minimum_stock tidak memengaruhi status (kompatibilitas API)
    # -------------------------------------------------------------------
    def test_minimum_stock_does_not_affect_status(self):
        """Nilai minimum_stock TIDAK memengaruhi status — threshold absolut yang berlaku."""
        # Stok 3 selalu LOW, berapa pun minimum_stock-nya
        for min_val in [0.0, 1.0, 5.0, 10.0, 50.0]:
            with self.subTest(minimum_stock=min_val):
                self.assertEqual(
                    evaluate_stock_status(3.0, min_val),
                    StockStatus.LOW,
                    f"Stok 3.0 dengan minimum {min_val} harus tetap LOW"
                )

        # Stok 10 selalu SAFE, berapa pun minimum_stock-nya
        for min_val in [0.0, 5.0, 10.0, 20.0]:
            with self.subTest(minimum_stock=min_val):
                self.assertEqual(
                    evaluate_stock_status(10.0, min_val),
                    StockStatus.SAFE,
                    f"Stok 10.0 dengan minimum {min_val} harus tetap SAFE"
                )

    # -------------------------------------------------------------------
    # Pengujian deskripsi status
    # -------------------------------------------------------------------
    def test_descriptions_registered_for_all_statuses(self):
        """Memastikan setiap status memiliki dokumentasi deskripsi."""
        for status in [StockStatus.EMPTY, StockStatus.LOW, StockStatus.SAFE]:
            self.assertIn(status, STOCK_STATUS_DESCRIPTIONS)
            self.assertGreater(len(STOCK_STATUS_DESCRIPTIONS[status]), 10)

    def test_no_critical_or_warning_in_enum(self):
        """Memastikan status lama CRITICAL dan WARNING sudah tidak ada."""
        status_values = [s.value for s in StockStatus]
        self.assertNotIn("CRITICAL", status_values)
        self.assertNotIn("WARNING", status_values)
        self.assertIn("EMPTY", status_values)
        self.assertIn("LOW", status_values)
        self.assertIn("SAFE", status_values)


if __name__ == "__main__":
    unittest.main()

