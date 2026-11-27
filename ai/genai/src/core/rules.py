"""Definisi dan dokumentasi aturan konsisten status stok ROKKUS.

Aturan klasifikasi stok (Tahap 5 — diselaraskan dengan dataset Data Science):

1. EMPTY:
   - Kondisi: current_stock == 0
   - Penjelasan: Stok barang telah habis sepenuhnya.
   - Tindakan: Memerlukan pengadaan ulang darurat segera.

2. LOW:
   - Kondisi: 0 < current_stock <= 5
   - Penjelasan: Stok barang menipis dan mendekati batas kritis.
   - Tindakan: Jadwalkan restock dalam waktu dekat dan pantau pergerakan harian.

3. SAFE:
   - Kondisi: current_stock > 5
   - Penjelasan: Stok barang mencukupi untuk operasional harian.
   - Tindakan: Pertahankan rotasi FIFO dan lanjutkan pencatatan rutin.

CATATAN KOMPATIBILITAS API:
   Parameter `minimum_stock` tetap diterima pada request API untuk kompatibilitas
   dan integrasi masa depan (misalnya model ML Husain yang menggunakan batas_minimum
   sebagai fitur). Namun, penentuan status stok saat ini menggunakan threshold
   absolut tetap (0 dan 5), bukan rasio terhadap minimum_stock.

PENYELARASAN TIM:
   Label EMPTY / LOW / SAFE selaras dengan dataset tim Data Science
   pada `data-science/data/processed/dataset_stok_rokkus_final.csv`
   (origin/main) yang menggunakan threshold absolut yang sama.
"""

from enum import Enum

# Threshold absolut untuk klasifikasi status stok (selaras dengan dataset DS)
STOCK_THRESHOLD_EMPTY: float = 0    # stok == 0  → EMPTY
STOCK_THRESHOLD_LOW: float = 5      # 0 < stok <= 5 → LOW; stok > 5 → SAFE


class StockStatus(str, Enum):
    """Enumerasi status tingkat ketersediaan stok barang.

    Nilai diselaraskan dengan label dataset Data Science ROKKUS:
    - EMPTY: stok habis (== 0)
    - LOW:   stok menipis (0 < stok <= 5)
    - SAFE:  stok aman (> 5)
    """
    SAFE  = "SAFE"
    LOW   = "LOW"
    EMPTY = "EMPTY"


STOCK_STATUS_DESCRIPTIONS = {
    StockStatus.EMPTY: (
        "Stok habis (current_stock == 0). Butuh pengadaan ulang darurat segera."
    ),
    StockStatus.LOW: (
        "Stok menipis (0 < current_stock <= 5). Jadwalkan restock dan pantau pergerakan harian."
    ),
    StockStatus.SAFE: (
        "Stok aman (current_stock > 5). Pertahankan rotasi FIFO dan pencatatan rutin."
    ),
}


def evaluate_stock_status(current_stock: float, minimum_stock: float = 0.0) -> StockStatus:
    """Mengevaluasi dan menentukan status stok secara deterministik.

    Menggunakan threshold absolut tetap yang diselaraskan dengan dataset
    Data Science ROKKUS (origin/main).

    Args:
        current_stock: Jumlah stok saat ini (harus non-negatif, >= 0).
        minimum_stock: Disediakan untuk kompatibilitas kontrak API dan integrasi
            masa depan (misalnya fitur model ML). Saat ini TIDAK digunakan untuk
            menentukan status — status ditentukan oleh threshold absolut:
            0 → EMPTY, 1–5 → LOW, >5 → SAFE.

    Returns:
        StockStatus: Nilai status EMPTY, LOW, atau SAFE.
    """
    if current_stock <= STOCK_THRESHOLD_EMPTY:
        return StockStatus.EMPTY
    elif current_stock <= STOCK_THRESHOLD_LOW:
        return StockStatus.LOW
    else:
        return StockStatus.SAFE

