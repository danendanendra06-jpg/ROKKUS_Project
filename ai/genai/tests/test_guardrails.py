"""Unit test untuk SummaryOutputGuardrail."""

import json
import sys
from pathlib import Path
import unittest

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.core.guardrails import (
    ActionType,
    LLMSummaryOutput,
    StructuredActionItem,
    SummaryOutputGuardrail,
)
from src.core.rules import StockStatus
from src.schemas.summary import ProcessedStockItem


class TestSummaryOutputGuardrail(unittest.TestCase):
    """Pengujian verifikasi guardrail terhadap berbagai variasi output model."""

    def setUp(self):
        self.guardrail = SummaryOutputGuardrail()
        self.valid_items = {
            "BB-001": ProcessedStockItem(
                id="BB-001",
                item_ref="BB-001",
                name="Tepung Terigu",
                category="bahan_baku",
                current_stock=4.0,
                minimum_stock=10.0,
                unit="kg",
                status=StockStatus.LOW,
                status_description="Stok menipis.",
            ),
            "BB-002": ProcessedStockItem(
                id="BB-002",
                item_ref="BB-002",
                name="Gula Pasir",
                category="bahan_baku",
                current_stock=25.0,
                minimum_stock=10.0,
                unit="kg",
                status=StockStatus.SAFE,
                status_description="Stok aman.",
            ),
        }

    def test_valid_structured_output_passes(self):
        """Memastikan output yang mematuhi skema dan referensi lolos tanpa pelanggaran."""
        payload = {
            "narrative": "Kondisi stok harian terpantau aman, namun Tepung Terigu berada pada batas kritis.",
            "actions": [
                {
                    "action_type": ActionType.RESTOCK_REVIEW.value,
                    "target_item_ref": "BB-001",
                    "notes": "Lakukan restock untuk Tepung Terigu."
                },
                {
                    "action_type": ActionType.NO_ACTION.value,
                    "target_item_ref": "BB-002",
                    "notes": "Stok gula aman."
                }
            ],
            "data_limitations_note": "Data transaksi harian tidak disertakan."
        }
        res = self.guardrail.validate(payload, self.valid_items, self.valid_items)
        self.assertTrue(res.is_valid)
        self.assertEqual(len(res.violations), 0)
        self.assertIsNotNone(res.parsed_output)
        self.assertEqual(len(res.parsed_output.actions), 2)

    def test_malformed_json_fails(self):
        """Memastikan string non-JSON langsung ditolak."""
        bad_json = "Ini bukan JSON { 'key': 123 "
        res = self.guardrail.validate(bad_json, self.valid_items)
        self.assertFalse(res.is_valid)
        self.assertIn("bukan merupakan format JSON yang valid", res.violations[0])

    def test_schema_mismatch_fails(self):
        """Memastikan payload dengan skema yang tidak cocok ditolak."""
        bad_schema = {
            "judul": "Ringkasan",
            "actions": "Bukan list objek"
        }
        res = self.guardrail.validate(bad_schema, self.valid_items)
        self.assertFalse(res.is_valid)
        self.assertIn("Ketidaksesuaian skema output Pydantic", res.violations[0])

    def test_fictitious_product_reference_fails(self):
        """Memastikan tindakan yang mereferensikan produk fiktif/tidak dikenal ditolak."""
        payload = {
            "narrative": "Ringkasan kondisi inventaris.",
            "actions": [
                {
                    "action_type": ActionType.RESTOCK_REVIEW.value,
                    "target_item_ref": "PRODUK_GAIB_999",
                    "notes": "Restock produk fiktif"
                }
            ]
        }
        res = self.guardrail.validate(payload, self.valid_items)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("produk fiktif/tidak dikenal" in v for v in res.violations))

    def test_speculative_timeframe_fails(self):
        """Memastikan kalimat estimasi waktu habis ditolak."""
        payload = {
            "narrative": "Stok tepung terigu diperkirakan akan habis dalam 2 hari ke depan.",
            "actions": []
        }
        res = self.guardrail.validate(payload, self.valid_items)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("prediksi spekulatif" in v for v in res.violations))

    def test_unproven_financial_claim_fails(self):
        """Memastikan klaim nominal omzet/penjualan tanpa data pendukung ditolak."""
        payload = {
            "narrative": "Penjualan hari ini mencapai Rp 10.000.000 dengan omzet yang meningkat.",
            "actions": []
        }
        res = self.guardrail.validate(payload, self.valid_items)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("klaim data finansial/omzet" in v for v in res.violations))

    def test_benign_financial_disclaimer_passes(self):
        """Memastikan kalimat yang semata-mata menyatakan ketiadaan data finansial diizinkan (Requirement 5)."""
        payload = {
            "narrative": "Ringkasan stok harian terpantau baik. Perlu dicatat bahwa data penjualan dan omzet tidak tersedia dalam sistem ini.",
            "actions": []
        }
        res = self.guardrail.validate(payload, self.valid_items)
        self.assertTrue(res.is_valid)
        self.assertEqual(len(res.violations), 0)

    def test_inconsistent_action_for_safe_item_fails(self):
        """Memastikan item yang sudah dinilai SAFE tidak diberi tindakan RESTOCK_REVIEW tanpa alasan."""
        payload = {
            "narrative": "Stok terpantau baik.",
            "actions": [
                {
                    "action_type": ActionType.RESTOCK_REVIEW.value,
                    "target_item_ref": "BB-002",  # Gula Pasir berstatus SAFE
                    "notes": "Restock gula pasir."
                }
            ]
        }
        res = self.guardrail.validate(payload, self.valid_items, self.valid_items)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("berstatus SAFE tetapi diberi tindakan RESTOCK_REVIEW" in v for v in res.violations))


if __name__ == "__main__":
    unittest.main()
