"""
make_dummy_data.py – Generator Data Sintetis ROKKUS
====================================================
Capstone Asah 2026 | Tim A26-CS159

⚠️  DATA INI ADALAH DATA SINTETIS PLACEHOLDER.
    Dibuat untuk keperluan pengembangan dan pengujian model ML.
    BUKAN data asli UMKM ROKKUS Mardani Raya (data asli bersifat rahasia).

Cara swap ke data asli:
    1. Letakkan file CSV asli di data/ (atau path lain sesuai kesepakatan tim).
    2. Ubah `path_data` di configs/config.yaml ke path CSV tersebut.
    3. Sesuaikan mapping `kolom` di configs/config.yaml jika nama kolom berbeda.
    4. Tidak perlu mengubah kode preprocessing atau training.

Jalankan:
    python src/make_dummy_data.py
    # Output: sample_data/stok_harian.csv
"""

from __future__ import annotations

import argparse
import os
import random
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Seed & Path
# ---------------------------------------------------------------------------
RANDOM_STATE = 42
rng = np.random.default_rng(RANDOM_STATE)
random.seed(RANDOM_STATE)

OUTPUT_DIR = Path(__file__).parent.parent / "sample_data"
OUTPUT_FILE = OUTPUT_DIR / "stok_harian.csv"

# ---------------------------------------------------------------------------
# Katalog produk ROKKUS (representatif, bukan daftar resmi)
# ---------------------------------------------------------------------------
PRODUK = [
    # (id_barang, nama_barang,       kategori,       rasa,           batas_minimum, kapasitas_produksi_harian)
    ("SKU-001", "Roti Kukus Coklat",     "roti_kukus", "coklat",    15, 50),
    ("SKU-002", "Roti Kukus Keju",       "roti_kukus", "keju",      15, 45),
    ("SKU-003", "Roti Kukus Pandan",     "roti_kukus", "pandan",    10, 40),
    ("SKU-004", "Roti Kukus Strawberry", "roti_kukus", "strawberry", 10, 35),
    ("SKU-005", "Roti Kukus Original",   "roti_kukus", "original",  12, 60),
    ("SKU-006", "Roti Bakar Coklat",     "roti_bakar", "coklat",    10, 30),
    ("SKU-007", "Roti Bakar Keju",       "roti_bakar", "keju",      10, 28),
    ("SKU-008", "Roti Bakar Srikaya",    "roti_bakar", "srikaya",    8, 25),
    ("SKU-009", "Roti Bakar Mix",        "roti_bakar", "mix",        8, 20),
    ("SKU-010", "Roti Kukus Kacang",     "roti_kukus", "kacang",    10, 38),
]

# ---------------------------------------------------------------------------
# Parameter simulasi
# ---------------------------------------------------------------------------
START_DATE = date(2025, 1, 1)
END_DATE   = date(2025, 11, 14)   # ~10,5 bulan → data train/test yang cukup


def simulate_stok(start_date: date, end_date: date, produk: list) -> pd.DataFrame:
    """
    Simulasi stok harian per SKU.

    Model sederhana:
      - Setiap hari ada produksi (barang_masuk) ≈ kapasitas × noise
      - Penjualan (barang_keluar) dipengaruhi: hari kerja, weekend boost,
        musim ramadan-lebaran (April), akhir bulan, tren random walk ringan.
      - Sesekali ada kejadian stok habis / over-demand.
    """
    dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

    rows = []
    for sku_id, nama, kategori, rasa, batas_min, kap_harian in produk:
        stok = int(kap_harian * rng.uniform(0.8, 1.2))   # stok awal SKU

        for d in dates:
            # --- faktor permintaan ---
            dow = d.weekday()
            is_weekend = dow >= 5
            weekend_mult = rng.uniform(1.1, 1.4) if is_weekend else 1.0

            # Ramadan/Lebaran simulasi (April): permintaan naik
            ramadan_mult = rng.uniform(1.2, 1.5) if d.month == 4 else 1.0

            # Akhir bulan: permintaan sedikit naik
            eomonth_mult = rng.uniform(1.05, 1.15) if d.day >= 25 else 1.0

            # Noise harian
            noise = rng.uniform(0.7, 1.3)

            permintaan = int(kap_harian * 0.6 * weekend_mult * ramadan_mult * eomonth_mult * noise)
            permintaan = max(0, permintaan)

            # --- produksi (barang masuk) ---
            # Produksi tidak dilakukan saat stok masih tinggi (efisiensi)
            rasio = stok / max(1, kap_harian)
            if rasio > 1.5:
                produksi = 0
            elif rasio > 0.8:
                produksi = int(kap_harian * rng.uniform(0.3, 0.6))
            else:
                produksi = int(kap_harian * rng.uniform(0.7, 1.1))

            stok_awal = max(0, stok)
            barang_masuk = max(0, produksi)
            stok_dengan_masuk = stok_awal + barang_masuk

            # Penjualan tidak melebihi stok yang ada
            barang_keluar = min(permintaan, stok_dengan_masuk)
            stok_akhir = stok_dengan_masuk - barang_keluar

            rows.append({
                "id_barang":    sku_id,
                "nama_barang":  nama,
                "kategori":     kategori,
                "rasa":         rasa,
                "tanggal":      d.isoformat(),
                "stok_awal":    stok_awal,
                "barang_masuk": barang_masuk,
                "barang_keluar": barang_keluar,
                "stok_akhir":   stok_akhir,
                "batas_minimum": batas_min,
            })

            stok = stok_akhir   # carry forward

    df = pd.DataFrame(rows)
    df["tanggal"] = pd.to_datetime(df["tanggal"])
    df = df.sort_values(["tanggal", "id_barang"]).reset_index(drop=True)
    return df


def main(output_path: Path = OUTPUT_FILE) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("⏳ Membuat data sintetis ROKKUS …")
    df = simulate_stok(START_DATE, END_DATE, PRODUK)

    df.to_csv(output_path, index=False)

    n_rows = len(df)
    n_sku  = df["id_barang"].nunique()
    n_days = df["tanggal"].nunique()

    print(f"✅ Data tersimpan → {output_path}")
    print(f"   {n_rows:,} baris | {n_sku} SKU | {n_days} hari")
    print(f"   Rentang: {df['tanggal'].min().date()} s/d {df['tanggal'].max().date()}")
    print()
    print("Distribusi status stok (aturan sederhana untuk referensi):")
    habis   = (df["stok_akhir"] == 0).sum()
    menipis = ((df["stok_akhir"] > 0) & (df["stok_akhir"] <= df["batas_minimum"])).sum()
    aman    = len(df) - habis - menipis
    total   = len(df)
    print(f"   aman    : {aman:,} ({aman/total*100:.1f}%)")
    print(f"   menipis : {menipis:,} ({menipis/total*100:.1f}%)")
    print(f"   habis   : {habis:,} ({habis/total*100:.1f}%)")
    print()
    print("Kolom:", list(df.columns))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate data sintetis ROKKUS")
    parser.add_argument(
        "--output", type=Path, default=OUTPUT_FILE,
        help=f"Path output CSV (default: {OUTPUT_FILE})"
    )
    args = parser.parse_args()
    main(args.output)
