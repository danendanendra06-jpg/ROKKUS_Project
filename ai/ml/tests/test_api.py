"""
test_api.py – Unit Test: FastAPI Endpoints
==========================================
Capstone Asah 2026 | Tim A26-CS159

Test:
  - GET /ml/health
  - POST /ml/predict-status (input valid)
  - POST /ml/predict-status (input tidak valid: stok negatif, kolom hilang, dll.)

Jalankan:
  cd ai/ml
  pytest tests/test_api.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from api import app

MODEL_PATH = Path(__file__).parent.parent / "models" / "best_model.joblib"
MODEL_AVAILABLE = MODEL_PATH.exists()

client = TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def valid_item():
    return {
        "stok_saat_ini":   5.0,
        "batas_minimum":  15.0,
        "barang_masuk":   20.0,
        "barang_keluar":  30.0,
        "avg_keluar_7h":  28.0,
        "days_of_cover":   0.18,
        "rasio_stok":      0.33,
        "total_masuk_7h": 140.0,
        "total_keluar_7h": 196.0,
        "kategori":        "roti_kukus",
        "rasa":            "coklat",
    }


@pytest.fixture
def valid_item_aman():
    return {
        "stok_saat_ini":   80.0,
        "batas_minimum":   15.0,
        "barang_masuk":    50.0,
        "barang_keluar":   20.0,
        "avg_keluar_7h":   18.0,
        "days_of_cover":    4.44,
        "rasio_stok":       5.33,
        "total_masuk_7h":  350.0,
        "total_keluar_7h": 126.0,
        "kategori":         "roti_bakar",
        "rasa":             "keju",
    }


# ---------------------------------------------------------------------------
# Tests: GET /ml/health
# ---------------------------------------------------------------------------

class TestHealth:
    def test_health_returns_200(self):
        resp = client.get("/ml/health")
        assert resp.status_code == 200

    def test_health_response_keys(self):
        resp = client.get("/ml/health")
        data = resp.json()
        assert "status" in data
        assert "model_ready" in data
        assert "keterangan" in data

    def test_health_status_field(self):
        resp = client.get("/ml/health")
        data = resp.json()
        assert data["status"] in ("ok", "degraded")

    def test_health_model_ready_is_bool(self):
        resp = client.get("/ml/health")
        assert isinstance(resp.json()["model_ready"], bool)


# ---------------------------------------------------------------------------
# Tests: POST /ml/predict-status – INPUT TIDAK VALID
# (Tidak memerlukan model; validasi terjadi sebelum inferensi)
# ---------------------------------------------------------------------------

class TestPredictInvalidInput:
    def test_stok_negatif_returns_422_or_400(self, valid_item):
        """Stok negatif harus ditolak (422 oleh Pydantic, karena ge=0 constraint)."""
        bad = valid_item.copy()
        bad["stok_saat_ini"] = -5.0
        resp = client.post("/ml/predict-status", json={"items": [bad]})
        assert resp.status_code in (400, 422)

    def test_batas_minimum_negatif_returns_422(self, valid_item):
        bad = valid_item.copy()
        bad["batas_minimum"] = -1.0
        resp = client.post("/ml/predict-status", json={"items": [bad]})
        assert resp.status_code in (400, 422)

    def test_kolom_wajib_hilang_returns_422(self, valid_item):
        """Kolom hilang → 422 dari Pydantic."""
        bad = valid_item.copy()
        del bad["stok_saat_ini"]
        resp = client.post("/ml/predict-status", json={"items": [bad]})
        assert resp.status_code == 422

    def test_kategori_kosong_returns_422(self, valid_item):
        bad = valid_item.copy()
        bad["kategori"] = ""
        resp = client.post("/ml/predict-status", json={"items": [bad]})
        assert resp.status_code == 422

    def test_rasa_spasi_saja_returns_422(self, valid_item):
        bad = valid_item.copy()
        bad["rasa"] = "   "
        resp = client.post("/ml/predict-status", json={"items": [bad]})
        assert resp.status_code == 422

    def test_tipe_salah_string_untuk_numerik(self, valid_item):
        bad = valid_item.copy()
        bad["stok_saat_ini"] = "banyak"
        resp = client.post("/ml/predict-status", json={"items": [bad]})
        assert resp.status_code == 422

    def test_daftar_items_kosong_returns_422(self):
        resp = client.post("/ml/predict-status", json={"items": []})
        assert resp.status_code == 422

    def test_body_tidak_lengkap_returns_422(self):
        resp = client.post("/ml/predict-status", json={})
        assert resp.status_code == 422

    def test_avg_keluar_7h_negatif_returns_422(self, valid_item):
        bad = valid_item.copy()
        bad["avg_keluar_7h"] = -0.5
        resp = client.post("/ml/predict-status", json={"items": [bad]})
        assert resp.status_code in (400, 422)

    def test_days_of_cover_negatif_returns_422(self, valid_item):
        bad = valid_item.copy()
        bad["days_of_cover"] = -1.0
        resp = client.post("/ml/predict-status", json={"items": [bad]})
        assert resp.status_code in (400, 422)


# ---------------------------------------------------------------------------
# Tests: POST /ml/predict-status – INPUT VALID
# (Hanya dijalankan jika model tersedia)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not MODEL_AVAILABLE, reason="Model belum dilatih (jalankan train.py)")
class TestPredictValidInput:
    def test_single_item_returns_200(self, valid_item):
        resp = client.post("/ml/predict-status", json={"items": [valid_item]})
        assert resp.status_code == 200

    def test_response_structure(self, valid_item):
        resp = client.post("/ml/predict-status", json={"items": [valid_item]})
        data = resp.json()
        assert "total_items" in data
        assert "prediksi"    in data
        assert isinstance(data["prediksi"], list)
        assert len(data["prediksi"]) == 1

    def test_prediksi_keys(self, valid_item):
        resp = client.post("/ml/predict-status", json={"items": [valid_item]})
        item = resp.json()["prediksi"][0]
        assert "status"       in item
        assert "probabilitas" in item
        assert "versi_model"  in item

    def test_status_valid_value(self, valid_item):
        resp = client.post("/ml/predict-status", json={"items": [valid_item]})
        status = resp.json()["prediksi"][0]["status"]
        assert status in ("aman", "menipis", "habis")

    def test_probabilitas_sum_to_one(self, valid_item):
        resp = client.post("/ml/predict-status", json={"items": [valid_item]})
        proba = resp.json()["prediksi"][0]["probabilitas"]
        total = sum(proba.values())
        assert abs(total - 1.0) < 1e-3

    def test_batch_items(self, valid_item, valid_item_aman):
        resp = client.post("/ml/predict-status",
                           json={"items": [valid_item, valid_item_aman]})
        data = resp.json()
        assert data["total_items"] == 2
        assert len(data["prediksi"]) == 2

    def test_semua_nol_stok_habis_atau_menipis(self, valid_item):
        """Input dengan stok 0 harus diprediksi 'habis' atau sangat menipis."""
        item = valid_item.copy()
        item["stok_saat_ini"] = 0.0
        item["days_of_cover"] = 0.0
        item["rasio_stok"]    = 0.0
        resp = client.post("/ml/predict-status", json={"items": [item]})
        assert resp.status_code == 200
        status = resp.json()["prediksi"][0]["status"]
        assert status in ("habis", "menipis")


# ---------------------------------------------------------------------------
# Tests: POST /ml/status (Rule-Based Endpoint Tanpa Model .joblib)
# ---------------------------------------------------------------------------

class TestStockStatusRuleBasedEndpoint:
    def test_minimal_payload_success(self):
        """Uji payload minimal: hanya stok_saat_ini dan batas_minimum."""
        payload = {
            "items": [
                {"stok_saat_ini": 3.0, "batas_minimum": 5.0}
            ]
        }
        resp = client.post("/ml/status", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_items"] == 1
        res = data["hasil"][0]
        assert res["status"] == "menipis"
        assert res["is_menipis"] is True
        assert res["is_habis"] is False
        assert res["metode"] == "rule_based"

    def test_stok_nol_adalah_habis(self):
        payload = {
            "items": [
                {"stok_saat_ini": 0, "batas_minimum": 10}
            ]
        }
        resp = client.post("/ml/status", json=payload)
        assert resp.status_code == 200
        res = resp.json()["hasil"][0]
        assert res["status"] == "habis"
        assert res["is_habis"] is True
        assert res["is_menipis"] is False

    def test_stok_sama_dengan_batas_adalah_menipis(self):
        payload = {
            "items": [
                {"stok_saat_ini": 5.0, "batas_minimum": 5.0}
            ]
        }
        resp = client.post("/ml/status", json=payload)
        assert resp.status_code == 200
        res = resp.json()["hasil"][0]
        assert res["status"] == "menipis"
        assert res["is_menipis"] is True

    def test_stok_di_atas_batas_adalah_aman(self):
        payload = {
            "items": [
                {"stok_saat_ini": 15.0, "batas_minimum": 5.0}
            ]
        }
        resp = client.post("/ml/status", json=payload)
        assert resp.status_code == 200
        res = resp.json()["hasil"][0]
        assert res["status"] == "aman"
        assert res["is_menipis"] is False
        assert res["is_habis"] is False

    def test_stok_desimal(self):
        payload = {
            "items": [
                {"stok_saat_ini": 0.5, "batas_minimum": 1.0}
            ]
        }
        resp = client.post("/ml/status", json=payload)
        assert resp.status_code == 200
        res = resp.json()["hasil"][0]
        assert res["status"] == "menipis"

    def test_batas_minimum_nol(self):
        payload = {
            "items": [
                {"stok_saat_ini": 0, "batas_minimum": 0},
                {"stok_saat_ini": 5, "batas_minimum": 0}
            ]
        }
        resp = client.post("/ml/status", json=payload)
        assert resp.status_code == 200
        hasil = resp.json()["hasil"]
        assert hasil[0]["status"] == "habis"
        assert hasil[1]["status"] == "aman"

    def test_stok_negatif_returns_422(self):
        payload = {
            "items": [
                {"stok_saat_ini": -1.0, "batas_minimum": 5.0}
            ]
        }
        resp = client.post("/ml/status", json=payload)
        assert resp.status_code == 422

    def test_batas_minimum_negatif_returns_422(self):
        payload = {
            "items": [
                {"stok_saat_ini": 10.0, "batas_minimum": -5.0}
            ]
        }
        resp = client.post("/ml/status", json=payload)
        assert resp.status_code == 422

    def test_batch_items(self):
        payload = {
            "items": [
                {"stok_saat_ini": 0, "batas_minimum": 5, "id_barang": "PR001"},
                {"stok_saat_ini": 3, "batas_minimum": 5, "id_barang": "PR002"},
                {"stok_saat_ini": 10, "batas_minimum": 5, "id_barang": "PR003"}
            ]
        }
        resp = client.post("/ml/status", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_items"] == 3
        assert data["hasil"][0]["status"] == "habis"
        assert data["hasil"][1]["status"] == "menipis"
        assert data["hasil"][2]["status"] == "aman"

