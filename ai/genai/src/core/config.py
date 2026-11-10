"""Pengaturan konfigurasi aplikasi menggunakan environment variables."""

import os
from pathlib import Path
from typing import Literal

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict

    class Settings(BaseSettings):
        """Konfigurasi utama layanan ROKKUS AI Inventory Assistant."""
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore",
        )

        APP_NAME: str = "ROKKUS AI Inventory Assistant"
        APP_VERSION: str = "0.1.0"
        ENVIRONMENT: str = "development"
        HOST: str = "127.0.0.1"
        PORT: int = 8001

        # Provider LLM: 'mock' (tahap ini) atau 'gemini' (masa depan)
        LLM_PROVIDER: Literal["mock", "gemini"] = "mock"

        # Path file data inventaris sintetis
        INVENTORY_DATA_PATH: str = "data/synthetic_inventory.json"

        # Gemini API (Masa depan)
        GEMINI_API_KEY: str | None = None
        GEMINI_MODEL_NAME: str = "gemini-1.5-flash"

except ImportError:  # pragma: no cover
    # Fallback jika pydantic-settings belum terinstal
    class Settings:  # type: ignore[no-redef]
        """Fallback konfigurasi sederhana jika pydantic-settings belum diinstal."""
        APP_NAME: str = os.getenv("APP_NAME", "ROKKUS AI Inventory Assistant")
        APP_VERSION: str = os.getenv("APP_VERSION", "0.1.0")
        ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
        HOST: str = os.getenv("HOST", "127.0.0.1")
        PORT: int = int(os.getenv("PORT", "8001"))
        LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "mock")
        INVENTORY_DATA_PATH: str = os.getenv(
            "INVENTORY_DATA_PATH", "data/synthetic_inventory.json"
        )
        GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY", None)
        GEMINI_MODEL_NAME: str = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")


settings = Settings()


def resolve_inventory_path(raw_path: str | None = None) -> Path:
    """Mencari path absolut file dataset sintetis secara andal.

    Mendukung penemuan file baik dijalankan dari root repositori maupun
    dari dalam direktori ai/genai/.
    """
    target = raw_path or settings.INVENTORY_DATA_PATH
    p = Path(target)
    if p.is_absolute() and p.exists():
        return p

    # Coba relatif terhadap direktori modul (ai/genai)
    module_dir = Path(__file__).resolve().parent.parent.parent
    candidate_1 = module_dir / target
    if candidate_1.exists():
        return candidate_1

    # Coba relatif terhadap working directory saat ini
    candidate_2 = Path.cwd() / target
    if candidate_2.exists():
        return candidate_2

    # Coba path default data/synthetic_inventory.json di dalam module_dir
    candidate_3 = module_dir / "data" / "synthetic_inventory.json"
    if candidate_3.exists():
        return candidate_3

    # Kembalikan path kandidat 1 jika belum ada
    return candidate_1

