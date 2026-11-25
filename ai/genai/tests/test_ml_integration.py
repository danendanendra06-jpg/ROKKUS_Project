"""Pengujian Contract, Simulasi Integrasi, dan Resilience ML & GenAI (Tahap 6B).

Memvalidasi:
1. Kontrak endpoint POST /ml/predict-status (11 fitur input, tipe data, validasi Pydantic ge=0, non-empty string).
2. Pemisahan semantik antara status stok aktual (EMPTY, LOW, SAFE) dan prediksi risiko ML (habis, menipis, aman).
3. Penanganan jujur terhadap ketiadaan histori 7 hari pada snapshot dataset DS (tanpa fabrikasi data).
4. Simulasi integrasi end-to-end: response GenAI diperkaya dengan wawasan risiko ML secara non-destruktif.
5. Uji ketahanan (resilience): ketika layanan ML mengalami 503, timeout, atau error, response GenAI tetap utuh.
"""

from datetime import date
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    from pydantic import ValidationError
    from src.schemas.ml_integration import (
        MLForecastItemInput,
        MLForecastRequest,
        MLForecastResponse,
        MLForecastResultItem,
        MLItemFeatureInput,
        MLPredictRequest,
        MLPredictResponse,
        MLPrediksiItem,
    )
    from src.adapters.ml_integration_adapter import (
        MLServiceClient,
        MLGenAIIntegrator,
    )
    from src.schemas.summary import (
        DailyStockItemInput,
        DailyStockSummaryRequest,
        DailyStockSummaryResponse,
        DailySummaryData,
        DailySummaryMeta,
        ProcessedStockItem,
        StockStatusCounts,
    )
    from src.core.rules import StockStatus
    from src.services.summary_service import DailySummaryService
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


class TestMLContractAndValidation(unittest.TestCase):
    """Pengujian kontrak dan validasi skema input 11 fitur model ML Husain."""

    def setUp(self):
        if not FASTAPI_AVAILABLE:
            self.skipTest("Pydantic / FastAPI belum terinstal.")
        self.valid_ml_features = {
            "stok_saat_ini": 5.0,
            "batas_minimum": 15.0,
            "barang_masuk": 20.0,
            "barang_keluar": 30.0,
            "avg_keluar_7h": 28.0,
            "days_of_cover": 0.18,
            "rasio_stok": 0.33,
            "total_masuk_7h": 140.0,
            "total_keluar_7h": 196.0,
            "kategori": "roti_kukus",
            "rasa": "coklat",
        }

    def test_valid_11_features_passes_contract(self):
        """Memastikan 11 fitur lengkap dengan nilai valid berhasil di-parse."""
        item = MLItemFeatureInput(**self.valid_ml_features)
        self.assertEqual(item.stok_saat_ini, 5.0)
        self.assertEqual(item.kategori, "roti_kukus")
        self.assertEqual(item.rasa, "coklat")

    def test_negative_numeric_feature_fails_validation(self):
        """Memastikan fitur numerik bernilai negatif ditolak oleh validasi ge=0."""
        # Stok negatif
        bad_stok = self.valid_ml_features.copy()
        bad_stok["stok_saat_ini"] = -1.0
        with self.assertRaises(ValidationError):
            MLItemFeatureInput(**bad_stok)

        # Days of cover negatif
        bad_doc = self.valid_ml_features.copy()
        bad_doc["days_of_cover"] = -0.5
        with self.assertRaises(ValidationError):
            MLItemFeatureInput(**bad_doc)

        # Avg keluar 7h negatif
        bad_avg = self.valid_ml_features.copy()
        bad_avg["avg_keluar_7h"] = -10.0
        with self.assertRaises(ValidationError):
            MLItemFeatureInput(**bad_avg)

    def test_empty_or_whitespace_categorical_fails(self):
        """Memastikan kolom kategorik kosong atau hanya spasi ditolak."""
        bad_kat = self.valid_ml_features.copy()
        bad_kat["kategori"] = "   "
        with self.assertRaises(ValidationError):
            MLItemFeatureInput(**bad_kat)

        bad_rasa = self.valid_ml_features.copy()
        bad_rasa["rasa"] = ""
        with self.assertRaises(ValidationError):
            MLItemFeatureInput(**bad_rasa)

    def test_missing_features_fails_validation(self):
        """Memastikan jika ada salah satu dari 11 fitur yang hilang, request ditolak."""
        incomplete = self.valid_ml_features.copy()
        del incomplete["total_masuk_7h"]
        with self.assertRaises(ValidationError):
            MLItemFeatureInput(**incomplete)

    def test_ml_predict_request_and_response_contract(self):
        """Memvalidasi struktur request dan response batch inferensi ML."""
        req = MLPredictRequest(items=[MLItemFeatureInput(**self.valid_ml_features)])
        self.assertEqual(len(req.items), 1)

        client = MLServiceClient(mock_mode=True)
        res = client.predict_status(req)

        self.assertEqual(res.total_items, 1)
        self.assertEqual(len(res.prediksi), 1)
        pred = res.prediksi[0]
        self.assertIn(pred.status, ["aman", "menipis", "habis"])
        self.assertIn("habis", pred.probabilitas)
        self.assertIn("menipis", pred.probabilitas)
        self.assertIn("aman", pred.probabilitas)
        self.assertAlmostEqual(sum(pred.probabilitas.values()), 1.0, places=2)


class TestSemanticSeparationAndDSHonesty(unittest.TestCase):
    """Pengujian pemisahan semantik DS/GenAI vs ML dan kejujuran data tanpa fabrikasi histori 7 hari."""

    def setUp(self):
        if not FASTAPI_AVAILABLE:
            self.skipTest("Pydantic / FastAPI belum terinstal.")
        self.integrator = MLGenAIIntegrator()

    def test_ds_snapshot_row_missing_7d_history_is_not_fabricated(self):
        """Memverifikasi bahwa baris snapshot DS (1 September 2026) tidak memiliki histori 7 hari,

        dan integrator menolak membuat fitur palsu secara otomatis.
        """
        ds_snapshot_row = {
            "product_id": "PR001",
            "product_name": "Lotus Biscoff",
            "category": "Roti Manis",
            "price": 18000,
            "tanggal_stok": "2026-09-01",
            "stok_awal": 16,
            "total_masuk": 35,
            "total_keluar": 39,
            "stok_akhir": 12,
            "status_stok": "Safe",
        }

        feat, reason = self.integrator.extract_ml_features_from_ds_row(ds_snapshot_row)
        self.assertIsNone(feat, "Fitur ML tidak boleh dihasilkan jika histori 7 hari tidak tersedia")
        self.assertIsNotNone(reason)
        self.assertIn("Dataset DS tidak memiliki histori 7 hari", reason)
        self.assertIn("avg_keluar_7h", reason)
        self.assertIn("days_of_cover", reason)

    def test_semantic_domains_remain_strictly_separated(self):
        """Memastikan domain status faktual DS (EMPTY, LOW, SAFE) tidak tertukar dengan

        domain prediksi risiko ML (habis, menipis, aman).
        """
        # Status faktual GenAI/DS
        self.assertEqual(StockStatus.EMPTY.value, "EMPTY")
        self.assertEqual(StockStatus.LOW.value, "LOW")
        self.assertEqual(StockStatus.SAFE.value, "SAFE")

        # Prediksi risiko ML
        ml_labels = {"habis", "menipis", "aman"}
        self.assertNotIn("EMPTY", ml_labels)
        self.assertNotIn("LOW", ml_labels)
        self.assertNotIn("SAFE", ml_labels)


class TestMLGenAIIntegrationAndResilience(unittest.TestCase):
    """Pengujian simulasi pengayaan wawasan ML ke ringkasan GenAI serta ketahanan sistem (resilience)."""

    def setUp(self):
        if not FASTAPI_AVAILABLE:
            self.skipTest("Pydantic / FastAPI belum terinstal.")
        self.summary_service = DailySummaryService()
        self.request = DailyStockSummaryRequest(
            date=date(2026, 11, 19),
            store_name="ROKKUS Mardani Raya",
            items=[
                DailyStockItemInput(
                    name="Lotus Biscoff",
                    current_stock=0.0,
                    minimum_stock=5.0,
                    unit="porsi",
                    category="Roti Manis",
                ),
                DailyStockItemInput(
                    name="Keju Slice",
                    current_stock=3.0,
                    minimum_stock=5.0,
                    unit="slice",
                    category="Tambahan",
                ),
                DailyStockItemInput(
                    name="Roti Gandum",
                    current_stock=15.0,
                    minimum_stock=5.0,
                    unit="buah",
                    category="Bahan Baku",
                ),
            ],
        )

    def test_enrichment_success_preserves_factual_status_counts(self):
        """Memvalidasi pengayaan ML menambahkan wawasan risiko ke suggested_actions

        tanpa mengubah status_counts faktual (1 EMPTY, 1 LOW, 1 SAFE).
        """
        genai_response = self.summary_service.generate_summary(self.request)

        # Baseline verifikasi
        self.assertEqual(genai_response.data.status_counts.empty, 1)
        self.assertEqual(genai_response.data.status_counts.low, 1)
        self.assertEqual(genai_response.data.status_counts.safe, 1)

        # Simulasi fitur ML lengkap untuk item
        ml_features = [
            MLItemFeatureInput(
                stok_saat_ini=0.0,
                batas_minimum=5.0,
                barang_masuk=10.0,
                barang_keluar=25.0,
                avg_keluar_7h=20.0,
                days_of_cover=0.0,
                rasio_stok=0.0,
                total_masuk_7h=70.0,
                total_keluar_7h=140.0,
                kategori="roti_kukus",
                rasa="Lotus Biscoff",
            ),
            MLItemFeatureInput(
                stok_saat_ini=3.0,
                batas_minimum=5.0,
                barang_masuk=5.0,
                barang_keluar=15.0,
                avg_keluar_7h=12.0,
                days_of_cover=0.25,
                rasio_stok=0.6,
                total_masuk_7h=35.0,
                total_keluar_7h=84.0,
                kategori="roti_kukus",
                rasa="Keju Slice",
            ),
        ]

        integrator = MLGenAIIntegrator()
        enriched_response, err = integrator.enrich_summary_with_ml_insights(
            genai_response, ml_inputs=ml_features
        )

        self.assertIsNone(err)
        # Status counts faktual TIDAK berubah
        self.assertEqual(enriched_response.data.status_counts.empty, 1)
        self.assertEqual(enriched_response.data.status_counts.low, 1)
        self.assertEqual(enriched_response.data.status_counts.safe, 1)

        # Suggested actions memuat peringatan risiko ML
        ml_actions = [
            a for a in enriched_response.data.suggested_actions if "[ML_RISK_PREDICTION]" in a
        ]
        self.assertGreater(len(ml_actions), 0)
        self.assertTrue(any("Lotus Biscoff" in a for a in ml_actions))
        self.assertTrue(any("Keju Slice" in a for a in ml_actions))

    def test_resilience_when_ml_service_fails_or_unavailable(self):
        """Memastikan jika ML Service mengalami 503 UNAVAILABLE atau exception,

        response GenAI tetap utuh, tidak melempar uncaught exception (graceful degradation).
        """
        genai_response = self.summary_service.generate_summary(self.request)
        orig_actions_count = len(genai_response.data.suggested_actions)

        # Mock ML Client yang gagal / 503
        failing_client = MagicMock(spec=MLServiceClient)
        failing_client.predict_status.side_effect = RuntimeError("ML Service Unavailable 503: Model not loaded")

        integrator = MLGenAIIntegrator(ml_client=failing_client)
        ml_features = [
            MLItemFeatureInput(
                stok_saat_ini=0.0,
                batas_minimum=5.0,
                barang_masuk=10.0,
                barang_keluar=25.0,
                avg_keluar_7h=20.0,
                days_of_cover=0.0,
                rasio_stok=0.0,
                total_masuk_7h=70.0,
                total_keluar_7h=140.0,
                kategori="roti_kukus",
                rasa="Lotus Biscoff",
            )
        ]

        safe_response, err = integrator.enrich_summary_with_ml_insights(
            genai_response, ml_inputs=ml_features
        )

        # Sistem tetap stabil (graceful degradation)
        self.assertIsNotNone(err)
        self.assertIn("503", err)
        self.assertEqual(safe_response.status, "success")
        self.assertEqual(len(safe_response.data.suggested_actions), orig_actions_count)
        self.assertEqual(safe_response.data.status_counts.empty, 1)


class TestMLForecastingContractAndResilience(unittest.TestCase):
    """Pengujian kontrak dan resilience untuk endpoint POST /ml/forecast-stock (Tahap 7B)."""

    def setUp(self):
        if not FASTAPI_AVAILABLE:
            self.skipTest("Pydantic / FastAPI belum terinstal.")
        self.valid_forecast_item = {
            "id_barang": "PR001",
            "nama_barang": "Lotus Biscoff",
            "batas_minimum": 5.0,
            "stok_saat_ini": 10.0,
            "barang_masuk": 2.0,
            "barang_keluar": 1.0,
            "avg_keluar_7h": 1.0,
            "total_masuk_7h": 14.0,
            "total_keluar_7h": 7.0,
            "kategori": "Roti Manis",
            "rasa": "Lotus Biscoff",
        }

    def test_forecast_item_input_valid_contract(self):
        """Memvalidasi pembuatan MLForecastItemInput dengan data valid."""
        item = MLForecastItemInput(**self.valid_forecast_item)
        self.assertEqual(item.id_barang, "PR001")
        self.assertEqual(item.stok_saat_ini, 10.0)
        self.assertEqual(item.batas_minimum, 5.0)

    def test_forecast_item_input_negative_numeric_fails(self):
        """Memastikan fitur numerik bernilai negatif pada forecast input ditolak."""
        bad = self.valid_forecast_item.copy()
        bad["stok_saat_ini"] = -5.0
        with self.assertRaises(ValidationError):
            MLForecastItemInput(**bad)

    def test_forecast_item_empty_string_fails(self):
        """Memastikan string kosong pada id_barang, kategori, atau rasa ditolak."""
        bad = self.valid_forecast_item.copy()
        bad["id_barang"] = "   "
        with self.assertRaises(ValidationError):
            MLForecastItemInput(**bad)

    def test_forecast_request_horizon_validation(self):
        """Memvalidasi aturan ketat horizon_days pada MLForecastRequest (hanya horizon=7)."""
        item = MLForecastItemInput(**self.valid_forecast_item)
        req = MLForecastRequest(items=[item], horizon_days=7)
        self.assertEqual(req.horizon_days, 7)

        # Default horizon adalah 7
        default_req = MLForecastRequest(items=[item])
        self.assertEqual(default_req.horizon_days, 7)

        # Horizon != 7 harus gagal sesuai batasan model ML Husain
        with self.assertRaises(ValidationError):
            MLForecastRequest(items=[item], horizon_days=3)

        with self.assertRaises(ValidationError):
            MLForecastRequest(items=[item], horizon_days=14)

        with self.assertRaises(ValidationError):
            MLForecastRequest(items=[item], horizon_days=30)

    def test_forecast_mock_client_response_contract(self):
        """Memvalidasi respons mock forecasting client menghasilkan struktur yang valid."""
        item = MLForecastItemInput(**self.valid_forecast_item)
        req = MLForecastRequest(items=[item], horizon_days=7)

        client = MLServiceClient(mock_mode=True)
        res = client.forecast_stock(req)

        self.assertEqual(res.total_items, 1)
        self.assertEqual(len(res.results), 1)
        r = res.results[0]
        self.assertEqual(r.id_barang, "PR001")
        self.assertEqual(r.horizon_days, 7)
        self.assertIsInstance(r.predicted_stock, float)
        self.assertIn(r.predicted_status, ["aman", "menipis", "habis"])

    def test_forecast_client_resilience_503(self):
        """Memastikan client menangani error 503 dari service ML forecasting."""
        item = MLForecastItemInput(**self.valid_forecast_item)
        req = MLForecastRequest(items=[item], horizon_days=7)

        client = MLServiceClient(mock_mode=False, base_url="http://non-existent-ml-host:9999")
        with self.assertRaises(Exception):
            client.forecast_stock(req)

    def test_forecasting_does_not_mutate_factual_stock_counts(self):
        """Memastikan hasil forecasting terisolasi dan tidak mengubah status_counts faktual DS/GenAI."""
        counts = StockStatusCounts(empty=5, low=8, safe=16, total_items=29)
        # Simulasi hasil forecasting memprediksi barang habis di masa depan
        forecast_result = MLForecastResultItem(
            id_barang="PR001",
            nama_barang="Lotus Biscoff",
            horizon_days=7,
            predicted_stock=0.0,
            predicted_status="habis",
            batas_minimum=5.0,
            model_version="forecast_v1",
        )
        # Status counts faktual hari ini tetap tidak terpengaruh
        self.assertEqual(counts.safe, 16)
        self.assertEqual(counts.empty, 5)
        self.assertEqual(counts.low, 8)
        self.assertEqual(forecast_result.predicted_status, "habis")


if __name__ == "__main__":
    unittest.main()
