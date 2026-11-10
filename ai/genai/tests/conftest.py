"""Konfigurasi fixture pytest dan path import sistem."""

import sys
from pathlib import Path
import pytest

# Pastikan path modul ai/genai dan ai/genai/src terdaftar di sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


@pytest.fixture
def sample_inventory_file():
    """Mengembalikan path file data inventaris sintetis."""
    return BASE_DIR / "data" / "synthetic_inventory.json"

