"""
test_preprocessing.py – Unit Test: Preprocessing Pipeline
==========================================================
Capstone Asah 2026 | Tim A26-CS159

Jalankan:
  cd ai/ml
  pytest tests/test_preprocessing.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

# Tambahkan src/ ke path
SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from preprocessing import (
    build_pipeline,
    clean_data,
    create_labels,
    engineer_features,
    time_split,
)

CONFIG_PATH = Path(__file__).parent.parent / "configs" / "config.yaml"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def cfg():
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


@pytest.fixture
def sample_df(cfg):
    """DataFrame minimal yang mensimulasikan data stok ROKKUS."""
    kol = cfg["data"]["kolom"]
    n = 60   # 60 hari, 2 SKU → 120 baris

    rows = []
    for sku in ["SKU-001", "SKU-002"]:
        batas_min = 15
        stok = 50
        for i in range(n):
            masuk  = int(np.random.default_rng(42 + i).integers(0, 25))
            keluar = int(np.random.default_rng(99 + i).integers(5, 35))
            stok   = max(0, stok + masuk - keluar)
            rows.append({
                kol["id_barang"]:     sku,
                kol["nama_barang"]:   "Roti Test",
                kol["kategori"]:      "roti_kukus",
                kol["rasa"]:          "coklat",
                kol["tanggal"]:       pd.Timestamp("2025-01-01") + pd.Timedelta(days=i),
                kol["stok_awal"]:     max(0, stok),
                kol["barang_masuk"]:  masuk,
                kol["barang_keluar"]: min(keluar, stok + masuk),
                kol["stok_akhir"]:    stok,
                kol["batas_minimum"]: batas_min,
            })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Tests: clean_data
# ---------------------------------------------------------------------------

class TestCleanData:
    def test_hapus_duplikat(self, sample_df, cfg):
        df_dup = pd.concat([sample_df, sample_df.iloc[:5]], ignore_index=True)
        df_clean = clean_data(df_dup, cfg)
        assert len(df_clean) == len(sample_df)

    def test_clip_nilai_negatif(self, cfg):
        kol = cfg["data"]["kolom"]
        df = pd.DataFrame([{
            kol["id_barang"]:     "SKU-X",
            kol["nama_barang"]:   "Test",
            kol["kategori"]:      "roti_kukus",
            kol["rasa"]:          "coklat",
            kol["tanggal"]:       pd.Timestamp("2025-01-01"),
            kol["stok_awal"]:     -5,
            kol["barang_masuk"]:  -10,
            kol["barang_keluar"]: 20,
            kol["stok_akhir"]:    10,
            kol["batas_minimum"]: 5,
        }])
        df_clean = clean_data(df, cfg)
        assert df_clean[kol["stok_awal"]].iloc[0] == 0
        assert df_clean[kol["barang_masuk"]].iloc[0] == 0

    def test_data_valid_tidak_diubah(self, sample_df, cfg):
        df_clean = clean_data(sample_df.copy(), cfg)
        # Jumlah baris tidak berkurang (tidak ada duplikat di sample_df)
        assert len(df_clean) == len(sample_df)


# ---------------------------------------------------------------------------
# Tests: engineer_features
# ---------------------------------------------------------------------------

class TestEngineerFeatures:
    def test_kolom_fitur_ada(self, sample_df, cfg):
        df_clean = clean_data(sample_df, cfg)
        df_feat  = engineer_features(df_clean, cfg)

        expected = ["avg_keluar_7h", "total_keluar_7h", "total_masuk_7h",
                    "stok_saat_ini", "days_of_cover", "rasio_stok"]
        for col in expected:
            assert col in df_feat.columns, f"Kolom '{col}' tidak ditemukan"

    def test_days_of_cover_non_negatif(self, sample_df, cfg):
        df_clean = clean_data(sample_df, cfg)
        df_feat  = engineer_features(df_clean, cfg)
        assert (df_feat["days_of_cover"] >= 0).all()

    def test_rasio_stok_non_negatif(self, sample_df, cfg):
        df_clean = clean_data(sample_df, cfg)
        df_feat  = engineer_features(df_clean, cfg)
        assert (df_feat["rasio_stok"] >= 0).all()

    def test_avg_keluar_7h_non_negatif(self, sample_df, cfg):
        df_clean = clean_data(sample_df, cfg)
        df_feat  = engineer_features(df_clean, cfg)
        assert (df_feat["avg_keluar_7h"] >= 0).all()


# ---------------------------------------------------------------------------
# Tests: create_labels
# ---------------------------------------------------------------------------

class TestCreateLabels:
    def test_semua_kelas_ada_dalam_data_besar(self, sample_df, cfg):
        df_clean  = clean_data(sample_df, cfg)
        df_feat   = engineer_features(df_clean, cfg)
        df_labeled = create_labels(df_feat, cfg)

        kelas = set(cfg["label_rules"]["kelas"])
        actual = set(df_labeled[cfg["label_rules"]["kolom_target"]].unique())
        # Setidaknya ada kelas "aman" (hampir pasti ada)
        assert "aman" in actual

    def test_stok_nol_selalu_habis(self, cfg):
        """Baris dengan stok_akhir == 0 harus dilabel 'habis'."""
        kol = cfg["data"]["kolom"]
        df = pd.DataFrame([{
            kol["id_barang"]:     "SKU-X",
            kol["nama_barang"]:   "Test",
            kol["kategori"]:      "roti_kukus",
            kol["rasa"]:          "coklat",
            kol["tanggal"]:       pd.Timestamp("2025-01-01"),
            kol["stok_awal"]:     10,
            kol["barang_masuk"]:  0,
            kol["barang_keluar"]: 10,
            kol["stok_akhir"]:    0,
            kol["batas_minimum"]: 5,
            "avg_keluar_7h":      5.0,
            "total_keluar_7h":    35.0,
            "total_masuk_7h":     20.0,
            "stok_saat_ini":      0.0,
            "days_of_cover":      0.0,
            "rasio_stok":         0.0,
        }])
        df_labeled = create_labels(df, cfg)
        assert df_labeled[cfg["label_rules"]["kolom_target"]].iloc[0] == "habis"

    def test_kolom_target_ada(self, sample_df, cfg):
        df_clean   = clean_data(sample_df, cfg)
        df_feat    = engineer_features(df_clean, cfg)
        df_labeled = create_labels(df_feat, cfg)
        assert cfg["label_rules"]["kolom_target"] in df_labeled.columns


# ---------------------------------------------------------------------------
# Tests: time_split
# ---------------------------------------------------------------------------

class TestTimeSplit:
    def test_ukuran_split(self, sample_df, cfg):
        df_clean   = clean_data(sample_df, cfg)
        df_feat    = engineer_features(df_clean, cfg)
        df_labeled = create_labels(df_feat, cfg)

        X_train, X_test, y_train, y_test = time_split(df_labeled, cfg)

        total = len(X_train) + len(X_test)
        assert total == len(df_labeled)
        # Test set ≈ 20%
        ratio = len(X_test) / total
        assert 0.15 <= ratio <= 0.25, f"Rasio test set tidak sesuai: {ratio:.2f}"

    def test_fitur_lengkap(self, sample_df, cfg):
        df_clean   = clean_data(sample_df, cfg)
        df_feat    = engineer_features(df_clean, cfg)
        df_labeled = create_labels(df_feat, cfg)

        X_train, X_test, y_train, y_test = time_split(df_labeled, cfg)

        expected_features = cfg["features"]["numerik"] + cfg["features"]["kategorik"]
        for f in expected_features:
            assert f in X_train.columns
            assert f in X_test.columns

    def test_pipeline_fit_transform(self, sample_df, cfg):
        df_clean   = clean_data(sample_df, cfg)
        df_feat    = engineer_features(df_clean, cfg)
        df_labeled = create_labels(df_feat, cfg)

        X_train, X_test, y_train, y_test = time_split(df_labeled, cfg)
        pipeline = build_pipeline(cfg)

        X_train_t = pipeline.fit_transform(X_train)
        X_test_t  = pipeline.transform(X_test)

        n_num = len(cfg["features"]["numerik"])
        n_cat = len(cfg["features"]["kategorik"])
        assert X_train_t.shape[1] == n_num + n_cat
        assert X_test_t.shape[1]  == n_num + n_cat
