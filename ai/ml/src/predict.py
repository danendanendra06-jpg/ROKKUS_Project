"""
predict.py – Inferensi Model Terbaik
=====================================
Capstone Asah 2026 | Tim A26-CS159

Fungsi publik:
  predict_status(input_data, model_path, config_path)
    → dict: status, probabilitas per kelas, versi model

  flag_stok_menipis(stok_saat_ini, batas_minimum, days_of_cover, cfg)
    → dict: is_menipis, alasan, saran
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional, Union

import joblib
import numpy as np
import pandas as pd
import yaml

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default paths (relatif terhadap ai/ml/)
# ---------------------------------------------------------------------------
_ML_DIR = Path(__file__).parent.parent
_DEFAULT_CONFIG = _ML_DIR / "configs" / "config.yaml"
_DEFAULT_MODEL  = _ML_DIR / "models" / "best_model.joblib"
_DEFAULT_META   = _ML_DIR / "models" / "metadata.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_config(config_path: Path) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_metadata(meta_path: Path) -> dict:
    with open(meta_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _resolve(base: Path, path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (base / p).resolve()


# ---------------------------------------------------------------------------
# Validasi input
# ---------------------------------------------------------------------------

REQUIRED_FEATURES_DOC = """
Input dict wajib mengandung semua fitur numerik dan kategorik sesuai config:
  Numerik  : stok_saat_ini, batas_minimum, barang_masuk, barang_keluar,
             avg_keluar_7h, days_of_cover, rasio_stok,
             total_masuk_7h, total_keluar_7h
  Kategorik: kategori, rasa
"""


class PredictInputError(ValueError):
    """Raised ketika input ke predict_status tidak valid."""


def _validate_input(input_data: dict, required_features: list[str]) -> None:
    """
    Validasi input dictionary sebelum inferensi.
    Raises PredictInputError jika ada masalah.
    """
    # Kolom hilang
    missing = [f for f in required_features if f not in input_data]
    if missing:
        raise PredictInputError(
            f"Kolom berikut wajib ada di input: {missing}\n{REQUIRED_FEATURES_DOC}"
        )

    # Validasi numerik non-negatif
    non_neg_cols = [
        "stok_saat_ini", "batas_minimum", "barang_masuk", "barang_keluar",
        "avg_keluar_7h", "days_of_cover", "rasio_stok",
        "total_masuk_7h", "total_keluar_7h",
    ]
    for col in non_neg_cols:
        if col not in input_data:
            continue
        val = input_data[col]
        if not isinstance(val, (int, float)):
            raise PredictInputError(f"Kolom '{col}' harus berupa angka, bukan {type(val).__name__}.")
        if val < 0:
            raise PredictInputError(
                f"Nilai negatif tidak valid: '{col}' = {val}. "
                "Stok dan nilai transaksi tidak boleh negatif."
            )
        if np.isnan(val) or np.isinf(val):
            raise PredictInputError(f"Kolom '{col}' berisi NaN atau Inf.")

    # Validasi kategorik non-empty
    cat_cols = ["kategori", "rasa"]
    for col in cat_cols:
        if col not in input_data:
            continue
        val = input_data[col]
        if not isinstance(val, str) or not val.strip():
            raise PredictInputError(
                f"Kolom '{col}' harus berupa string non-kosong."
            )


# ---------------------------------------------------------------------------
# Fungsi utama: predict_status
# ---------------------------------------------------------------------------

def predict_status(
    input_data: Union[dict, list[dict]],
    model_path: Optional[Path] = None,
    config_path: Optional[Path] = None,
    meta_path: Optional[Path] = None,
) -> Union[dict, list[dict]]:
    """
    Prediksi status stok untuk satu atau beberapa item.

    Parameters
    ----------
    input_data : dict atau list[dict]
        Fitur per item stok. Semua fitur numerik dan kategorik wajib ada.
    model_path : Path, optional
        Path ke file .joblib model terbaik.
    config_path : Path, optional
        Path ke config.yaml.
    meta_path : Path, optional
        Path ke metadata.json.

    Returns
    -------
    dict (untuk input tunggal) atau list[dict] (untuk input list).
    Tiap dict berisi:
      {
        "status"      : str  ("aman" | "menipis" | "habis"),
        "probabilitas": {kelas: float, ...},
        "versi_model" : str,
      }

    Raises
    ------
    PredictInputError     : jika input tidak valid.
    FileNotFoundError     : jika model/config tidak ditemukan.
    """
    model_path  = model_path  or _DEFAULT_MODEL
    config_path = config_path or _DEFAULT_CONFIG
    meta_path   = meta_path   or _DEFAULT_META

    if not Path(model_path).exists():
        raise FileNotFoundError(
            f"Model tidak ditemukan: {model_path}\n"
            "Jalankan: python src/train.py"
        )

    model    = joblib.load(model_path)
    cfg      = _load_config(config_path)
    metadata = _load_metadata(meta_path) if Path(meta_path).exists() else {"versi": "unknown"}

    feat_cfg   = cfg["features"]
    all_features = feat_cfg["numerik"] + feat_cfg["kategorik"]
    kelas      = cfg["label_rules"]["kelas"]
    versi      = metadata.get("versi", "unknown")

    single = isinstance(input_data, dict)
    items  = [input_data] if single else input_data

    results = []
    for item in items:
        _validate_input(item, all_features)

        df = pd.DataFrame([item])[all_features]

        pred   = model.predict(df)[0]
        proba  = {}
        if hasattr(model, "predict_proba"):
            proba_arr = model.predict_proba(df)[0]
            kelas_model = list(model.classes_)
            # Pastikan urutan sesuai kelas di config
            for k in kelas:
                if k in kelas_model:
                    proba[k] = round(float(proba_arr[kelas_model.index(k)]), 4)
                else:
                    proba[k] = 0.0
        else:
            proba = {k: (1.0 if k == pred else 0.0) for k in kelas}

        results.append({
            "status":       str(pred),
            "probabilitas": proba,
            "versi_model":  versi,
        })

    return results[0] if single else results


# ---------------------------------------------------------------------------
# Fungsi tambahan: flag_stok_menipis
# ---------------------------------------------------------------------------

def flag_stok_menipis(
    stok_saat_ini: float,
    batas_minimum: float,
    days_of_cover: Optional[float] = None,
    config_path: Optional[Path] = None,
) -> dict:
    """
    Penanda stok menipis berdasarkan aturan bisnis eksplisit.
    Tidak menggunakan model ML — ini adalah rule-based check yang cepat
    dan dapat digunakan tanpa memanggil model.

    Parameters
    ----------
    stok_saat_ini  : float  – stok akhir hari ini
    batas_minimum  : float  – ambang minimum SKU
    days_of_cover  : float | None – sisa hari stok (opsional)
    config_path    : Path | None

    Returns
    -------
    {
      "is_menipis"  : bool,
      "is_habis"    : bool,
      "alasan"      : str,
      "saran"       : str,
    }

    Raises
    ------
    PredictInputError : jika nilai negatif atau non-numerik.
    """
    if config_path is None:
        config_path = _DEFAULT_CONFIG

    cfg = _load_config(config_path)
    lr  = cfg["label_rules"]
    doc_thr = lr["days_of_cover_threshold"]

    # Validasi
    for name, val in [("stok_saat_ini", stok_saat_ini), ("batas_minimum", batas_minimum)]:
        if not isinstance(val, (int, float)):
            raise PredictInputError(f"'{name}' harus numerik.")
        if val < 0:
            raise PredictInputError(f"'{name}' tidak boleh negatif (nilai: {val}).")

    stok = float(stok_saat_ini)
    bmin = float(batas_minimum)

    is_habis = stok == 0

    cond_batas = stok <= bmin and stok > 0
    # Catatan: days_of_cover hanya sebagai indikator peringatan tambahan, 
    # namun status menipis standar bisnis ditentukan oleh stok <= batas_minimum.
    # cond_doc dipertahankan untuk backward-compatibility peringatan.
    cond_doc   = (days_of_cover is not None) and (days_of_cover < doc_thr) and (stok > 0)
    is_menipis = (not is_habis) and (cond_batas or cond_doc)

    if is_habis:
        alasan = "Stok mencapai 0 unit."
        saran  = "Segera lakukan resupply atau produksi ulang."
    elif is_menipis:
        alasan_parts = []
        if cond_batas:
            alasan_parts.append(f"Stok ({stok:.0f}) ≤ batas minimum ({bmin:.0f}).")
        if cond_doc:
            alasan_parts.append(f"Days of cover ({days_of_cover:.1f} hari) di bawah ambang ({doc_thr} hari).")
        alasan = " ".join(alasan_parts)
        saran  = f"Pertimbangkan resupply. Stok tersisa untuk ≈{days_of_cover:.1f} hari." \
                 if days_of_cover is not None else "Pertimbangkan resupply segera."
    else:
        alasan = f"Stok ({stok:.0f}) di atas batas minimum ({bmin:.0f})."
        saran  = "Stok aman."

    return {
        "is_menipis": is_menipis,
        "is_habis":   is_habis,
        "alasan":     alasan,
        "saran":      saran,
    }


# ---------------------------------------------------------------------------
# Fungsi baru: classify_stock_status (Rule-Based Murni)
# ---------------------------------------------------------------------------

def classify_stock_status(
    stok_saat_ini: float,
    batas_minimum: float,
    days_of_cover: Optional[float] = None,
    config_path: Optional[Path] = None,
) -> dict:
    """
    Klasifikasi status stok aktual per barang menggunakan aturan bisnis deterministik:
      - 'habis'   : stok_saat_ini <= 0
      - 'menipis' : stok_saat_ini > 0 dan stok_saat_ini <= batas_minimum
      - 'aman'    : stok_saat_ini > batas_minimum

    Days of cover tidak mengubah status aktual, namun jika disertakan akan dicatat
    sebagai indikator tambahan di bagian 'alasan'/'saran'.

    Tidak menggunakan model Machine Learning (.joblib).

    Returns
    -------
    {
      "status":     str   ("aman" | "menipis" | "habis"),
      "is_menipis": bool,
      "is_habis":   bool,
      "alasan":     str,
      "saran":      str,
      "metode":     "rule_based",
    }
    """
    # Validasi input numerik & non-negatif
    for name, val in [("stok_saat_ini", stok_saat_ini), ("batas_minimum", batas_minimum)]:
        if not isinstance(val, (int, float)):
            raise PredictInputError(f"'{name}' harus numerik, bukan {type(val).__name__}.")
        if val < 0:
            raise PredictInputError(f"'{name}' tidak boleh negatif (nilai: {val}).")

    stok = float(stok_saat_ini)
    bmin = float(batas_minimum)

    # Aturan klasifikasi aktual
    if stok <= 0:
        status = "habis"
        is_habis = True
        is_menipis = False
        alasan = "Stok mencapai 0 unit (stok habis)."
        saran = "Segera lakukan resupply atau produksi ulang."
    elif stok <= bmin:
        status = "menipis"
        is_habis = False
        is_menipis = True
        alasan = f"Stok ({stok:.2f} unit) berada di bawah atau sama dengan batas minimum ({bmin:.2f} unit)."
        saran = "Pertimbangkan resupply segera untuk mencegah stok habis."
    else:
        status = "aman"
        is_habis = False
        is_menipis = False
        alasan = f"Stok ({stok:.2f} unit) aman di atas batas minimum ({bmin:.2f} unit)."
        saran = "Stok aman untuk operasional."

    # Tambahan indikator days_of_cover jika ada
    if days_of_cover is not None:
        if not isinstance(days_of_cover, (int, float)) or days_of_cover < 0:
            raise PredictInputError("days_of_cover harus berupa angka non-negatif.")
        if status == "aman" and days_of_cover < 2.0:
            alasan += f" Catatan: Days of cover ({days_of_cover:.1f} hari) mendekati batas ambang perputaran."
            saran = f"Pantau laju penjualan. Estimasi sisa stok untuk ≈{days_of_cover:.1f} hari."

    return {
        "status":     status,
        "is_menipis": is_menipis,
        "is_habis":   is_habis,
        "alasan":     alasan,
        "saran":      saran,
        "metode":     "rule_based",
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # Contoh inferensi
    contoh = {
        "stok_saat_ini":  5.0,
        "batas_minimum":  15.0,
        "barang_masuk":   20.0,
        "barang_keluar":  30.0,
        "avg_keluar_7h":  28.0,
        "days_of_cover":  0.18,
        "rasio_stok":     0.33,
        "total_masuk_7h": 140.0,
        "total_keluar_7h": 196.0,
        "kategori":       "roti_kukus",
        "rasa":           "coklat",
    }

    print("=== Contoh predict_status ===")
    try:
        hasil = predict_status(contoh)
        print(json.dumps(hasil, indent=2, ensure_ascii=False))
    except FileNotFoundError as e:
        print(f"⚠️  {e}")

    print("\n=== Contoh flag_stok_menipis ===")
    flag = flag_stok_menipis(
        stok_saat_ini=5.0,
        batas_minimum=15.0,
        days_of_cover=0.18,
    )
    print(json.dumps(flag, indent=2, ensure_ascii=False))
