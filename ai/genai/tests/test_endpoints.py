"""Pengujian integrasi endpoint HTTP API v1 menggunakan TestClient."""

import sys
from pathlib import Path
import unittest

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Coba import FastAPI TestClient
try:
    from fastapi.testclient import TestClient
    from src.main import app
    from src.core.config import settings
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


class TestAPIEndpoints(unittest.TestCase):
    """Pengujian integrasi endpoint REST API."""

    def setUp(self):
        if not FASTAPI_AVAILABLE:
            self.skipTest("FastAPI belum terinstal di environment saat ini.")
        self._orig_provider = settings.LLM_PROVIDER
        settings.LLM_PROVIDER = "mock"
        self.client = TestClient(app)

    def tearDown(self):
        if FASTAPI_AVAILABLE:
            settings.LLM_PROVIDER = self._orig_provider

    def test_root_endpoint(self):
        """Endpoint GET / harus mengembalikan status online dan active_provider mock."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["active_provider"], "mock")
        self.assertEqual(data["status"], "online")

    def test_health_endpoint(self):
        """Endpoint GET /api/v1/health harus mengembalikan status healthy dan provider mock."""
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["active_provider"], "mock")
        self.assertIn("gemini_configured", data)
        self.assertIsInstance(data["gemini_configured"], bool)
        self.assertGreater(data["inventory_items_loaded"], 0)

    def test_chat_endpoint_success(self):
        """Endpoint POST /api/v1/assistant/chat harus merespon dengan status success dan provider mock."""
        payload = {
            "message": "Bahan baku apa saja yang stoknya di bawah batas minimum?",
            "category_filter": "bahan_baku"
        }
        response = self.client.post("/api/v1/assistant/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["data"]["meta"]["provider"], "mock")
        self.assertIn("reply", data["data"])
        self.assertGreater(len(data["data"]["context_items"]), 0)

    def test_chat_endpoint_validation_error(self):
        """Payload tidak valid (pesan terlalu pendek) harus mengembalikan HTTP 422."""
        payload = {"message": "a"}  # Kurang dari panjang minimum (2 karakter)
        response = self.client.post("/api/v1/assistant/chat", json=payload)
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()

