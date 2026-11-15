"""
test_predict.py – Unit Test: Fungsi Inferensi
==============================================
Capstone Asah 2026 | Tim A26-CS159

Jalankan:
  cd ai/ml
  pytest tests/test_predict.py -v

Catatan: test yang membutuhkan model terlatih dilewati (xfail/skip)
  jika file models/best_model.joblib belum ada.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from predict import PredictInputError, flag_stok_menipis, predict_status

CONFIG_PATH = Path(__file__).parent.parent / "configs" / "config.yaml"
MODEL_PATH  = Path(__file__).parent.parent / "models" / "best_model.joblib"
META_PATH   = Path(__file__).parent.parent / "models" / "metadata.json"

MODEL_AVAILABLE = MODEL_PATH.exists()

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def valid_input():
    """Contoh input valid."""
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
def valid_input_aman():
    """Contoh input yang seharusnya 'aman'."""
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
# Tests: flag_stok_menipis (rule-based, tidak butuh model)
# ---------------------------------------------------------------------------

class TestFlagStokMenipis:
    def test_stok_habis(self):
        result = flag_stok_menipis(0, 15.0, days_of_cover=0.0)
        assert result["is_habis"]    is True
        assert result["is_menipis"]  is False

    def test_stok_menipis_karena_batas(self):
        # Stok 10, batas 15 → menipis karena stok < batas
        result = flag_stok_menipis(10, 15.0, days_of_cover=3.0)
        assert result["is_menipis"] is True
        assert result["is_habis"]   is False

    def test_stok_menipis_karena_days_of_cover(self):
        # Stok 20, batas 15 (aman dari batas), tapi days_of_cover < 2
        result = flag_stok_menipis(20, 15.0, days_of_cover=1.0,
                                   config_path=CONFIG_PATH)
        assert result["is_menipis"] is True

    def test_stok_aman(self):
        result = flag_stok_menipis(50, 15.0, days_of_cover=5.0)
        assert result["is_menipis"] is False
        assert result["is_habis"]   is False
        assert "aman" in result["saran"].lower()

    def test_stok_negatif_raises(self):
        with pytest.raises(PredictInputError, match="negatif"):
            flag_stok_menipis(-1, 15.0)

    def test_batas_negatif_raises(self):
        with pytest.raises(PredictInputError, match="negatif"):
            flag_stok_menipis(10, -5.0)

    def test_tipe_salah_raises(self):
        with pytest.raises(PredictInputError):
            flag_stok_menipis("banyak", 15.0)

    def test_tanpa_days_of_cover(self):
        """days_of_cover bersifat opsional."""
        result = flag_stok_menipis(10, 15.0)
        assert result["is_menipis"] is True   # karena stok <= batas_minimum

    def test_output_keys_lengkap(self):
        result = flag_stok_menipis(5, 15, 0.5)
        assert "is_menipis" in result
        assert "is_habis"   in result
        assert "alasan"     in result
        assert "saran"      in result


# ---------------------------------------------------------------------------
# Tests: validate_input (via predict_status, tanpa model)
# ---------------------------------------------------------------------------

class TestValidateInput:
    def test_kolom_hilang(self):
        with pytest.raises(PredictInputError, match="wajib ada"):
            predict_status(
                {"stok_saat_ini": 5},   # sangat tidak lengkap
                model_path=MODEL_PATH,
                config_path=CONFIG_PATH,
            )

    def test_stok_negatif_raises(self, valid_input):
        bad = valid_input.copy()
        bad["stok_saat_ini"] = -1.0
        with pytest.raises(PredictInputError, match="negatif"):
            predict_status(bad, model_path=MODEL_PATH, config_path=CONFIG_PATH)

    def test_kategori_kosong_raises(self, valid_input):
        bad = valid_input.copy()
        bad["kategori"] = ""
        with pytest.raises(PredictInputError):
            predict_status(bad, model_path=MODEL_PATH, config_path=CONFIG_PATH)

    def test_nan_raises(self, valid_input):
        import math
        bad = valid_input.copy()
        bad["avg_keluar_7h"] = math.nan
        with pytest.raises(PredictInputError):
            predict_status(bad, model_path=MODEL_PATH, config_path=CONFIG_PATH)


# ---------------------------------------------------------------------------
# Tests: predict_status (memerlukan model terlatih)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not MODEL_AVAILABLE, reason="Model belum dilatih (jalankan train.py)")
class TestPredictStatus:
    def test_output_keys(self, valid_input):
        result = predict_status(
            valid_input,
            model_path=MODEL_PATH,
            config_path=CONFIG_PATH,
            meta_path=META_PATH,
        )
        assert "status"       in result
        assert "probabilitas" in result
        assert "versi_model"  in result

    def test_status_valid_string(self, valid_input):
        result = predict_status(valid_input, model_path=MODEL_PATH,
                                config_path=CONFIG_PATH, meta_path=META_PATH)
        with open(CONFIG_PATH) as f:
            cfg = yaml.safe_load(f)
        assert result["status"] in cfg["label_rules"]["kelas"]

    def test_probabilitas_sum_to_one(self, valid_input):
        result = predict_status(valid_input, model_path=MODEL_PATH,
                                config_path=CONFIG_PATH, meta_path=META_PATH)
        total = sum(result["probabilitas"].values())
        assert abs(total - 1.0) < 1e-3, f"Sum probabilitas = {total}"

    def test_batch_input(self, valid_input, valid_input_aman):
        results = predict_status(
            [valid_input, valid_input_aman],
            model_path=MODEL_PATH,
            config_path=CONFIG_PATH,
            meta_path=META_PATH,
        )
        assert isinstance(results, list)
        assert len(results) == 2
        for r in results:
            assert "status" in r
            assert "probabilitas" in r

    def test_model_tidak_crash_dengan_unknown_kategori(self, valid_input):
        """Input dengan kategori tidak dikenal: pipeline harus handle, tidak crash."""
        unknown = valid_input.copy()
        unknown["kategori"] = "roti_goreng"   # kategori tidak ada di training
        try:
            result = predict_status(unknown, model_path=MODEL_PATH,
                                    config_path=CONFIG_PATH, meta_path=META_PATH)
            # Tidak crash → test passed
            assert "status" in result
        except PredictInputError:
            pass   # Jika divalidasi dan ditolak → juga ok
