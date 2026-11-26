# conftest.py – Konfigurasi pytest untuk ai/ml/
# Tambahkan src/ ke sys.path agar import lintas modul bekerja.

import sys
from pathlib import Path

# Tambahkan src/ ke path
sys.path.insert(0, str(Path(__file__).parent / "src"))
