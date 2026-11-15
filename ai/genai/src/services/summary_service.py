"""Layanan bisnis untuk menghasilkan Daily Stock Summary menggunakan Mock Engine."""

from datetime import datetime, timezone
from typing import List

from ..core.rules import (
    StockStatus,
    evaluate_stock_status,
    STOCK_STATUS_DESCRIPTIONS,
)
from ..schemas.summary import (
    DailyStockSummaryRequest,
    DailyStockSummaryResponse,
    DailySummaryData,
    DailySummaryMeta,
    ProcessedStockItem,
    StockStatusCounts,
)


class DailySummaryService:
    """Service untuk menganalisis data stok harian dan menyusun ringkasan naratif.

    Menggunakan klasifikasi konsisten dari core.rules dan menghasilkan ringkasan
    bahasa Indonesia yang terstruktur tanpa prediksi waktu spekulatif.
    """

    def generate_summary(
        self,
        request: DailyStockSummaryRequest,
        provider: str = "mock",
        is_synthetic: bool = True,
        source: str = "synthetic_input",
    ) -> DailyStockSummaryResponse:
        """Memproses request data stok harian dan mengembalikan response lengkap."""
        processed_items: List[ProcessedStockItem] = []
        critical_items: List[ProcessedStockItem] = []
        warning_items: List[ProcessedStockItem] = []
        safe_items: List[ProcessedStockItem] = []

        # 1. Evaluasi status setiap item
        for item in request.items:
            status = evaluate_stock_status(item.current_stock, item.minimum_stock)
            desc = STOCK_STATUS_DESCRIPTIONS.get(status, "")

            processed = ProcessedStockItem(
                id=item.id,
                name=item.name,
                category=item.category,
                current_stock=item.current_stock,
                minimum_stock=item.minimum_stock,
                unit=item.unit,
                status=status,
                status_description=desc,
            )
            processed_items.append(processed)

            if status == StockStatus.CRITICAL:
                critical_items.append(processed)
            elif status == StockStatus.WARNING:
                warning_items.append(processed)
            else:
                safe_items.append(processed)

        total_items = len(processed_items)
        counts = StockStatusCounts(
            critical=len(critical_items),
            warning=len(warning_items),
            safe=len(safe_items),
            total_items=total_items,
        )

        # 2. Susun narasi ringkasan stok harian (Bahasa Indonesia)
        summary_text = self._build_summary_narrative(
            date_str=request.date.isoformat(),
            store_name=request.store_name or "UMKM ROKKUS Mardani Raya",
            counts=counts,
            critical_items=critical_items,
            warning_items=warning_items,
            safe_items=safe_items,
        )

        # 3. Susun daftar tindakan yang disarankan (tanpa prediksi spekulatif)
        suggested_actions = self._build_suggested_actions(
            critical_items=critical_items,
            warning_items=warning_items,
            safe_items=safe_items,
        )

        # 4. Susun metadata
        now_iso = datetime.now(timezone.utc).isoformat()
        meta = DailySummaryMeta(
            provider=provider,
            is_synthetic=is_synthetic,
            source=source,
            generated_at=now_iso,
        )

        data = DailySummaryData(
            date=request.date.isoformat(),
            store_name=request.store_name or "UMKM ROKKUS Mardani Raya",
            summary=summary_text,
            status_counts=counts,
            items=processed_items,
            suggested_actions=suggested_actions,
            meta=meta,
        )

        return DailyStockSummaryResponse(
            status="success",
            data=data,
        )

    def _build_summary_narrative(
        self,
        date_str: str,
        store_name: str,
        counts: StockStatusCounts,
        critical_items: List[ProcessedStockItem],
        warning_items: List[ProcessedStockItem],
        safe_items: List[ProcessedStockItem],
    ) -> str:
        """Menyusun teks narasi ringkasan berbasis data faktual tanpa estimasi spekulatif."""
        parts: List[str] = []

        parts.append(
            f"Ringkasan Stok Harian ({date_str}) untuk {store_name}: "
            f"Dari total {counts.total_items} barang yang dipantau, tercatat "
            f"{counts.critical} barang berstatus CRITICAL, "
            f"{counts.warning} barang berstatus WARNING, dan "
            f"{counts.safe} barang berstatus SAFE."
        )

        if critical_items:
            crit_details = "; ".join(
                f"{item.name} (sisa {item.current_stock} {item.unit}, min: {item.minimum_stock} {item.unit})"
                for item in critical_items
            )
            parts.append(
                f"Perhatian mendesak diperlukan pada item berstatus kritis: {crit_details}. "
                f"Barang-barang ini berada pada atau di bawah batas minimum dan membutuhkan pengadaan ulang segera."
            )

        if warning_items:
            warn_details = "; ".join(
                f"{item.name} (sisa {item.current_stock} {item.unit}, min: {item.minimum_stock} {item.unit})"
                for item in warning_items
            )
            parts.append(
                f"Item pada zona waspada yang perlu dipantau ketat: {warn_details}."
            )

        if safe_items and not critical_items and not warning_items:
            parts.append(
                "Seluruh stok barang saat ini berada dalam kondisi aman melampaui 150% ambang batas minimum "
                "untuk mendukung operasional."
            )
        elif safe_items:
            parts.append(
                f"Sebanyak {counts.safe} barang lainnya berada dalam kondisi stok aman untuk operasional."
            )

        return " ".join(parts)

    def _build_suggested_actions(
        self,
        critical_items: List[ProcessedStockItem],
        warning_items: List[ProcessedStockItem],
        safe_items: List[ProcessedStockItem],
    ) -> List[str]:
        """Menyusun rekomendasi aksi operasional berdasarkan klasifikasi status."""
        actions: List[str] = []

        if critical_items:
            names = ", ".join(i.name for i in critical_items)
            actions.append(f"Lakukan pemesanan ulang (restock) darurat hari ini untuk: {names}.")

        if warning_items:
            names = ", ".join(i.name for i in warning_items)
            actions.append(f"Lakukan pengecekan fisik dan koordinasi jadwal pengadaan untuk item waspada: {names}.")

        if safe_items:
            actions.append("Pertahankan rotasi barang menggunakan metode FIFO (First In First Out).")

        if not critical_items and not warning_items:
            actions.append("Lanjutkan pencatatan mutasi stok harian secara berkala.")

        return actions

