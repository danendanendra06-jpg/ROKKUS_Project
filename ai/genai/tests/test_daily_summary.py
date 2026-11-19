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
    from src.core.config import settings
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
        self._orig_provider = settings.LLM_PROVIDER
        settings.LLM_PROVIDER = "mock"
        self.service = DailySummaryService()

    def tearDown(self):
        if FASTAPI_AVAILABLE:
            settings.LLM_PROVIDER = self._orig_provider

    def test_mixed_stock_items_summary(self):
        """Memvalidasi kalkulasi status dan narasi ringkasan untuk item campuran."""
        request = DailyStockSummaryRequest(
            date=date(2026, 11, 15),
            store_name="ROKKUS Mardani Raya",
            items=[
                DailyStockItemInput(
                    name="Lotus Biscoff",
                    current_stock=0.0,   # EMPTY
                    minimum_stock=5.0,
                    unit="porsi",
                ),
                DailyStockItemInput(
                    name="Coklat Keju",
                    current_stock=3.0,   # LOW (1–5)
                    minimum_stock=5.0,
                    unit="porsi",
                ),
                DailyStockItemInput(
                    name="Telur Mayo",
                    current_stock=20.0,  # SAFE (> 5)
                    minimum_stock=5.0,
                    unit="porsi",
                ),
            ],
        )

        response = self.service.generate_summary(request)

        self.assertEqual(response.status, "success")
        data = response.data
        self.assertEqual(data.date, "2026-11-15")
        self.assertEqual(data.status_counts.total_items, 3)
        self.assertEqual(data.status_counts.empty, 1)
        self.assertEqual(data.status_counts.low, 1)
        self.assertEqual(data.status_counts.safe, 1)

        # Verifikasi metadata
        self.assertEqual(data.meta.provider, "mock")
        self.assertTrue(data.meta.is_synthetic)
        self.assertEqual(data.meta.source, "synthetic_input")

        # Verifikasi ketiadaan prediksi waktu spekulatif
        self.assertNotIn("1-2 hari", data.summary)
        self.assertNotIn("akan habis pada", data.summary)

        # Verifikasi item detail
        self.assertEqual(data.items[0].status, StockStatus.EMPTY)
        self.assertEqual(data.items[1].status, StockStatus.LOW)
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
        self.assertEqual(response.data.status_counts.empty, 0)
        self.assertEqual(response.data.status_counts.low, 0)
        self.assertEqual(response.data.status_counts.safe, 1)
        self.assertIn("aman", response.data.summary.lower())

    def test_all_empty_scenario(self):
        """Memvalidasi aksi saat barang dalam kondisi habis (EMPTY)."""
        request = DailyStockSummaryRequest(
            date=date(2026, 11, 15),
            items=[
                DailyStockItemInput(
                    name="Ragi Instan",
                    current_stock=0.0,   # == 0 → EMPTY
                    minimum_stock=5.0,
                    unit="sachet",
                )
            ],
        )

        response = self.service.generate_summary(request)
        self.assertEqual(response.data.status_counts.empty, 1)
        self.assertEqual(response.data.status_counts.safe, 0)
        self.assertIn("restock", response.data.suggested_actions[0].lower())

    def test_low_and_empty_scenario(self):
        """Memvalidasi penanganan barang EMPTY dan LOW."""
        request = DailyStockSummaryRequest(
            date=date(2026, 11, 15),
            items=[
                DailyStockItemInput(
                    name="Bahan Percobaan",
                    current_stock=5.0,  # 1–5 → LOW
                    minimum_stock=0.0,
                    unit="kg",
                ),
                DailyStockItemInput(
                    name="Bahan Kosong",
                    current_stock=0.0,  # == 0 → EMPTY
                    minimum_stock=0.0,
                    unit="kg",
                ),
            ],
        )

        response = self.service.generate_summary(request)
        self.assertEqual(response.data.status_counts.low, 1)
        self.assertEqual(response.data.status_counts.empty, 1)
        self.assertEqual(response.data.status_counts.safe, 0)


class TestDailySummaryEndpointsIntegration(unittest.TestCase):
    """Pengujian integrasi endpoint HTTP POST /api/v1/summary/daily."""

    def setUp(self):
        if not FASTAPI_AVAILABLE:
            self.skipTest("FastAPI belum terinstal di environment.")
        self._orig_provider = settings.LLM_PROVIDER
        settings.LLM_PROVIDER = "mock"
        self.client = TestClient(app)

    def tearDown(self):
        if FASTAPI_AVAILABLE:
            settings.LLM_PROVIDER = self._orig_provider

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
        self.assertEqual(data["data"]["status_counts"]["low"], 1)
        self.assertEqual(data["data"]["status_counts"]["empty"], 0)
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

