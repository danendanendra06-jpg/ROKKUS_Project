"""
preprocessing.py – Load, Validasi, Feature Engineering, Split
==============================================================
Capstone Asah 2026 | Tim A26-CS159

Pipeline:
  1. Load CSV & validasi kolom wajib
  2. Cleaning (duplikat, nilai negatif, missing)
  3. Feature engineering per SKU (rolling, rasio, days_of_cover)
  4. Labeling otomatis dari aturan di config
  5. Build sklearn Pipeline (scaling numerik + encoding kategorik)
  6. Split berbasis waktu (train = awal, test = akhir)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd
import yaml
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder, StandardScaler

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_config(config_path: str | Path) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _resolve_path(base: Path, path_str: str) -> Path:
    """Resolve path relatif terhadap base (direktori ai/ml/)."""
    p = Path(path_str)
    if p.is_absolute():
        return p
    return (base / p).resolve()


# ---------------------------------------------------------------------------
# 1. Load & Validasi
# ---------------------------------------------------------------------------

def load_data(config_path: str | Path) -> Tuple[pd.DataFrame, dict]:
    """
    Load CSV dari path di config, validasi kolom wajib.

    Returns
    -------
    df : DataFrame mentah
    cfg : dict konfigurasi
    """
    cfg = _load_config(config_path)
    base_dir = Path(config_path).parent.parent   # ai/ml/

    csv_path = _resolve_path(base_dir, cfg["data"]["path_data"])
    logger.info(f"Memuat data dari: {csv_path}")

    if not csv_path.exists():
        raise FileNotFoundError(
            f"File data tidak ditemukan: {csv_path}\n"
            "Jalankan: python src/make_dummy_data.py  (untuk data sintetis)\n"
            "atau ubah path_data di configs/config.yaml ke dataset asli."
        )

    df = pd.read_csv(csv_path, parse_dates=[cfg["data"]["kolom"]["tanggal"]], encoding="utf-8")

    # Validasi kolom wajib
    kolom = cfg["data"]["kolom"]
    wajib = list(kolom.values())
    hilang = [c for c in wajib if c not in df.columns]
    if hilang:
        raise ValueError(
            f"Kolom berikut tidak ditemukan di CSV:\n  {hilang}\n"
            "Periksa mapping `kolom` di configs/config.yaml."
        )

    logger.info(f"Data dimuat: {len(df):,} baris, {df.shape[1]} kolom")
    return df, cfg


# ---------------------------------------------------------------------------
# 2. Cleaning
# ---------------------------------------------------------------------------

def clean_data(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """
    - Hapus duplikat (id_barang, tanggal)
    - Pastikan nilai numerik non-negatif
    - Isi missing dengan 0 untuk kolom transaksi
    """
    kol = cfg["data"]["kolom"]
    pk  = [kol["id_barang"], kol["tanggal"]]

    n_before = len(df)
    df = df.drop_duplicates(subset=pk, keep="last")
    n_after = len(df)
    if n_before != n_after:
        logger.warning(f"Dihapus {n_before - n_after} baris duplikat.")

    # Kolom numerik wajib non-negatif
    num_cols = [
        kol["stok_awal"], kol["barang_masuk"],
        kol["barang_keluar"], kol["stok_akhir"],
        kol["batas_minimum"],
    ]
    for col in num_cols:
        n_neg = (df[col] < 0).sum()
        if n_neg > 0:
            logger.warning(f"  {n_neg} nilai negatif di '{col}' di-clip ke 0.")
            df[col] = df[col].clip(lower=0)

    # Isi missing
    for col in num_cols:
        if df[col].isna().any():
            df[col] = df[col].fillna(0)
            logger.warning(f"  Missing value di '{col}' diisi 0.")

    # Sort untuk rolling
    df = df.sort_values([kol["id_barang"], kol["tanggal"]]).reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# 3. Feature Engineering
# ---------------------------------------------------------------------------

def engineer_features(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """
    Feature engineering berbasis jendela waktu per SKU.

    Fitur yang dibuat:
      - avg_keluar_7h    : rolling mean 7 hari barang_keluar
      - total_keluar_7h  : rolling sum 7 hari barang_keluar
      - total_masuk_7h   : rolling sum 7 hari barang_masuk
      - days_of_cover    : stok_akhir / max(avg_keluar_7h, min_avg)
      - rasio_stok       : stok_akhir / max(batas_minimum, 1)
      - stok_saat_ini    : alias stok_akhir (lebih deskriptif sebagai fitur)

    CATATAN LEAKAGE:
      stok_akhir tidak dipakai langsung sebagai fitur model—hanya lewat
      days_of_cover dan rasio_stok—untuk menghindari kebocoran trivial dari
      label ke fitur (label diturunkan dari stok_akhir dan batas_minimum).
      Lihat docs/leakage_note di README.md.
    """
    kol = cfg["data"]["kolom"]
    feat_cfg = cfg["features"]
    win  = feat_cfg["rolling_window_days"]
    dmin = feat_cfg["days_of_cover_min_avg"]

    col_id     = kol["id_barang"]
    col_masuk  = kol["barang_masuk"]
    col_keluar = kol["barang_keluar"]
    col_akhir  = kol["stok_akhir"]
    col_batas  = kol["batas_minimum"]

    df = df.copy()

    # Rolling per SKU (min_periods=1 agar baris awal tetap valid)
    grouped = df.groupby(col_id, sort=False)

    df["avg_keluar_7h"] = (
        grouped[col_keluar]
        .transform(lambda x: x.rolling(win, min_periods=1).mean())
    )
    df["total_keluar_7h"] = (
        grouped[col_keluar]
        .transform(lambda x: x.rolling(win, min_periods=1).sum())
    )
    df["total_masuk_7h"] = (
        grouped[col_masuk]
        .transform(lambda x: x.rolling(win, min_periods=1).sum())
    )

    # Alias + derived
    df["stok_saat_ini"] = df[col_akhir]
    avg_safe = df["avg_keluar_7h"].clip(lower=dmin)
    df["days_of_cover"] = (df["stok_saat_ini"] / avg_safe).clip(upper=30.0)
    df["rasio_stok"]    = df["stok_saat_ini"] / df[col_batas].clip(lower=1)

    return df


# ---------------------------------------------------------------------------
# 4. Labeling
# ---------------------------------------------------------------------------

def create_labels(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """
    Buat kolom label `status_stok` berdasarkan aturan di config:

      habis   → stok_akhir == 0
      menipis → stok_akhir > 0 DAN
                (stok_akhir <= batas_minimum ATAU days_of_cover < threshold)
      aman    → selain itu
    """
    kol        = cfg["data"]["kolom"]
    lr         = cfg["label_rules"]
    target_col = lr["kolom_target"]
    habis_thr  = lr["habis_threshold"]
    doc_thr    = lr["days_of_cover_threshold"]

    col_akhir = kol["stok_akhir"]
    col_batas = kol["batas_minimum"]

    df = df.copy()

    cond_habis   = df[col_akhir] <= habis_thr
    cond_menipis = (
        (~cond_habis) & (
            (df[col_akhir] <= df[col_batas]) |
            (df["days_of_cover"] < doc_thr)
        )
    )

    df[target_col] = "aman"
    df.loc[cond_menipis, target_col] = "menipis"
    df.loc[cond_habis,   target_col] = "habis"

    dist = df[target_col].value_counts()
    logger.info(f"Distribusi label:\n{dist.to_string()}")
    return df


# ---------------------------------------------------------------------------
# 5. Build sklearn Pipeline
# ---------------------------------------------------------------------------

def build_pipeline(cfg: dict) -> Pipeline:
    """
    Buat sklearn Pipeline dengan ColumnTransformer:
      - Numerik  : StandardScaler
      - Kategorik: OrdinalEncoder (handle_unknown='use_encoded_value', unknown_value=-1)

    Pipeline ini di-fit HANYA pada data train, lalu di-transform ke train & test.
    """
    feat_cfg = cfg["features"]
    num_features = feat_cfg["numerik"]
    cat_features = feat_cfg["kategorik"]

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), num_features),
            (
                "cat",
                OrdinalEncoder(
                    handle_unknown="use_encoded_value",
                    unknown_value=-1,
                    dtype=np.float64,
                ),
                cat_features,
            ),
        ],
        remainder="drop",   # Kolom lain diabaikan oleh transformer
    )

    pipeline = Pipeline([("preprocessor", preprocessor)])
    return pipeline


# ---------------------------------------------------------------------------
# 6. Split Berbasis Waktu
# ---------------------------------------------------------------------------

def time_split(
    df: pd.DataFrame,
    cfg: dict,
    target_col: Optional[str] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Split data train/test berbasis waktu (train = awal, test = akhir).
    Ini lebih jujur untuk data time-series daripada random split.

    Returns
    -------
    X_train, X_test, y_train, y_test
    """
    lr = cfg["label_rules"]
    sp = cfg["split"]
    feat_cfg = cfg["features"]

    target = target_col or lr["kolom_target"]
    kol    = cfg["data"]["kolom"]
    col_tgl = kol["tanggal"]

    all_features = feat_cfg["numerik"] + feat_cfg["kategorik"]

    # Kolom yang dibutuhkan ada?
    missing_feat = [f for f in all_features if f not in df.columns]
    if missing_feat:
        raise ValueError(f"Fitur tidak ditemukan di DataFrame: {missing_feat}")
    if target not in df.columns:
        raise ValueError(f"Kolom target '{target}' tidak ditemukan.")

    df_sorted = df.sort_values(col_tgl).reset_index(drop=True)

    if sp["tanggal_split"]:
        cutoff = pd.Timestamp(sp["tanggal_split"])
        train_mask = df_sorted[col_tgl] < cutoff
        test_mask  = ~train_mask
    else:
        n = len(df_sorted)
        split_idx = int(n * (1 - sp["test_size"]))
        train_mask = pd.Series([True] * split_idx + [False] * (n - split_idx))
        test_mask  = ~train_mask

    df_train = df_sorted[train_mask.values]
    df_test  = df_sorted[test_mask.values]

    logger.info(
        f"Split: train={len(df_train):,} ({len(df_train)/len(df)*100:.1f}%), "
        f"test={len(df_test):,} ({len(df_test)/len(df)*100:.1f}%)"
    )

    X_train = df_train[all_features]
    X_test  = df_test[all_features]
    y_train = df_train[target]
    y_test  = df_test[target]

    return X_train, X_test, y_train, y_test


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_preprocessing(config_path: str | Path) -> dict:
    """
    Jalankan seluruh pipeline preprocessing.

    Returns
    -------
    dict berisi:
      df_full    : DataFrame lengkap setelah feature engineering & labeling
      X_train    : fitur train (belum di-transform sklearn)
      X_test     : fitur test
      y_train    : label train
      y_test     : label test
      pipeline   : sklearn Pipeline (belum di-fit)
      cfg        : dict konfigurasi
    """
    df_raw, cfg = load_data(config_path)
    df_clean    = clean_data(df_raw, cfg)
    df_feat     = engineer_features(df_clean, cfg)
    df_labeled  = create_labels(df_feat, cfg)

    X_train, X_test, y_train, y_test = time_split(df_labeled, cfg)
    pipeline = build_pipeline(cfg)

    return {
        "df_full":  df_labeled,
        "X_train":  X_train,
        "X_test":   X_test,
        "y_train":  y_train,
        "y_test":   y_test,
        "pipeline": pipeline,
        "cfg":      cfg,
    }


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    cfg_path = Path(__file__).parent.parent / "configs" / "config.yaml"
    result = run_preprocessing(cfg_path)

    df = result["df_full"]
    print(f"\nTotal baris     : {len(df):,}")
    print(f"Fitur numerik   : {result['cfg']['features']['numerik']}")
    print(f"Fitur kategorik : {result['cfg']['features']['kategorik']}")
    print(f"\nX_train shape   : {result['X_train'].shape}")
    print(f"X_test shape    : {result['X_test'].shape}")
    print(f"\nDistribusi label (train):\n{result['y_train'].value_counts()}")
    print(f"\nDistribusi label (test):\n{result['y_test'].value_counts()}")
