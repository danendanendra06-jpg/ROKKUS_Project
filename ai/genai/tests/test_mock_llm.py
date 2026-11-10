"""Pengujian MockLLMService dan verifikasi provider mock."""

import asyncio
import sys
from pathlib import Path
import unittest

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.repositories.mock_inventory import MockInventoryRepository
from src.services.mock_llm import MockLLMService
from src.services.assistant_service import AssistantService
from src.schemas.chat import ChatRequest


class TestMockLLMService(unittest.TestCase):
    """Pengujian logika mock response dan identitas provider."""

    def setUp(self):
        data_path = BASE_DIR / "data" / "synthetic_inventory.json"
        self.repo = MockInventoryRepository(file_path=data_path)
        self.llm = MockLLMService()
        self.service = AssistantService(self.repo, self.llm)

    def test_provider_identity_is_strictly_mock(self):
        """Memastikan nama provider SELALU 'mock' dan BUKAN 'gemini'."""
        self.assertEqual(self.llm.provider_name, "mock")
        self.assertNotEqual(self.llm.provider_name, "gemini")

    def test_generate_critical_stock_response(self):
        """Memvalidasi respons pertanyaan stok kritis/menipis."""
        request = ChatRequest(message="Barang apa yang stoknya kritis hari ini?")
        response = asyncio.run(self.service.handle_chat(request))

        self.assertEqual(response.status, "success")
        self.assertEqual(response.data.meta.provider, "mock")
        self.assertIn("CRITICAL", response.data.reply)
        self.assertGreater(len(response.data.context_items), 0)
        self.assertGreater(len(response.data.suggested_actions), 0)

    def test_generate_summary_response(self):
        """Memvalidasi respons permintaan ringkasan status inventaris."""
        request = ChatRequest(message="Berikan ringkasan stok harian")
        response = asyncio.run(self.service.handle_chat(request))

        self.assertEqual(response.status, "success")
        self.assertEqual(response.data.meta.provider, "mock")
        self.assertIn("Ringkasan", response.data.reply)
        self.assertGreater(len(response.data.context_items), 0)

    def test_category_filter_applied(self):
        """Memvalidasi pemfilteran kategori kemasan pada asisten."""
        request = ChatRequest(
            message="Bagaimana stok kemasan saat ini?",
            category_filter="kemasan",
        )
        response = asyncio.run(self.service.handle_chat(request))

        self.assertEqual(response.status, "success")
        for item in response.data.context_items:
            self.assertEqual(item.category, "kemasan")


if __name__ == "__main__":
    unittest.main()

