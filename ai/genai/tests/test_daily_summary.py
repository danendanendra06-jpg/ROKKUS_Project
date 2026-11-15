"""Unit test dan integration test untuk fitur Daily Stock Summary."""

from datetime import date
import sys
from pathlib import Path
import unittest

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    from fastapi.testclient import TestClient
    from src.main import app
    from src.services.summary_service import DailySummaryService
    from src.schemas.summary import (
        DailyStockItemInput,
        DailyStockSummaryRequest,
    )
    from src.core.rules import StockStatus
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


class TestDailySummaryServiceUnit(unittest.TestCase):
    """Pengujian level unit untuk DailySummaryService."""

    def setUp(self):
        if not FASTAPI_AVAILABLE:
            self.skipTest("FastAPI / Pydantic belum terinstal di environment.")
        self.service = DailySummaryService()

    def test_mixed_stock_items_summary(self):
        """Memvalidasi kalkulasi status dan narasi ringkasan untuk item campuran."""
        request = DailyStockSummaryRequest(
            date=date(2026, 11, 15),
            store_name="ROKKUS Mardani Raya",
            items=[
                DailyStockItemInput(
                    name="Tepung Terigu",
                    current_stock=4.0,
                    minimum_stock=10.0,
                    unit="kg",
                ),
                DailyStockItemInput(
                    name="Margarin Bakeri",
                    current_stock=8.0,
                    minimum_stock=6.0,
                    unit="kg",
                ),
                DailyStockItemInput(
                    name="Gula Pasir",
                    current_stock=25.0,
                    minimum_stock=10.0,
                    unit="kg",
                ),
            ],
        )

        response = self.service.generate_summary(request)

        self.assertEqual(response.status, "success")
        data = response.data
        self.assertEqual(data.date, "2026-11-15")
        self.assertEqual(data.status_counts.total_items, 3)
        self.assertEqual(data.status_counts.critical, 1)
        self.assertEqual(data.status_counts.warning, 1)
        self.assertEqual(data.status_counts.safe, 1)

        # Verifikasi metadata
        self.assertEqual(data.meta.provider, "mock")
        self.assertTrue(data.meta.is_synthetic)
        self.assertEqual(data.meta.source, "synthetic_input")

        # Verifikasi ketiadaan prediksi waktu spekulatif
        self.assertNotIn("1-2 hari", data.summary)
        self.assertNotIn("akan habis pada", data.summary)

        # Verifikasi item detail
        self.assertEqual(data.items[0].status, StockStatus.CRITICAL)
        self.assertEqual(data.items[1].status, StockStatus.WARNING)
        self.assertEqual(data.items[2].status, StockStatus.SAFE)

    def test_all_safe_scenario(self):
        """Memvalidasi narasi saat seluruh barang dalam kondisi aman."""
        request = DailyStockSummaryRequest(
            date=date(2026, 11, 15),
            items=[
                DailyStockItemInput(
                    name="Kotak Dus",
                    current_stock=200.0,
                    minimum_stock=50.0,
                    unit="pcs",
                )
            ],
        )

        response = self.service.generate_summary(request)
        self.assertEqual(response.data.status_counts.critical, 0)
        self.assertEqual(response.data.status_counts.warning, 0)
        self.assertEqual(response.data.status_counts.safe, 1)
        self.assertIn("aman", response.data.summary.lower())

    def test_all_critical_scenario(self):
        """Memvalidasi aksi saat seluruh barang dalam kondisi kritis."""
        request = DailyStockSummaryRequest(
            date=date(2026, 11, 15),
            items=[
                DailyStockItemInput(
                    name="Ragi Instan",
                    current_stock=0.0,
                    minimum_stock=5.0,
                    unit="sachet",
                )
            ],
        )

        response = self.service.generate_summary(request)
        self.assertEqual(response.data.status_counts.critical, 1)
        self.assertEqual(response.data.status_counts.safe, 0)
        self.assertIn("restock", response.data.suggested_actions[0].lower())

    def test_zero_minimum_stock_in_service(self):
        """Memvalidasi penanganan barang dengan batas minimum 0 di dalam ringkasan."""
        request = DailyStockSummaryRequest(
            date=date(2026, 11, 15),
            items=[
                DailyStockItemInput(
                    name="Bahan Percobaan",
                    current_stock=5.0,
                    minimum_stock=0.0,
                    unit="kg",
                ),
                DailyStockItemInput(
                    name="Bahan Kosong",
                    current_stock=0.0,
                    minimum_stock=0.0,
                    unit="kg",
                ),
            ],
        )

        response = self.service.generate_summary(request)
        self.assertEqual(response.data.status_counts.safe, 1)
        self.assertEqual(response.data.status_counts.critical, 1)


class TestDailySummaryEndpointsIntegration(unittest.TestCase):
    """Pengujian integrasi endpoint HTTP POST /api/v1/summary/daily."""

    def setUp(self):
        if not FASTAPI_AVAILABLE:
            self.skipTest("FastAPI belum terinstal di environment.")
        self.client = TestClient(app)

    def test_endpoint_success_flow(self):
        """Pengujian flow normal endpoint dengan data sintetis valid."""
        payload = {
            "date": "2026-11-15",
            "store_name": "ROKKUS Mardani Raya (Ilustratif)",
            "items": [
                {
                    "name": "Tepung Terigu Segitiga Biru",
                    "current_stock": 4.0,
                    "minimum_stock": 10.0,
                    "unit": "kg",
                    "category": "bahan_baku",
                },
                {
                    "name": "Gula Pasir Tebu",
                    "current_stock": 25.0,
                    "minimum_stock": 10.0,
                    "unit": "kg",
                    "category": "bahan_baku",
                },
            ],
        }

        response = self.client.post("/api/v1/summary/daily", json=payload)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["data"]["date"], "2026-11-15")
        self.assertEqual(data["data"]["meta"]["provider"], "mock")
        self.assertTrue(data["data"]["meta"]["is_synthetic"])
        self.assertEqual(data["data"]["status_counts"]["total_items"], 2)
        self.assertEqual(data["data"]["status_counts"]["critical"], 1)
        self.assertEqual(data["data"]["status_counts"]["safe"], 1)

    def test_endpoint_empty_items_validation_error(self):
        """Memastikan list items kosong ditolak dengan HTTP 422."""
        payload = {
            "date": "2026-11-15",
            "items": [],
        }
        response = self.client.post("/api/v1/summary/daily", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_endpoint_negative_stock_validation_error(self):
        """Memastikan stok negatif ditolak dengan HTTP 422."""
        payload = {
            "date": "2026-11-15",
            "items": [
                {
                    "name": "Tepung Terigu",
                    "current_stock": -5.0,
                    "minimum_stock": 10.0,
                    "unit": "kg",
                }
            ],
        }
        response = self.client.post("/api/v1/summary/daily", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_endpoint_negative_minimum_stock_validation_error(self):
        """Memastikan minimum stok negatif ditolak dengan HTTP 422."""
        payload = {
            "date": "2026-11-15",
            "items": [
                {
                    "name": "Tepung Terigu",
                    "current_stock": 10.0,
                    "minimum_stock": -1.0,
                    "unit": "kg",
                }
            ],
        }
        response = self.client.post("/api/v1/summary/daily", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_endpoint_empty_name_or_whitespace_error(self):
        """Memastikan nama barang kosong atau hanya spasi ditolak dengan HTTP 422."""
        payload = {
            "date": "2026-11-15",
            "items": [
                {
                    "name": "   ",
                    "current_stock": 10.0,
                    "minimum_stock": 5.0,
                    "unit": "kg",
                }
            ],
        }
        response = self.client.post("/api/v1/summary/daily", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_endpoint_empty_unit_or_whitespace_error(self):
        """Memastikan satuan unit kosong atau hanya spasi ditolak dengan HTTP 422."""
        payload = {
            "date": "2026-11-15",
            "items": [
                {
                    "name": "Tepung Terigu",
                    "current_stock": 10.0,
                    "minimum_stock": 5.0,
                    "unit": "  ",
                }
            ],
        }
        response = self.client.post("/api/v1/summary/daily", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_endpoint_invalid_calendar_date_error(self):
        """Memastikan tanggal kalender yang tidak valid (misal 31 Februari) ditolak dengan HTTP 422."""
        payload = {
            "date": "2026-02-31",  # Tanggal kalender tidak ada
            "items": [
                {
                    "name": "Tepung Terigu",
                    "current_stock": 10.0,
                    "minimum_stock": 5.0,
                    "unit": "kg",
                }
            ],
        }
        response = self.client.post("/api/v1/summary/daily", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_endpoint_nan_or_inf_stock_error(self):
        """Memastikan nilai non-finite (NaN / Infinity) ditolak."""
        payload = {
            "date": "2026-11-15",
            "items": [
                {
                    "name": "Tepung Terigu",
                    "current_stock": "NaN",
                    "minimum_stock": 5.0,
                    "unit": "kg",
                }
            ],
        }
        response = self.client.post("/api/v1/summary/daily", json=payload)
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()

