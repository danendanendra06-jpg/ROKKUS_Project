"""Definisi dan dokumentasi aturan konsisten status stok ROKKUS.

Aturan klasifikasi stok:
1. CRITICAL:
   - Kondisi: current_stock <= minimum_stock
   - Penjelasan: Stok barang telah mencapai atau berada di bawah ambang batas minimum.
   - Tindakan: Memerlukan restock segera untuk mencegah terhentinya aktivitas produksi/penjualan.

2. WARNING:
   - Kondisi: minimum_stock < current_stock <= (minimum_stock * 1.5)
   - Penjelasan: Stok barang berada di atas ambang minimum namun dalam zona waspada (di bawah atau sama dengan 150% batas minimum).
   - Tindakan: Perlu dipantau dan dipersiapkan jadwal pemesanan ulang ke supplier.

3. SAFE:
   - Kondisi: current_stock > (minimum_stock * 1.5)
   - Penjelasan: Stok barang melampaui 150% ambang minimum.
   - Tindakan: Stok berada dalam kondisi aman untuk operasional harian.
"""

from enum import Enum


class StockStatus(str, Enum):
    """Enumerasi status tingkat ketersediaan stok barang."""
    SAFE = "SAFE"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


STOCK_STATUS_DESCRIPTIONS = {
    StockStatus.CRITICAL: (
        "Stok sama atau di bawah batas minimum (current <= min). Butuh restock darurat."
    ),
    StockStatus.WARNING: (
        "Stok mendekati batas minimum (min < current <= min * 1.5). Pantau & rencanakan restock."
    ),
    StockStatus.SAFE: (
        "Stok mencukupi untuk operasional (current > min * 1.5). Kondisi aman."
    ),
}


def evaluate_stock_status(current_stock: float, minimum_stock: float) -> StockStatus:
    """Mengevaluasi dan menentukan status stok secara konsisten.

    Args:
        current_stock: Jumlah stok saat ini (harus non-negatif).
        minimum_stock: Ambang batas minimum stok yang ditentukan.

    Returns:
        StockStatus: Nilai status SAFE, WARNING, atau CRITICAL.
    """
    if current_stock <= minimum_stock:
        return StockStatus.CRITICAL
    elif current_stock <= (minimum_stock * 1.5):
        return StockStatus.WARNING
    else:
        return StockStatus.SAFE

