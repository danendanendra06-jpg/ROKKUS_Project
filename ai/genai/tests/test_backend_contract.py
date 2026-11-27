"""Contract test dan validasi integrasi payload Backend & Dataset Data Science (Tahap 6A).

Memvalidasi:
1. Kontrak request simulasi backend (format tanggal ISO, items, types, optional fields).
2. Kontrak response endpoint DailyStockSummary (struktur JSON, nested fields, data types).
3. Kontrak suggested_actions sesuai skema List[str].
4. Penanganan validasi request backend (HTTP 422 untuk nilai negatif, nama kosong, format invalid).
5. Integrasi 29 produk sintetis Data Science pada tanggal pertama dataset (5 EMPTY, 8 LOW, 16 SAFE).
"""

from datetime import date
from pathlib import Path
import sys
import unittest

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    from fastapi.testclient import TestClient
    from src.main import app
    from src.core.config import settings
    from src.adapters.ds_dataset_adapter import DSDatasetAdapter
    from src.services.summary_service import DailySummaryService
    from src.schemas.summary import (
        DailyStockItemInput,
        DailyStockSummaryRequest,
        DailyStockSummaryResponse,
        StockStatusCounts,
    )
    from src.core.rules import StockStatus
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


class TestBackendContract(unittest.TestCase):
    """Pengujian kontrak REST API untuk simulasi payload backend."""

    def setUp(self):
        if not FASTAPI_AVAILABLE:
            self.skipTest("FastAPI belum terinstal.")
        self._orig_provider = settings.LLM_PROVIDER
        settings.LLM_PROVIDER = "mock"
        self.client = TestClient(app)

    def tearDown(self):
        if FASTAPI_AVAILABLE:
            settings.LLM_PROVIDER = self._orig_provider

    def test_backend_standard_request_contract(self):
        """Memvalidasi payload request standar dari backend menghasilkan respon 200 dengan struktur lengkap."""
        payload = {
            "date": "2026-11-19",
            "store_name": "ROKKUS Store Pusat",
            "items": [
                {
                    "name": "Lotus Biscoff",
                    "current_stock": 0.0,
                    "minimum_stock": 5.0,
                    "unit": "porsi",
                    "category": "Roti Manis",
                },
                {
                    "name": "Keju Slice",
                    "current_stock": 3.0,
                    "minimum_stock": 5.0,
                    "unit": "slice",
                    "category": "Tambahan",
                },
                {
                    "name": "Roti Gandum",
                    "current_stock": 15.0,
                    "minimum_stock": 5.0,
                    "unit": "buah",
                    "category": "Bahan Baku",
                },
            ],
        }

        response = self.client.post("/api/v1/summary/daily", json=payload)
        self.assertEqual(response.status_code, 200)

        body = response.json()
        # Top-level contract
        self.assertEqual(body["status"], "success")
        self.assertIn("data", body)
        data = body["data"]

        # Response contract fields
        self.assertEqual(data["date"], "2026-11-19")
        self.assertEqual(data["store_name"], "ROKKUS Store Pusat")
        self.assertIsInstance(data["summary"], str)
        self.assertGreater(len(data["summary"]), 0)

        # Status counts contract
        counts = data["status_counts"]
        self.assertEqual(counts["total_items"], 3)
        self.assertEqual(counts["empty"], 1)
        self.assertEqual(counts["low"], 1)
        self.assertEqual(counts["safe"], 1)

        # Items list contract
        items = data["items"]
        self.assertEqual(len(items), 3)
        for item in items:
            self.assertIn("name", item)
            self.assertIn("current_stock", item)
            self.assertIn("minimum_stock", item)
            self.assertIn("unit", item)
            self.assertIn("status", item)
            self.assertIn(item["status"], ["EMPTY", "LOW", "SAFE"])

        # Suggested actions contract: List[str]
        actions = data["suggested_actions"]
        self.assertIsInstance(actions, list)
        self.assertGreater(len(actions), 0)
        for act in actions:
            self.assertIsInstance(act, str)

        # Meta contract
        meta = data["meta"]
        self.assertIn("provider", meta)
        self.assertIn("requested_provider", meta)
        self.assertIn("execution_provider", meta)
        self.assertIn("fallback_applied", meta)
        self.assertIn("guardrail_status", meta)
        self.assertIn("disclaimer", meta)
        self.assertIsInstance(meta["fallback_applied"], bool)
        self.assertIsInstance(meta["disclaimer"], str)

    def test_backend_minimal_payload_contract(self):
        """Memvalidasi payload backend dengan field opsional yang diabaikan (store_name dan category)."""
        payload = {
            "date": "2026-11-19",
            "items": [
                {
                    "name": "Kopi Susu",
                    "current_stock": 10.0,
                    "minimum_stock": 5.0,
                    "unit": "cup",
                }
            ],
        }

        response = self.client.post("/api/v1/summary/daily", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["store_name"], "UMKM ROKKUS Mardani Raya")
        self.assertEqual(data["status_counts"]["safe"], 1)

    def test_backend_validation_error_contract(self):
        """Memvalidasi kontrak response HTTP 422 saat backend mengirim data invalid."""
        # 1. Missing date
        res = self.client.post("/api/v1/summary/daily", json={"items": [{"name": "A", "current_stock": 1, "unit": "pcs"}]})
        self.assertEqual(res.status_code, 422)

        # 2. Negative stock
        res = self.client.post("/api/v1/summary/daily", json={"date": "2026-11-19", "items": [{"name": "A", "current_stock": -1, "unit": "pcs"}]})
        self.assertEqual(res.status_code, 422)

        # 3. Empty name
        res = self.client.post("/api/v1/summary/daily", json={"date": "2026-11-19", "items": [{"name": "", "current_stock": 1, "unit": "pcs"}]})
        self.assertEqual(res.status_code, 422)


class TestDS29SyntheticIntegration(unittest.TestCase):
    """Pengujian integrasi langsung dengan 29 produk sintetis dataset Data Science."""

    def setUp(self):
        if not FASTAPI_AVAILABLE:
            self.skipTest("FastAPI belum terinstal.")
        self._orig_provider = settings.LLM_PROVIDER
        settings.LLM_PROVIDER = "mock"
        self.adapter = DSDatasetAdapter()
        self.service = DailySummaryService()

    def tearDown(self):
        if FASTAPI_AVAILABLE:
            settings.LLM_PROVIDER = self._orig_provider

    def test_ds_29_synthetic_products_classification_counts(self):
        """Memvalidasi pembacaan 29 produk sintetis DS menghasilkan tepat 5 EMPTY, 8 LOW, dan 16 SAFE."""
        dates = self.adapter.get_available_dates()
        self.assertGreater(len(dates), 0)
        first_date = dates[0]

        request = self.adapter.load_request(first_date)
        self.assertEqual(len(request.items), 29)

        response = self.service.generate_summary(request)

        # Validasi struktur respon
        self.assertEqual(response.status, "success")
        self.assertTrue(response.data.meta.is_synthetic)
        self.assertEqual(response.data.status_counts.total_items, 29)

        # Verifikasi distribusi status stok sesuai aturan DS
        self.assertEqual(response.data.status_counts.empty, 5, "Jumlah item EMPTY harus tepat 5")
        self.assertEqual(response.data.status_counts.low, 8, "Jumlah item LOW harus tepat 8")
        self.assertEqual(response.data.status_counts.safe, 16, "Jumlah item SAFE harus tepat 16")

        # Verifikasi kelima produk EMPTY spesifik
        empty_items = [item.name for item in response.data.items if item.status == StockStatus.EMPTY]
        expected_empty = {"Nutella Keju", "Srikaya", "Strawberry", "Tiramisu", "Telur Beef Sosis"}
        self.assertEqual(set(empty_items), expected_empty)

        # Verifikasi suggested_actions format
        self.assertIsInstance(response.data.suggested_actions, list)
        self.assertGreater(len(response.data.suggested_actions), 0)
        for action in response.data.suggested_actions:
            self.assertIsInstance(action, str)

        # Verifikasi meta fallback dan requested/execution provider
        self.assertEqual(response.data.meta.requested_provider, "mock")
        self.assertEqual(response.data.meta.execution_provider, "mock")
        self.assertEqual(response.data.meta.provider, "mock")
        self.assertFalse(response.data.meta.fallback_applied)


if __name__ == "__main__":
    unittest.main()
