"""Adapter untuk membaca dataset Data Science ROKKUS (read-only) dan
mengonversinya ke schema DailyStockSummaryRequest modul GenAI.

CATATAN PENTING:
- Adapter ini bersifat READ-ONLY: tidak memodifikasi, menyalin, atau
  merestrukturisasi file milik tim Data Science.
- Path CSV dapat dikonfigurasi melalui parameter atau environment variable
  DS_DATASET_PATH untuk fleksibilitas lintas environment.
- Dataset yang dibaca adalah DATA SINTETIS (September 2026) yang dibuat
  oleh tim Data Science untuk keperluan prototipe. BUKAN data operasional
  nyata UMKM ROKKUS Mardani Raya.
- Metadata is_synthetic=True dan source="ds_synthetic_dataset_sept2026"
  disertakan pada setiap request yang dihasilkan adapter ini.

Kolom CSV yang dipetakan:
  product_id   → items[].id
  product_name → items[].name
  category     → items[].category
  stok_akhir   → items[].current_stock
  tanggal_stok → date (request root)

Default nilai yang disisipkan (tidak ada di CSV):
  minimum_stock = 5.0  (threshold absolut Low/Safe yang digunakan tim DS)
  unit          = "porsi" (produk jadi menu roti kukus ROKKUS)
"""

from __future__ import annotations

import csv
import os
from datetime import date as date_type
from pathlib import Path
from typing import List, Optional

from ..schemas.summary import DailyStockItemInput, DailyStockSummaryRequest

# Path default: data-science/data/processed/dataset_stok_rokkus_final.csv
# relatif terhadap root repository (dua level di atas ai/genai/)
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
_DEFAULT_DS_CSV = (
    _REPO_ROOT
    / "data-science"
    / "data"
    / "processed"
    / "dataset_stok_rokkus_final.csv"
)

# Nilai default yang disisipkan adapter karena tidak ada di CSV tim DS
DEFAULT_MINIMUM_STOCK: float = 5.0
DEFAULT_UNIT: str = "porsi"
DEFAULT_STORE_NAME: str = "UMKM ROKKUS Mardani Raya"

# Penanda metadata sumber data sintetis
DS_DATA_SOURCE: str = "ds_synthetic_dataset_sept2026"
DS_DISCLAIMER: str = (
    "PERINGATAN: Data berasal dari dataset sintetis tim Data Science ROKKUS "
    "(September 2026) untuk keperluan prototipe. BUKAN data operasional nyata UMKM."
)


class DSDatasetAdapter:
    """Adapter read-only untuk dataset Data Science → DailyStockSummaryRequest.

    Membaca `dataset_stok_rokkus_final.csv` dari path yang dapat dikonfigurasi
    dan mengonversinya menjadi payload request valid untuk endpoint
    POST /api/v1/summary/daily.

    Args:
        csv_path: Path absolut atau relatif ke file CSV. Jika None, dibaca dari
            environment variable DS_DATASET_PATH, atau menggunakan path default
            relatif terhadap root repository.
        minimum_stock: Nilai minimum_stock default yang disisipkan untuk semua item.
            Dapat di-override per item di masa depan.
        unit: Satuan unit default untuk item yang tidak memiliki kolom unit di CSV.
        store_name: Nama gerai yang digunakan pada request.
    """

    def __init__(
        self,
        csv_path: Optional[str | Path] = None,
        minimum_stock: float = DEFAULT_MINIMUM_STOCK,
        unit: str = DEFAULT_UNIT,
        store_name: str = DEFAULT_STORE_NAME,
    ):
        if csv_path is not None:
            self.csv_path = Path(csv_path)
            self._is_custom_path = True
        else:
            env_path = os.environ.get("DS_DATASET_PATH")
            self.csv_path = Path(env_path) if env_path else _DEFAULT_DS_CSV
            self._is_custom_path = False

        self.minimum_stock = minimum_stock
        self.unit = unit
        self.store_name = store_name

    def _read_csv_content(self) -> str:
        """Membaca isi CSV dari filesystem lokal, atau fallback ke origin/main via git show.

        Memungkinkan pembacaan dataset Data Science secara read-only langsung dari
        origin/main jika menggunakan path default dan branch belum di-merge.
        """
        if self.csv_path.exists():
            return self.csv_path.read_text(encoding="utf-8")

        # Fallback ke git show origin/main HANYA jika menggunakan path default
        if not self._is_custom_path:
            import subprocess
            git_ref = "origin/main:data-science/data/processed/dataset_stok_rokkus_final.csv"
            try:
                res = subprocess.run(
                    ["git", "show", git_ref],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    check=False,
                )
                if res.returncode == 0 and res.stdout.strip():
                    return res.stdout
            except Exception:
                pass

        raise FileNotFoundError(
            f"[DSDatasetAdapter] File CSV dataset Data Science tidak ditemukan di disk: "
            f"{self.csv_path}.\n"
            f"Pastikan path sudah benar atau atur environment variable DS_DATASET_PATH."
        )

    def load_request(
        self,
        target_date: Optional[date_type] = None,
    ) -> DailyStockSummaryRequest:
        """Membaca CSV dan menghasilkan DailyStockSummaryRequest untuk tanggal tertentu.

        Args:
            target_date: Filter baris berdasarkan kolom `tanggal_stok`.
                Jika None, menggunakan tanggal pertama yang ditemukan di CSV.

        Returns:
            DailyStockSummaryRequest: Payload siap kirim ke POST /api/v1/summary/daily.

        Raises:
            FileNotFoundError: Jika file CSV tidak ditemukan di disk maupun git remote.
            ValueError: Jika tidak ada baris data yang cocok atau CSV tidak valid.
        """
        import io
        csv_text = self._read_csv_content()
        rows = []

        reader = csv.DictReader(io.StringIO(csv_text))
        for row in reader:
            rows.append(row)

        if not rows:
            raise ValueError(
                f"[DSDatasetAdapter] File CSV kosong atau tidak memiliki baris data."
            )

        # Tentukan tanggal target
        if target_date is None:
            first_date_str = rows[0].get("tanggal_stok", "").strip()
            if not first_date_str:
                raise ValueError(
                    "[DSDatasetAdapter] Kolom 'tanggal_stok' tidak ditemukan atau kosong di baris pertama."
                )
            target_date = date_type.fromisoformat(first_date_str)

        target_date_str = target_date.isoformat()

        # Filter baris berdasarkan tanggal
        filtered = [
            r for r in rows
            if r.get("tanggal_stok", "").strip() == target_date_str
        ]

        if not filtered:
            raise ValueError(
                f"[DSDatasetAdapter] Tidak ada baris data untuk tanggal '{target_date_str}' "
                f"di dataset CSV ({self.csv_path})."
            )

        # Konversi baris CSV ke DailyStockItemInput
        items: List[DailyStockItemInput] = []
        for row in filtered:
            product_id = row.get("product_id", "").strip() or None
            product_name = row.get("product_name", "").strip()
            category = row.get("category", "produk_jadi").strip() or "produk_jadi"
            stok_akhir_str = row.get("stok_akhir", "0").strip()

            if not product_name:
                continue  # Lewati baris tanpa nama produk

            try:
                current_stock = float(stok_akhir_str)
            except (ValueError, TypeError):
                current_stock = 0.0

            items.append(
                DailyStockItemInput(
                    id=product_id,
                    name=product_name,
                    category=category,
                    current_stock=current_stock,
                    minimum_stock=self.minimum_stock,
                    unit=self.unit,
                )
            )

        if not items:
            raise ValueError(
                f"[DSDatasetAdapter] Tidak ada item valid yang dapat dimuat dari tanggal '{target_date_str}'."
            )

        return DailyStockSummaryRequest(
            date=target_date,
            store_name=self.store_name,
            items=items,
        )

    def get_available_dates(self) -> List[date_type]:
        """Membaca semua tanggal unik yang tersedia di CSV.

        Returns:
            List[date_type]: Daftar tanggal unik terurut dari CSV.
        """
        import io
        csv_text = self._read_csv_content()
        seen: set = set()
        dates: List[date_type] = []

        reader = csv.DictReader(io.StringIO(csv_text))
        for row in reader:
            date_str = row.get("tanggal_stok", "").strip()
            if date_str and date_str not in seen:
                seen.add(date_str)
                try:
                    dates.append(date_type.fromisoformat(date_str))
                except ValueError:
                    pass

        return sorted(dates)

    @property
    def metadata(self) -> dict:
        """Metadata yang harus disertakan saat menggunakan data dari adapter ini."""
        return {
            "is_synthetic": True,
            "source": DS_DATA_SOURCE,
            "disclaimer": DS_DISCLAIMER,
            "csv_path": str(self.csv_path),
            "default_minimum_stock": self.minimum_stock,
            "default_unit": self.unit,
        }
