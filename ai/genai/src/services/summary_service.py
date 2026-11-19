"""Layanan bisnis Daily Stock Summary dengan Prompt Engineering, Guardrails, dan Fallback."""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional

from ..core.guardrails import (
    ActionType,
    GuardrailValidationResult,
    LLMSummaryOutput,
    StructuredActionItem,
    SummaryOutputGuardrail,
)
from ..core.prompt_builder import SummaryPromptBuilder
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
from .summary_llm import BaseSummaryLLMService, MockSummaryLLMService

logger = logging.getLogger(__name__)


class DailySummaryService:
    """Service untuk menyusun ringkasan stok harian menggunakan pipeline aman:

    1. Deterministik Stock Evaluator (core.rules)
    2. PromptBuilder (Isolasi data mentah tidak tepercaya)
    3. LLM Service (Menghasilkan format terstruktur)
    4. Guardrails (Validasi anti-halusinasi entitas, klaim finansial, dan waktu spekulatif)
    5. Fallback Deterministik (Fail-safe jika AI gagal atau output melanggar guardrail)
    """

    def __init__(
        self,
        llm_service: Optional[BaseSummaryLLMService] = None,
        guardrail: Optional[SummaryOutputGuardrail] = None,
    ):
        self.llm_service = llm_service or MockSummaryLLMService()
        self.guardrail = guardrail or SummaryOutputGuardrail()

    def generate_summary(
        self,
        request: DailyStockSummaryRequest,
        provider: Optional[str] = None,
        is_synthetic: bool = True,
        source: str = "synthetic_input",
    ) -> DailyStockSummaryResponse:
        """Memproses request data stok harian dan mengembalikan response lengkap."""
        resolved_provider = provider or getattr(self.llm_service, "provider_name", "mock")
        # 1. EVALUASI DETERMINISTIK (core.rules)
        processed_items: List[ProcessedStockItem] = []
        empty_items: List[ProcessedStockItem] = []
        low_items: List[ProcessedStockItem] = []
        safe_items: List[ProcessedStockItem] = []
        valid_item_refs: Dict[str, ProcessedStockItem] = {}

        for idx, item in enumerate(request.items):
            status = evaluate_stock_status(item.current_stock, item.minimum_stock)
            desc = STOCK_STATUS_DESCRIPTIONS.get(status, "")
            ref = item.id if item.id else f"ITEM_{idx+1}"

            processed = ProcessedStockItem(
                id=item.id,
                item_ref=ref,
                name=item.name,
                category=item.category,
                current_stock=item.current_stock,
                minimum_stock=item.minimum_stock,
                unit=item.unit,
                status=status,
                status_description=desc,
            )
            processed_items.append(processed)
            valid_item_refs[ref] = processed

            if status == StockStatus.EMPTY:
                empty_items.append(processed)
            elif status == StockStatus.LOW:
                low_items.append(processed)
            else:
                safe_items.append(processed)

        # Hitung kuantitas status secara matematis dan deterministik
        total_items = len(processed_items)
        counts = StockStatusCounts(
            empty=len(empty_items),
            low=len(low_items),
            safe=len(safe_items),
            total_items=total_items,
        )

        date_str = request.date.isoformat()
        store_name = request.store_name or "UMKM ROKKUS Mardani Raya"

        # 2. PROMPT BUILDING
        system_prompt = SummaryPromptBuilder.build_system_prompt()
        user_prompt = SummaryPromptBuilder.build_user_prompt(
            date_str=date_str,
            store_name=store_name,
            processed_items=processed_items,
            status_counts=counts,
        )

        # Context untuk LLM Service
        context: Dict[str, Any] = {
            "date": date_str,
            "store_name": store_name,
            "status_counts": counts.model_dump(),
            "items": processed_items,
        }

        # 3 & 4. EKSEKUSI MODEL & GUARDRAIL VALIDATION
        fallback_applied = False
        guardrail_status = "passed"
        raw_llm_output: Optional[str] = None
        validation_result: Optional[GuardrailValidationResult] = None

        try:
            # Panggil LLM Service (sync wrapper)
            import asyncio
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    raw_llm_output = pool.submit(
                        asyncio.run,
                        self.llm_service.generate_summary_json(
                            system_prompt, user_prompt, valid_item_refs, context
                        )
                    ).result()
            else:
                raw_llm_output = asyncio.run(
                    self.llm_service.generate_summary_json(
                        system_prompt, user_prompt, valid_item_refs, context
                    )
                )

            # Validasi Guardrail
            validation_result = self.guardrail.validate(
                raw_output=raw_llm_output,
                valid_item_refs=valid_item_refs,
                processed_items_by_ref=valid_item_refs,
            )

        except Exception as e:
            logger.warning(f"Kegagalan eksekusi LLM Service: {str(e)}")
            fallback_applied = True
            guardrail_status = f"fallback_triggered (provider_error: {str(e)})"
            validation_result = GuardrailValidationResult(
                is_valid=False,
                violations=[f"Penyedia LLM mengalami error: {str(e)}"],
            )

        # 5. PEMILIHAN OUTPUT: AI RESMI VS DETERMINISTIC FALLBACK
        if validation_result and validation_result.is_valid and validation_result.parsed_output:
            # Model sukses dan lolos guardrail
            parsed: LLMSummaryOutput = validation_result.parsed_output
            summary_text = parsed.narrative

            # Konversi structured actions ke list of string (kompatibilitas 100%)
            suggested_actions = self._format_structured_actions(parsed.actions, valid_item_refs)
            fallback_applied = False
            guardrail_status = "passed"
        else:
            # Terjadi pelanggaran guardrail atau error -> FALLBACK KE GENERATOR DETERMINISTIK
            fallback_applied = True
            if not guardrail_status.startswith("fallback_triggered"):
                violations_detail = "; ".join(validation_result.violations) if validation_result else "Unknown validation failure"
                guardrail_status = f"fallback_triggered: {violations_detail}"
            logger.info(f"Mengaktifkan fallback deterministik. Status: {guardrail_status}")

            summary_text = self._build_deterministic_narrative(
                date_str=date_str,
                store_name=store_name,
                counts=counts,
                empty_items=empty_items,
                low_items=low_items,
                safe_items=safe_items,
            )
            suggested_actions = self._build_deterministic_actions(
                empty_items=empty_items,
                low_items=low_items,
                safe_items=safe_items,
            )

        # 6. PENYUSUNAN METADATA & RESPONSE
        now_iso = datetime.now(timezone.utc).isoformat()

        requested_provider = resolved_provider
        if fallback_applied:
            execution_provider = "deterministic_fallback"
            actual_provider = "deterministic_fallback"
            generator_label = "Fallback Deterministik"
        else:
            execution_provider = resolved_provider
            actual_provider = resolved_provider
            if resolved_provider.lower().startswith("gemini"):
                generator_label = f"AI Assistant ({resolved_provider})"
            elif resolved_provider.lower() == "mock":
                generator_label = "Mock Service"
            else:
                generator_label = f"Layanan AI ({resolved_provider})"

        if is_synthetic:
            disclaimer_text = (
                f"PERINGATAN: Ringkasan ini dihasilkan oleh {generator_label} menggunakan "
                "data sintetis/ilustratif untuk prototipe ROKKUS, bukan data operasional nyata UMKM."
            )
        else:
            disclaimer_text = (
                f"PERINGATAN: Ringkasan ini dihasilkan oleh {generator_label}. "
                "Selalu verifikasi kondisi fisik inventaris toko sebelum mengambil keputusan pengadaan besar."
            )

        meta = DailySummaryMeta(
            provider=actual_provider,
            requested_provider=requested_provider,
            execution_provider=execution_provider,
            is_synthetic=is_synthetic,
            source=source,
            disclaimer=disclaimer_text,
            generated_at=now_iso,
            fallback_applied=fallback_applied,
            guardrail_status=guardrail_status,
        )

        data = DailySummaryData(
            date=date_str,
            store_name=store_name,
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

    def _format_structured_actions(
        self,
        actions: List[StructuredActionItem],
        valid_item_refs: Dict[str, ProcessedStockItem],
    ) -> List[str]:
        """Memformat tindakan terstruktur menjadi list string untuk kompatibilitas respon."""
        formatted: List[str] = []
        for act in actions:
            target_item = valid_item_refs.get(act.target_item_ref)
            target_name = target_item.name if target_item else act.target_item_ref
            formatted.append(f"[{act.action_type.value}] {target_name}: {act.notes}")

        if not formatted:
            formatted.append("Pertahankan rotasi barang menggunakan metode FIFO (First In First Out).")

        return formatted

    def _build_deterministic_narrative(
        self,
        date_str: str,
        store_name: str,
        counts: StockStatusCounts,
        empty_items: List[ProcessedStockItem],
        low_items: List[ProcessedStockItem],
        safe_items: List[ProcessedStockItem],
    ) -> str:
        """Generator narasi deterministik tanpa prediksi spekulatif (Fail-safe)."""
        parts: List[str] = []

        parts.append(
            f"Ringkasan Stok Harian ({date_str}) untuk {store_name}: "
            f"Dari total {counts.total_items} barang yang dipantau, tercatat "
            f"{counts.empty} barang berstatus EMPTY (habis), "
            f"{counts.low} barang berstatus LOW (menipis), dan "
            f"{counts.safe} barang berstatus SAFE (aman)."
        )

        if empty_items:
            empty_details = "; ".join(
                f"{item.name} (sisa {item.current_stock} {item.unit})"
                for item in empty_items
            )
            parts.append(
                f"Stok habis dan butuh pengadaan darurat segera: {empty_details}."
            )

        if low_items:
            low_details = "; ".join(
                f"{item.name} (sisa {item.current_stock} {item.unit})"
                for item in low_items
            )
            parts.append(
                f"Stok menipis yang perlu dijadwalkan restock: {low_details}."
            )

        if safe_items and not empty_items and not low_items:
            parts.append(
                "Seluruh stok barang saat ini berada dalam kondisi aman (> 5 unit) "
                "untuk mendukung operasional."
            )
        elif safe_items:
            parts.append(
                f"Sebanyak {counts.safe} barang lainnya berada dalam kondisi stok aman untuk operasional."
            )

        return " ".join(parts)

    def _build_deterministic_actions(
        self,
        empty_items: List[ProcessedStockItem],
        low_items: List[ProcessedStockItem],
        safe_items: List[ProcessedStockItem],
    ) -> List[str]:
        """Generator rekomendasi tindakan deterministik (Fail-safe)."""
        actions: List[str] = []

        if empty_items:
            names = ", ".join(i.name for i in empty_items)
            actions.append(f"Lakukan pemesanan ulang (restock) darurat hari ini untuk: {names}.")

        if low_items:
            names = ", ".join(i.name for i in low_items)
            actions.append(f"Jadwalkan restock dalam waktu dekat untuk item menipis: {names}.")

        if safe_items:
            actions.append("Pertahankan rotasi barang menggunakan metode FIFO (First In First Out).")

        if not empty_items and not low_items:
            actions.append("Lanjutkan pencatatan mutasi stok harian secara berkala.")

        return actions
