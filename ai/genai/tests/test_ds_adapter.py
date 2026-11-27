"""Unit test untuk DSDatasetAdapter (Tahap 5).

Memvalidasi pembacaan dataset Data Science (read-only), pemetaan kolom ke DTO GenAI,
handling file not found, dan penandaan metadata data sintetis.
"""

from datetime import date
from pathlib import Path
import tempfile
import sys
import unittest

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.adapters.ds_dataset_adapter import (
    DSDatasetAdapter,
    DEFAULT_MINIMUM_STOCK,
    DEFAULT_UNIT,
    DS_DATA_SOURCE,
    DS_DISCLAIMER,
)
from src.core.rules import evaluate_stock_status, StockStatus
from src.schemas.summary import DailyStockSummaryRequest


class TestDSDatasetAdapter(unittest.TestCase):
    """Pengujian adapter dataset Data Science."""

    def setUp(self):
        # Buat file CSV sintetis sementara untuk pengujian unit terisolasi
        self.temp_dir = tempfile.TemporaryDirectory()
        self.csv_path = Path(self.temp_dir.name) / "test_dataset_stok_rokkus.csv"

        csv_content = (
            "product_id,product_name,category,price,tanggal_stok,stok_awal,total_masuk,total_keluar,stok_akhir,status_stok\n"
            "PR001,Lotus Biscoff,Roti Manis,18000,2026-09-01,16,35,39,12,Safe\n"
            "PR004,Nutella Keju,Roti Manis,18000,2026-09-01,20,17,37,0,Empty\n"
            "PR009,Keju,Roti Manis,11000,2026-09-01,20,7,23,4,Low\n"
            "AD001,Keju Slice,Tambahan,2000,2026-09-01,25,10,31,4,Low\n"
            "PR001,Lotus Biscoff,Roti Manis,18000,2026-09-02,12,20,15,17,Safe\n"
        )
        self.csv_path.write_text(csv_content, encoding="utf-8")
        self.adapter = DSDatasetAdapter(csv_path=self.csv_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_request_success(self):
        """Memastikan adapter berhasil mengonversi baris CSV ke DailyStockSummaryRequest."""
        req = self.adapter.load_request(target_date=date(2026, 9, 1))

        self.assertIsInstance(req, DailyStockSummaryRequest)
        self.assertEqual(req.date, date(2026, 9, 1))
        self.assertEqual(len(req.items), 4)

        # Verifikasi item 0: Lotus Biscoff (stok 12 -> SAFE)
        item0 = req.items[0]
        self.assertEqual(item0.id, "PR001")
        self.assertEqual(item0.name, "Lotus Biscoff")
        self.assertEqual(item0.category, "Roti Manis")
        self.assertEqual(item0.current_stock, 12.0)
        self.assertEqual(item0.minimum_stock, DEFAULT_MINIMUM_STOCK)
        self.assertEqual(item0.unit, DEFAULT_UNIT)
        self.assertEqual(evaluate_stock_status(item0.current_stock, item0.minimum_stock), StockStatus.SAFE)

        # Verifikasi item 1: Nutella Keju (stok 0 -> EMPTY)
        item1 = req.items[1]
        self.assertEqual(item1.id, "PR004")
        self.assertEqual(item1.current_stock, 0.0)
        self.assertEqual(evaluate_stock_status(item1.current_stock, item1.minimum_stock), StockStatus.EMPTY)

        # Verifikasi item 2: Keju (stok 4 -> LOW)
        item2 = req.items[2]
        self.assertEqual(item2.id, "PR009")
        self.assertEqual(item2.current_stock, 4.0)
        self.assertEqual(evaluate_stock_status(item2.current_stock, item2.minimum_stock), StockStatus.LOW)

    def test_load_request_default_date_uses_first_available(self):
        """Jika target_date tidak diberikan, menggunakan tanggal pertama di CSV."""
        req = self.adapter.load_request()
        self.assertEqual(req.date, date(2026, 9, 1))

    def test_get_available_dates(self):
        """Memastikan daftar tanggal unik diekstrak dengan benar."""
        dates = self.adapter.get_available_dates()
        self.assertEqual(dates, [date(2026, 9, 1), date(2026, 9, 2)])

    def test_nonexistent_file_raises_filenotfound(self):
        """Memastikan FileNotFoundError dimunculkan jika file CSV tidak ditemukan."""
        bad_adapter = DSDatasetAdapter(csv_path="nonexistent/path/data.csv")
        with self.assertRaises(FileNotFoundError):
            bad_adapter.load_request()

    def test_date_not_found_raises_valueerror(self):
        """Memastikan ValueError dimunculkan jika tanggal tidak ada di dataset."""
        with self.assertRaises(ValueError) as ctx:
            self.adapter.load_request(target_date=date(2026, 12, 31))
        self.assertIn("Tidak ada baris data untuk tanggal", str(ctx.exception))

    def test_custom_minimum_stock_and_unit(self):
        """Memastikan konfigurasi custom minimum_stock dan unit diterapkan."""
        custom_adapter = DSDatasetAdapter(
            csv_path=self.csv_path,
            minimum_stock=10.0,
            unit="pcs",
            store_name="ROKKUS Cabang Uji",
        )
        req = custom_adapter.load_request(target_date=date(2026, 9, 1))
        self.assertEqual(req.store_name, "ROKKUS Cabang Uji")
        for item in req.items:
            self.assertEqual(item.minimum_stock, 10.0)
            self.assertEqual(item.unit, "pcs")

    def test_metadata_has_synthetic_markers(self):
        """Memastikan metadata adapter dengan jelas menandai data sintetis."""
        meta = self.adapter.metadata
        self.assertTrue(meta["is_synthetic"])
        self.assertEqual(meta["source"], DS_DATA_SOURCE)
        self.assertIn("sintetis", meta["disclaimer"].lower())
        self.assertIn("BUKAN", meta["disclaimer"])


if __name__ == "__main__":
    unittest.main()
