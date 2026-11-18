"""Layanan Mock LLM terstruktur untuk Tahap 3 (Prompt Engineering & Guardrails)."""

from abc import ABC, abstractmethod
import json
from typing import Any, Dict, List, Optional
from ..core.guardrails import ActionType, LLMSummaryOutput, StructuredActionItem


class BaseSummaryLLMService(ABC):
    """Kontrak dasar layanan LLM untuk pembuatan Daily Stock Summary."""

    @abstractmethod
    async def generate_summary_json(
        self,
        system_prompt: str,
        user_prompt: str,
        valid_item_refs: Dict[str, Any],
        context: Dict[str, Any],
    ) -> str:
        """Menghasilkan respon teks JSON terstruktur dari prompt."""
        pass


class MockSummaryLLMService(BaseSummaryLLMService):
    """Implementasi Mock LLM yang menghasilkan output terstruktur JSON valid.

    Dapat dikonfigurasi dengan mode khusus untuk keperluan pengujian guardrail & fallback.
    """

    MODE_NORMAL = "NORMAL"
    MODE_MALFORMED_JSON = "MALFORMED_JSON"
    MODE_INVALID_SCHEMA = "INVALID_SCHEMA"
    MODE_FICTITIOUS_ITEM = "FICTITIOUS_ITEM"
    MODE_SPECULATIVE_TIMEFRAME = "SPECULATIVE_TIMEFRAME"
    MODE_UNPROVEN_FINANCIAL_CLAIM = "UNPROVEN_FINANCIAL_CLAIM"
    MODE_TIMEOUT_ERROR = "TIMEOUT_ERROR"

    def __init__(self, mode: str = MODE_NORMAL, custom_response: Optional[str] = None):
        self.mode = mode
        self.custom_response = custom_response

    async def generate_summary_json(
        self,
        system_prompt: str,
        user_prompt: str,
        valid_item_refs: Dict[str, Any],
        context: Dict[str, Any],
    ) -> str:
        """Menghasilkan respon JSON terstruktur sesuai mode simulasi."""
        if self.custom_response is not None:
            return self.custom_response

        if self.mode == self.MODE_TIMEOUT_ERROR:
            raise TimeoutError("Simulasi timeout penyedia LLM (Mock Timeout).")

        if self.mode == self.MODE_MALFORMED_JSON:
            return "INI_BUKAN_JSON_VALID{broken_syntax: [123"

        if self.mode == self.MODE_INVALID_SCHEMA:
            return json.dumps({
                "teks_salah": "Field 'narrative' tidak ada dalam payload ini",
                "actions": "Bukan array"
            })

        if self.mode == self.MODE_FICTITIOUS_ITEM:
            return json.dumps({
                "narrative": "Ringkasan stok harian terpantau normal.",
                "actions": [
                    {
                        "action_type": ActionType.RESTOCK_REVIEW.value,
                        "target_item_ref": "PRODUK_FIKTIF_TIDAK_ADA",
                        "notes": "Barang fiktif yang tidak ada dalam request"
                    }
                ],
                "data_limitations_note": "Data transaksi tidak disertakan."
            })

        if self.mode == self.MODE_SPECULATIVE_TIMEFRAME:
            return json.dumps({
                "narrative": "Stok bahan baku diperkirakan akan habis dalam 2 hari ke depan jika produksi meningkat.",
                "actions": [],
                "data_limitations_note": None
            })

        if self.mode == self.MODE_UNPROVEN_FINANCIAL_CLAIM:
            return json.dumps({
                "narrative": "Kondisi stok terpantau stabil dengan estimasi omzet penjualan mencapai Rp 25.000.000 hari ini.",
                "actions": [],
                "data_limitations_note": None
            })

        # MODE_NORMAL: Menghasilkan output terstruktur yang mematuhi guardrail dan skema Pydantic
        date_str = context.get("date", "")
        store_name = context.get("store_name", "UMKM ROKKUS Mardani Raya")
        counts = context.get("status_counts", {})
        items = context.get("items", [])

        critical_items = [i for i in items if getattr(i, "status", None) == "CRITICAL"]
        warning_items = [i for i in items if getattr(i, "status", None) == "WARNING"]
        safe_items = [i for i in items if getattr(i, "status", None) == "SAFE"]

        narrative_parts = [
            f"Ringkasan Stok Harian ({date_str}) untuk {store_name}: "
            f"Dari total {len(items)} barang yang dipantau, tercatat {len(critical_items)} berstatus CRITICAL, "
            f"{len(warning_items)} berstatus WARNING, dan {len(safe_items)} berstatus SAFE."
        ]

        if critical_items:
            crit_names = ", ".join(f"{i.name} (sisa {i.current_stock} {i.unit})" for i in critical_items)
            narrative_parts.append(f"Perhatian mendesak diperlukan pada item berstatus kritis: {crit_names}.")

        if warning_items:
            warn_names = ", ".join(f"{i.name} (sisa {i.current_stock} {i.unit})" for i in warning_items)
            narrative_parts.append(f"Item zona waspada yang memerlukan pemantauan ketat: {warn_names}.")

        if safe_items and not critical_items and not warning_items:
            narrative_parts.append("Seluruh persediaan stok berada dalam ambang batas aman untuk operasional harian.")
        elif safe_items:
            narrative_parts.append(f"Sebanyak {len(safe_items)} barang lainnya berada dalam kondisi stok aman.")

        narrative_text = " ".join(narrative_parts)

        # Susun tindakan terstruktur dengan identifier sah
        actions_list: List[Dict[str, Any]] = []
        for crit in critical_items:
            ref = getattr(crit, "item_ref", None) or getattr(crit, "id", None) or "ITEM"
            actions_list.append({
                "action_type": ActionType.RESTOCK_REVIEW.value,
                "target_item_ref": ref,
                "notes": f"Lakukan restock darurat untuk {crit.name} karena stok berada pada atau di bawah batas minimum."
            })

        for warn in warning_items:
            ref = getattr(warn, "item_ref", None) or getattr(warn, "id", None) or "ITEM"
            actions_list.append({
                "action_type": ActionType.MONITOR.value,
                "target_item_ref": ref,
                "notes": f"Pantau pengeluaran dan siapkan pengadaan berkala untuk {warn.name}."
            })

        for safe in safe_items:
            ref = getattr(safe, "item_ref", None) or getattr(safe, "id", None) or "ITEM"
            actions_list.append({
                "action_type": ActionType.NO_ACTION.value,
                "target_item_ref": ref,
                "notes": f"Stok {safe.name} aman. Pertahankan rotasi penyimpanan normal."
            })

        output_data = {
            "narrative": narrative_text,
            "actions": actions_list,
            "data_limitations_note": "Data transaksi penjualan, omzet harian, dan mutasi finansial tidak disertakan dalam laporan stok ini."
        }

        return json.dumps(output_data, ensure_ascii=False)
