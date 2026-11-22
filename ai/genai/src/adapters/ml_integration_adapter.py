"""Client dan adapter simulasi integrasi Machine Learning (ML) ROKKUS (Tahap 6B).

Menghubungkan GenAI dengan model ML Husain (POST /ml/predict-status)
dengan kemampuan mock offline, penanganan timeout/503/koneksi gagal (resilience),
dan pemisahan semantik antara:
1. Status stok aktual (DS/GenAI: EMPTY, LOW, SAFE)
2. Prediksi risiko stok masa depan (ML: habis, menipis, aman)
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

from ..schemas.ml_integration import (
    MLItemFeatureInput,
    MLItemRiskEnrichment,
    MLPredictRequest,
    MLPredictResponse,
    MLPrediksiItem,
)
from ..schemas.summary import (
    DailyStockItemInput,
    DailyStockSummaryRequest,
    DailyStockSummaryResponse,
    ProcessedStockItem,
)
from ..core.rules import StockStatus

logger = logging.getLogger(__name__)


class MLServiceClient:
    """Client untuk berinteraksi dengan layanan ML Husain (POST /ml/predict-status).

    Dapat beroperasi dalam mode mock offline (default untuk pengujian) maupun
    terhubung ke service nyata via HTTP client.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8001",
        timeout: float = 3.0,
        mock_mode: bool = True,
        mock_response_generator: Optional[callable] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.mock_mode = mock_mode
        self.mock_response_generator = mock_response_generator

    def predict_status(self, request: MLPredictRequest) -> MLPredictResponse:
        """Memanggil endpoint POST /ml/predict-status atau menghasilkan mock response."""
        if self.mock_mode:
            if self.mock_response_generator:
                return self.mock_response_generator(request)
            return self._default_mock_predict(request)

        # Mode live HTTP client (jika service aktif di masa depan)
        try:
            import httpx
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(
                    f"{self.base_url}/ml/predict-status",
                    json=request.model_dump(),
                )
                if res.status_code == 200:
                    return MLPredictResponse(**res.json())
                elif res.status_code == 503:
                    raise RuntimeError("ML Service Unavailable (503): Model belum siap.")
                else:
                    raise RuntimeError(f"ML Service HTTP Error {res.status_code}: {res.text}")
        except Exception as e:
            logger.warning(f"[MLServiceClient] Gagal memanggil ML Service: {e}")
            raise

    def _default_mock_predict(self, request: MLPredictRequest) -> MLPredictResponse:
        """Mock inferensi deterministik yang meniru perilaku model ML terbaik Husain."""
        predictions: List[MLPrediksiItem] = []
        for item in request.items:
            stok = item.stok_saat_ini
            bmin = item.batas_minimum
            doc = item.days_of_cover

            # Aturan inferensi mock sesuai konfigurasi ML Husain
            if stok == 0:
                status = "habis"
                proba = {"habis": 0.95, "menipis": 0.05, "aman": 0.0}
            elif (stok <= bmin) or (doc < 2.0):
                status = "menipis"
                proba = {"habis": 0.1, "menipis": 0.85, "aman": 0.05}
            else:
                status = "aman"
                proba = {"habis": 0.0, "menipis": 0.1, "aman": 0.9}

            predictions.append(
                MLPrediksiItem(
                    status=status,
                    probabilitas=proba,
                    versi_model="rf_v1.0.0_mock",
                )
            )

        return MLPredictResponse(
            total_items=len(predictions),
            prediksi=predictions,
        )


class MLGenAIIntegrator:
    """Orkestrator integrasi ML dan GenAI.

    Tanggung Jawab:
    1. Mengidentifikasi kelengkapan fitur dari item GenAI / dataset DS.
    2. Jika 11 fitur lengkap, memanggil MLServiceClient untuk mendapatkan prediksi risiko.
    3. Jika fitur tidak lengkap (misal DS hanya punya 1 snapshot tanpa histori 7 hari),
       TIDAK mengarang data histori, melainkan menandai ketiadaan fitur ML secara jujur.
    4. Menggabungkan rekomendasi dan wawasan risiko ML ke narasi/suggested_actions GenAI
       tanpa merusak status stok faktual (EMPTY, LOW, SAFE).
    """

    def __init__(self, ml_client: Optional[MLServiceClient] = None):
        self.ml_client = ml_client or MLServiceClient(mock_mode=True)

    def extract_ml_features_from_ds_row(
        self,
        ds_row: Dict[str, str | float],
    ) -> Tuple[Optional[MLItemFeatureInput], Optional[str]]:
        """Memeriksa apakah satu baris data dari dataset DS memiliki 11 fitur ML lengkap.

        Returns:
            (MLItemFeatureInput, None) jika lengkap,
            (None, reason_str) jika terdapat fitur yang hilang.
        """
        required_7d_features = [
            "avg_keluar_7h",
            "days_of_cover",
            "rasio_stok",
            "total_masuk_7h",
            "total_keluar_7h",
        ]
        missing = [f for f in required_7d_features if f not in ds_row or ds_row[f] is None]
        if missing:
            return None, f"Dataset DS tidak memiliki histori 7 hari: {missing}"

        try:
            feat = MLItemFeatureInput(
                stok_saat_ini=float(ds_row.get("stok_akhir", ds_row.get("stok_saat_ini", 0))),
                batas_minimum=float(ds_row.get("batas_minimum", 5.0)),
                barang_masuk=float(ds_row.get("total_masuk", ds_row.get("barang_masuk", 0))),
                barang_keluar=float(ds_row.get("total_keluar", ds_row.get("barang_keluar", 0))),
                avg_keluar_7h=float(ds_row["avg_keluar_7h"]),
                days_of_cover=float(ds_row["days_of_cover"]),
                rasio_stok=float(ds_row["rasio_stok"]),
                total_masuk_7h=float(ds_row["total_masuk_7h"]),
                total_keluar_7h=float(ds_row["total_keluar_7h"]),
                kategori=str(ds_row.get("kategori", "roti_kukus")),
                rasa=str(ds_row.get("rasa", ds_row.get("product_name", "original"))),
            )
            return feat, None
        except Exception as e:
            return None, f"Gagal validasi fitur ML: {e}"

    def enrich_summary_with_ml_insights(
        self,
        summary_response: DailyStockSummaryResponse,
        ml_inputs: Optional[List[MLItemFeatureInput]] = None,
    ) -> Tuple[DailyStockSummaryResponse, Optional[str]]:
        """Memperkaya ringkasan harian GenAI dengan prediksi risiko ML secara non-destruktif.

        Jika ML tidak tersedia (resilience mode), ringkasan GenAI asli tetap utuh
        dan status degradasi dicatat.
        """
        if not ml_inputs:
            return summary_response, "Fitur ML tidak disertakan (menggunakan evaluasi stok faktual DS)."

        try:
            predict_req = MLPredictRequest(items=ml_inputs)
            predict_res = self.ml_client.predict_status(predict_req)

            # Petakan hasil prediksi ke suggested_actions tanpa mengubah status_counts faktual
            high_risk_alerts = []
            for item_input, pred in zip(ml_inputs, predict_res.prediksi):
                # Catat prediksi risiko ML ("habis", "menipis", "aman")
                if pred.status in ("habis", "menipis"):
                    conf = pred.probabilitas.get(pred.status, 0.0) * 100
                    high_risk_alerts.append(
                        f"[ML_RISK_PREDICTION] {item_input.rasa}: Prediksi risiko '{pred.status}' "
                        f"(probabilitas {conf:.1f}%, model: {pred.versi_model})"
                    )

            if high_risk_alerts:
                # Tambahkan ke suggested_actions tanpa menghapus rekomendasi operasional GenAI
                summary_response.data.suggested_actions.extend(high_risk_alerts)

            return summary_response, None

        except Exception as e:
            logger.warning(f"[MLGenAIIntegrator] Gagal memperkaya ringkasan dengan ML: {e}")
            # Resilience fallback: kembalikan response GenAI asli tanpa gagal
            return summary_response, f"Layanan ML tidak tersedia atau gagal: {e}"
