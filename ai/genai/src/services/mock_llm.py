"""Implementasi MockLLMService berbasis aturan dan data untuk prototipe."""

from datetime import datetime, timezone
from typing import List, Optional

from .llm_base import BaseLLMService
from ..core.rules import StockStatus
from ..schemas.chat import AssistantMessage, AssistantMeta
from ..schemas.inventory import InventoryItem


class MockLLMService(BaseLLMService):
    """Layanan Mock AI yang menghasilkan respons terstruktur berbasis data.

    CATATAN PENTING:
    Layanan ini bukan Generative AI sungguhan, melainkan simulated mock service
    yang meniru kontrak respons AI Inventory Assistant menggunakan heuristik aturan
    dan data sintetis ilustratif. Provider SELALU bernilai 'mock'.
    """

    @property
    def provider_name(self) -> str:
        return "mock"

    async def generate_response(
        self,
        user_query: str,
        context_items: List[InventoryItem],
        store_name: str,
        category_hint: Optional[str] = None,
    ) -> AssistantMessage:
        """Menghasilkan jawaban terstruktur menggunakan pola heuristik."""
        query_lower = user_query.strip().lower()
        now_iso = datetime.now(timezone.utc).isoformat()

        # Identifikasi item berdasarkan status
        critical_items = [i for i in context_items if i.status == StockStatus.CRITICAL]
        warning_items = [i for i in context_items if i.status == StockStatus.WARNING]
        safe_items = [i for i in context_items if i.status == StockStatus.SAFE]

        # Penentuan intent & peracikan jawaban
        suggested_actions: List[str] = []
        relevant_context: List[InventoryItem] = []

        if any(w in query_lower for w in ["kritis", "menipis", "habis", "restock", "kurang", "minimum"]):
            # Skenario 1: Pertanyaan stok kritis / kebutuhan restock
            relevant_context = critical_items if critical_items else context_items[:3]
            if critical_items:
                items_summary = ", ".join(
                    f"{item.name} ({item.current_stock} {item.unit}, min: {item.minimum_stock} {item.unit})"
                    for item in critical_items
                )
                reply = (
                    f"Berdasarkan data stok ilustratif {store_name}, terdapat {len(critical_items)} barang "
                    f"yang berada dalam status CRITICAL (stok <= batas minimum): {items_summary}. "
                    f"Disarankan segera melakukan restock darurat agar operasional tidak terganggu."
                )
                suggested_actions = [
                    f"Buat purchase order untuk item: {', '.join(i.id for i in critical_items)}",
                    "Prioritaskan bahan baku yang dibutuhkan untuk batch produksi berikutnya",
                ]
            else:
                reply = (
                    f"Saat ini tidak ada item yang berada dalam status CRITICAL pada data ilustratif {store_name}. "
                    f"Seluruh stok masih berada di atas ambang minimum."
                )
                suggested_actions = ["Lanjutkan pemantauan rutin stok harian."]

        elif any(w in query_lower for w in ["waspada", "peringatan", "warning", "hampir"]):
            # Skenario 2: Pertanyaan stok waspada (warning)
            relevant_context = warning_items if warning_items else context_items[:3]
            if warning_items:
                items_summary = ", ".join(
                    f"{item.name} ({item.current_stock} {item.unit})"
                    for item in warning_items
                )
                reply = (
                    f"Terdapat {len(warning_items)} barang yang berstatus WARNING di {store_name}: {items_summary}. "
                    f"Barang-barang ini berada di rentang 100%-150% batas minimum dan berpotensi menjadi kritis "
                    f"dalam 1-2 hari ke depan jika terjadi peningkatan pesanan."
                )
                suggested_actions = [
                    "Hubungi supplier untuk konfirmasi jadwal pengiriman berkala.",
                    "Lakukan pengecekan fisik fisik barang di gudang penyimpanan.",
                ]
            else:
                reply = f"Tidak ada item berstatus WARNING dalam data inventaris yang diperiksa."
                suggested_actions = ["Kondisi stok relatif stabil."]

        elif any(w in query_lower for w in ["aman", "cukup", "banyak", "safe"]):
            # Skenario 3: Pertanyaan stok aman
            relevant_context = safe_items if safe_items else context_items[:3]
            reply = (
                f"Terdapat {len(safe_items)} item dengan status SAFE (stok > 150% batas minimum) di {store_name}. "
                f"Ketersediaan barang-barang tersebut sangat mencukupi untuk mendukung proses operasional harian."
            )
            suggested_actions = ["Pertahankan rotasi FIFO (First In First Out) agar barang tidak kedaluwarsa."]

        elif any(w in query_lower for w in ["ringkasan", "rekap", "laporan", "kondisi", "semua", "status"]):
            # Skenario 4: Ringkasan keseluruhan inventaris
            relevant_context = context_items
            reply = (
                f"Ringkasan stok inventaris ilustratif {store_name}: "
                f"Total {len(context_items)} item terpantau, dengan rincian: "
                f"{len(critical_items)} berstatus CRITICAL, "
                f"{len(warning_items)} berstatus WARNING, dan "
                f"{len(safe_items)} berstatus SAFE. "
                f"Perhatian utama saat ini tertuju pada item berstatus kritis untuk segera dipasok."
            )
            if critical_items:
                suggested_actions.append(f"Restock mendesak untuk {critical_items[0].name}.")
            suggested_actions.append("Lakukan rekonsiliasi data stok keluar batch harian.")

        else:
            # Skenario 5: Respons fallback umum berbasis konteks
            relevant_context = context_items[:4]
            sample_names = ", ".join(i.name for i in context_items[:3])
            reply = (
                f"Halo! Saya asisten inventaris AI (Mock Prototype) untuk {store_name}. "
                f"Saya memantau data stok Anda (misal: {sample_names}). "
                f"Anda dapat menanyakan barang yang kritis, meminta ringkasan stok, "
                f"atau menyaring berdasarkan kategori seperti bahan baku dan kemasan."
            )
            suggested_actions = [
                "Tanyakan: 'Bahan baku apa yang stoknya kritis?'",
                "Tanyakan: 'Berikan ringkasan stok harian'",
            ]

        meta = AssistantMeta(
            provider="mock",
            tokens_estimated=0,
            processed_at=now_iso,
            context_items_count=len(relevant_context),
        )

        return AssistantMessage(
            reply=reply,
            context_items=relevant_context,
            suggested_actions=suggested_actions,
            meta=meta,
        )

