"""Unit test dan integration test untuk GeminiSummaryLLMService (Mocked, tanpa real API call)."""

import asyncio
from datetime import date
import json
import sys
from pathlib import Path
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.core.config import settings
from src.core.rules import StockStatus
from src.schemas.summary import DailyStockItemInput, DailyStockSummaryRequest
from src.services.gemini_summary_llm import GeminiSummaryLLMService
from src.services.summary_service import DailySummaryService
from src.services.summary_llm import MockSummaryLLMService
from src.api.v1.endpoints.summary import get_summary_service


class TestGeminiIntegration(unittest.TestCase):
    """Pengujian adapter Gemini Gen AI SDK dengan mock client."""

    def setUp(self):
        self.request = DailyStockSummaryRequest(
            date=date(2026, 11, 18),
            store_name="ROKKUS Mardani Raya",
            items=[
                DailyStockItemInput(
                    id="BB-001",
                    name="Tepung Terigu",
                    current_stock=4.0,
                    minimum_stock=10.0,
                    unit="kg",
                    category="bahan_baku",
                ),
                DailyStockItemInput(
                    id="PJ-001",
                    name="Roti Kukus Pandan",
                    current_stock=20.0,
                    minimum_stock=10.0,
                    unit="porsi",
                    category="produk_jadi",
                ),
            ],
        )

    def test_gemini_init_without_key_raises_error(self):
        """Memastikan inisialisasi tanpa API Key menghasilkan ValueError yang jelas."""
        with patch.object(settings, "GEMINI_API_KEY", None):
            with self.assertRaises(ValueError) as ctx:
                GeminiSummaryLLMService(api_key=None, client=None)
            self.assertIn("GEMINI_API_KEY wajib dikonfigurasi", str(ctx.exception))

    def test_gemini_model_name_configurable(self):
        """Memastikan nama model Gemini dapat dikonfigurasi secara dinamis."""
        mock_client = MagicMock()
        service = GeminiSummaryLLMService(
            api_key="test-key",
            model_name="gemini-2.0-flash",
            client=mock_client,
        )
        self.assertEqual(service.provider_name, "gemini-2.0-flash")

    def test_gemini_init_configures_http_options_and_retry(self):
        """Memastikan inisialisasi default mengonfigurasi HttpOptions (timeout_ms) dan retry_options (attempts=1)."""
        with patch("src.services.gemini_summary_llm.genai.Client") as mock_client_cls:
            GeminiSummaryLLMService(
                api_key="test-key",
                timeout_seconds=8.0,
            )
            mock_client_cls.assert_called_once()
            call_kwargs = mock_client_cls.call_args.kwargs
            self.assertEqual(call_kwargs.get("api_key"), "test-key")
            http_opts = call_kwargs.get("http_options")
            self.assertIsNotNone(http_opts)
            self.assertEqual(http_opts.timeout, 8000)
            self.assertIsNotNone(http_opts.retry_options)
            self.assertEqual(http_opts.retry_options.attempts, 1)

    def test_gemini_async_success_call_with_mock_client(self):
        """Memastikan pemanggilan asinkron yang berhasil lolos guardrail dan metadata akurat."""
        valid_gemini_json = json.dumps({
            "narrative": "Ringkasan stok harian: Tepung Terigu berada dalam kondisi kritis, sedangkan Roti Kukus Pandan aman.",
            "actions": [
                {
                    "action_type": "RESTOCK_REVIEW",
                    "target_item_ref": "BB-001",
                    "notes": "Lakukan restock darurat untuk Tepung Terigu."
                },
                {
                    "action_type": "NO_ACTION",
                    "target_item_ref": "PJ-001",
                    "notes": "Stok produk jadi aman."
                }
            ],
            "data_limitations_note": "Data penjualan tidak disertakan."
        })

        mock_response = MagicMock()
        mock_response.text = valid_gemini_json

        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        gemini_service = GeminiSummaryLLMService(
            api_key="test-api-key",
            model_name="gemini-2.5-flash",
            client=mock_client,
        )
        daily_service = DailySummaryService(llm_service=gemini_service)

        response = daily_service.generate_summary(self.request)

        # Verifikasi keberhasilan
        self.assertEqual(response.status, "success")
        self.assertEqual(response.data.meta.provider, "gemini-2.5-flash")
        self.assertFalse(response.data.meta.fallback_applied)
        self.assertEqual(response.data.meta.guardrail_status, "passed")

        # Verifikasi data terstruktur
        self.assertIn("Tepung Terigu", response.data.summary)
        self.assertEqual(len(response.data.suggested_actions), 2)
        self.assertIn("[RESTOCK_REVIEW]", response.data.suggested_actions[0])

    def test_gemini_timeout_triggers_deterministic_fallback(self):
        """Memastikan jika panggilan Gemini API mengalami timeout, sistem beralih ke fallback deterministik."""
        async def slow_generate(*args, **kwargs):
            await asyncio.sleep(0.3)
            return MagicMock(text="{}")

        mock_client = MagicMock()
        mock_client.aio.models.generate_content = slow_generate

        gemini_service = GeminiSummaryLLMService(
            api_key="test-key",
            model_name="gemini-2.5-flash",
            timeout_seconds=0.05,  # Timeout sangat singkat
            client=mock_client,
        )
        daily_service = DailySummaryService(llm_service=gemini_service)

        response = daily_service.generate_summary(self.request)

        self.assertEqual(response.status, "success")
        self.assertTrue(response.data.meta.fallback_applied)
        self.assertEqual(response.data.meta.requested_provider, "gemini-2.5-flash")
        self.assertEqual(response.data.meta.execution_provider, "deterministic_fallback")
        self.assertEqual(response.data.meta.provider, "deterministic_fallback")
        self.assertIn("Fallback Deterministik", response.data.meta.disclaimer)
        self.assertIn("timeout", response.data.meta.guardrail_status.lower())
        self.assertIn("Ringkasan Stok Harian (2026-11-18)", response.data.summary)

    def test_gemini_api_error_triggers_deterministic_fallback(self):
        """Memastikan error API (misal 429 quota exceeded) otomatis memicu fallback deterministik."""
        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(
            side_effect=RuntimeError("Google API Error 429: ResourceExhausted quota exceeded")
        )

        gemini_service = GeminiSummaryLLMService(
            api_key="test-key",
            model_name="gemini-2.5-flash",
            client=mock_client,
        )
        daily_service = DailySummaryService(llm_service=gemini_service)

        response = daily_service.generate_summary(self.request)

        self.assertEqual(response.status, "success")
        self.assertTrue(response.data.meta.fallback_applied)
        self.assertEqual(response.data.meta.requested_provider, "gemini-2.5-flash")
        self.assertEqual(response.data.meta.execution_provider, "deterministic_fallback")
        self.assertEqual(response.data.meta.provider, "deterministic_fallback")
        self.assertIn("Fallback Deterministik", response.data.meta.disclaimer)
        self.assertIn("ResourceExhausted", response.data.meta.guardrail_status)
        self.assertIn("Ringkasan Stok Harian", response.data.summary)

    def test_gemini_503_unavailable_triggers_deterministic_fallback(self):
        """Memastikan error 503 UNAVAILABLE (model overloaded) beralih ke fallback deterministik."""
        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(
            side_effect=RuntimeError("Google API Error 503: The model is overloaded. Please try again later.")
        )

        gemini_service = GeminiSummaryLLMService(
            api_key="test-key",
            model_name="gemini-2.5-flash",
            client=mock_client,
        )
        daily_service = DailySummaryService(llm_service=gemini_service)

        response = daily_service.generate_summary(self.request)

        self.assertEqual(response.status, "success")
        self.assertTrue(response.data.meta.fallback_applied)
        self.assertEqual(response.data.meta.requested_provider, "gemini-2.5-flash")
        self.assertEqual(response.data.meta.execution_provider, "deterministic_fallback")
        self.assertEqual(response.data.meta.provider, "deterministic_fallback")
        self.assertIn("Fallback Deterministik", response.data.meta.disclaimer)
        self.assertIn("503", response.data.meta.guardrail_status)
        self.assertIn("Ringkasan Stok Harian", response.data.summary)

    def test_gemini_hallucination_triggers_guardrail_fallback(self):
        """Memastikan jika respon Gemini menghasilkan produk fiktif, guardrail menolak dan memicu fallback."""
        hallucinated_json = json.dumps({
            "narrative": "Kondisi stok harian.",
            "actions": [
                {
                    "action_type": "RESTOCK_REVIEW",
                    "target_item_ref": "PRODUK_GAIB_999",  # Fiktif!
                    "notes": "Restock produk fiktif"
                }
            ],
            "data_limitations_note": None
        })

        mock_response = MagicMock()
        mock_response.text = hallucinated_json

        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        gemini_service = GeminiSummaryLLMService(
            api_key="test-key",
            model_name="gemini-2.5-flash",
            client=mock_client,
        )
        daily_service = DailySummaryService(llm_service=gemini_service)

        response = daily_service.generate_summary(self.request)

        self.assertEqual(response.status, "success")
        self.assertTrue(response.data.meta.fallback_applied)
        self.assertIn("produk fiktif/tidak dikenal", response.data.meta.guardrail_status)
        self.assertIn("Ringkasan Stok Harian", response.data.summary)

    def test_factory_returns_mock_when_provider_is_mock(self):
        """Memastikan factory get_summary_service mengembalikan MockSummaryLLMService saat LLM_PROVIDER=mock."""
        with patch.object(settings, "LLM_PROVIDER", "mock"):
            service = get_summary_service()
            self.assertIsInstance(service.llm_service, MockSummaryLLMService)

    def test_factory_returns_mock_when_gemini_key_missing(self):
        """Memastikan factory get_summary_service mengembalikan Mock saat LLM_PROVIDER=gemini tapi API key kosong."""
        with patch.object(settings, "LLM_PROVIDER", "gemini"):
            with patch.object(settings, "GEMINI_API_KEY", None):
                service = get_summary_service()
                self.assertIsInstance(service.llm_service, MockSummaryLLMService)

    def test_factory_returns_gemini_when_key_present(self):
        """Memastikan factory get_summary_service mengembalikan GeminiSummaryLLMService saat key tersedia."""
        with patch.object(settings, "LLM_PROVIDER", "gemini"):
            with patch.object(settings, "GEMINI_API_KEY", "dummy-api-key"):
                with patch("src.api.v1.endpoints.summary.GeminiSummaryLLMService") as mock_gemini_cls:
                    mock_instance = MagicMock()
                    mock_gemini_cls.return_value = mock_instance
                    service = get_summary_service()
                    self.assertEqual(service.llm_service, mock_instance)


if __name__ == "__main__":
    unittest.main()
