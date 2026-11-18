"""Guardrails dan skema validasi output terstruktur untuk ROKKUS AI Inventory Assistant."""

from enum import Enum
import json
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ValidationError


class ActionType(str, Enum):
    """Tipe rekomendasi operasional yang diizinkan dan dapat divalidasi."""
    RESTOCK_REVIEW = "RESTOCK_REVIEW"
    MONITOR = "MONITOR"
    NO_ACTION = "NO_ACTION"


class StructuredActionItem(BaseModel):
    """Rekomendasi tindakan operasional terhadap item inventaris tertentu."""
    action_type: ActionType = Field(..., description="Tipe tindakan: RESTOCK_REVIEW, MONITOR, atau NO_ACTION")
    target_item_ref: str = Field(..., description="Identifier item yang sah (misal 'BB-001' atau 'ITEM_1')")
    notes: str = Field(..., min_length=2, max_length=300, description="Keterangan singkat tindakan faktual")


class LLMSummaryOutput(BaseModel):
    """Format JSON terstruktur yang wajib dihasilkan oleh model bahasa."""
    narrative: str = Field(..., min_length=10, max_length=1500, description="Teks narasi ringkasan kondisi stok harian")
    actions: List[StructuredActionItem] = Field(default=[], description="Daftar tindakan operasional terstruktur")
    data_limitations_note: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Catatan faktual jika data tertentu seperti keuangan atau riwayat mutasi tidak tersedia"
    )


class GuardrailValidationResult:
    """Hasil verifikasi guardrail terhadap respon model."""

    def __init__(
        self,
        is_valid: bool,
        violations: Optional[List[str]] = None,
        parsed_output: Optional[LLMSummaryOutput] = None,
    ):
        self.is_valid = is_valid
        self.violations = violations or []
        self.parsed_output = parsed_output

    def __repr__(self) -> str:
        return f"<GuardrailValidationResult is_valid={self.is_valid} violations={len(self.violations)}>"


class SummaryOutputGuardrail:
    """Guardrail untuk memvalidasi output model dan mencegah halusinasi data."""

    # Pola klaim keuangan/transaksi tanpa bukti (mengabaikan kalimat yang menjelaskan ketiadaan data)
    ASSERTIVE_FINANCIAL_PATTERNS = [
        re.compile(r"\b(omzet|omset|penjualan|laba|rugi|keuntungan)\s*(sebesar|mencapai|sebanyak|tercatat|total)\s*(rp\.?|rupiah|\d+)", re.IGNORECASE),
        re.compile(r"\b(rp\.?|rupiah)\s*\d+([.,]\d+)?\b", re.IGNORECASE),
        re.compile(r"\b\d+\s*transaksi\s*(berhasil|terjadi|tercatat)\b", re.IGNORECASE),
    ]

    # Pola prediksi waktu spekulatif yang dilarang
    SPECULATIVE_TIMEFRAME_PATTERNS = [
        re.compile(r"\b\d+\s*(hari|minggu|bulan)\s*(ke depan|lagi)\b", re.IGNORECASE),
        re.compile(r"\bhabis\s+dalam\b", re.IGNORECASE),
        re.compile(r"\bbertahan\s+(hingga|sampai|selama)\b", re.IGNORECASE),
        re.compile(r"\bcukup\s+untuk\s+\d+\s*hari\b", re.IGNORECASE),
    ]

    # Frasa pengecualian yang sah (hanya menjelaskan keterbatasan data)
    DATA_UNAVAILABLE_EXCEPTIONS = [
        "tidak tersedia",
        "belum tersedia",
        "tidak disertakan",
        "tidak tercatat",
        "bukan data operasional",
        "tanpa data",
    ]

    def validate(
        self,
        raw_output: str | dict,
        valid_item_refs: Dict[str, Any],
        processed_items_by_ref: Optional[Dict[str, Any]] = None,
    ) -> GuardrailValidationResult:
        """Memvalidasi output LLM secara komprehensif.

        Args:
            raw_output: String JSON mentah atau dict hasil parsing model.
            valid_item_refs: Mapping identifier item yang valid (misal: {'BB-001': item, 'ITEM_1': item}).
            processed_items_by_ref: Mapping item ke status deterministik hasil Stock Evaluator.

        Returns:
            GuardrailValidationResult: Status validitas, daftar pelanggaran, dan objek output terstruktur.
        """
        violations: List[str] = []
        parsed_model: Optional[LLMSummaryOutput] = None

        # 1. Validasi Schema & JSON Parsing
        if isinstance(raw_output, str):
            try:
                # Bersihkan markdown wrapper jika model mengembalikan ```json ... ```
                cleaned = raw_output.strip()
                if cleaned.startswith("```"):
                    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
                    cleaned = re.sub(r"\s*```$", "", cleaned)
                data_dict = json.loads(cleaned)
            except Exception as e:
                return GuardrailValidationResult(
                    is_valid=False,
                    violations=[f"Output bukan merupakan format JSON yang valid: {str(e)}"],
                )
        elif isinstance(raw_output, dict):
            data_dict = raw_output
        else:
            return GuardrailValidationResult(
                is_valid=False,
                violations=["Tipe data raw_output harus berupa string JSON atau dict."],
            )

        try:
            parsed_model = LLMSummaryOutput.model_validate(data_dict)
        except ValidationError as e:
            field_errors = [f"{err['loc']}: {err['msg']}" for err in e.errors()]
            return GuardrailValidationResult(
                is_valid=False,
                violations=[f"Ketidaksesuaian skema output Pydantic: {', '.join(field_errors)}"],
            )

        # 2. Validasi Referensi Produk (Anti-Fictitious Product Entity)
        for idx, action in enumerate(parsed_model.actions):
            ref = action.target_item_ref.strip()
            if ref not in valid_item_refs:
                violations.append(
                    f"Action #{idx+1} mereferensikan produk fiktif/tidak dikenal: '{ref}'. "
                    f"Daftar item_ref sah yang tersedia: {list(valid_item_refs.keys())}"
                )

        # 3. Validasi Integritas Klaim Finansial & Transaksi
        text_to_check = parsed_model.narrative
        for pattern in self.ASSERTIVE_FINANCIAL_PATTERNS:
            match = pattern.search(text_to_check)
            if match:
                # Periksa apakah kalimat tersebut semata-mata menyatakan ketiadaan data
                matched_span = match.group(0)
                is_benign = any(exc in text_to_check.lower() for exc in self.DATA_UNAVAILABLE_EXCEPTIONS)
                # Jika klaim secara eksplisit menyebut angka/nominal rupiah, itu tetap pelanggaran
                has_nominal = bool(re.search(r"\b(rp\.?|rupiah|\d+)\b", matched_span, re.IGNORECASE))
                if has_nominal or not is_benign:
                    violations.append(
                        f"Terdeteksi klaim data finansial/omzet tanpa bukti: '{matched_span}'."
                    )

        # 4. Validasi Klaim Waktu Spekulatif (Speculative Timeframe)
        for pattern in self.SPECULATIVE_TIMEFRAME_PATTERNS:
            match = pattern.search(text_to_check)
            if match:
                violations.append(
                    f"Terdeteksi prediksi spekulatif ketahanan stok: '{match.group(0)}'."
                )

        # 5. Validasi Keselarasan Logika Rekomendasi (Sanity Check)
        if processed_items_by_ref:
            for action in parsed_model.actions:
                item = processed_items_by_ref.get(action.target_item_ref.strip())
                if item:
                    # Item berstatus SAFE tidak boleh diberi tindakan RESTOCK_REVIEW tanpa alasan
                    if getattr(item, "status", None) == "SAFE" and action.action_type == ActionType.RESTOCK_REVIEW:
                        violations.append(
                            f"Rekomendasi tidak konsisten: Item '{action.target_item_ref}' berstatus SAFE "
                            f"tetapi diberi tindakan RESTOCK_REVIEW."
                        )

        is_valid = len(violations) == 0
        return GuardrailValidationResult(
            is_valid=is_valid,
            violations=violations,
            parsed_output=parsed_model if is_valid else None,
        )
