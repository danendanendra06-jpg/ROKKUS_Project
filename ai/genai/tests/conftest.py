"""Konfigurasi fixture pytest dan path import sistem."""

import os
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

from src.core.config import settings


@pytest.fixture(autouse=True)
def isolate_test_environment(monkeypatch):
    """Isolasi environment pengujian agar selalu menggunakan mode mock dan tidak memanggil API live."""
    monkeypatch.setattr(settings, "LLM_PROVIDER", "mock")
    monkeypatch.setattr(settings, "ENVIRONMENT", "testing")
    yield


@pytest.fixture
def sample_inventory_file():
    """Mengembalikan path file data inventaris sintetis."""
    return BASE_DIR / "data" / "synthetic_inventory.json"

