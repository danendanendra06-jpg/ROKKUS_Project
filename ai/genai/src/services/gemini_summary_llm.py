"""Layanan Gemini LLM resmi menggunakan Google Gen AI SDK (google-genai)."""

import asyncio
import logging
from typing import Any, Dict, Optional

try:
    from google import genai
    from google.genai import types
    GENAI_SDK_AVAILABLE = True
except ImportError:  # pragma: no cover
    genai = None
    types = None
    GENAI_SDK_AVAILABLE = False

from .summary_llm import BaseSummaryLLMService
from ..core.config import settings

logger = logging.getLogger(__name__)


class GeminiSummaryLLMService(BaseSummaryLLMService):
    """Implementasi layanan LLM resmi menggunakan Google Gen AI SDK dengan asynchronous API.

    Fitur:
    - Konfigurasi model dinamis via GEMINI_MODEL_NAME (default: gemini-2.5-flash).
    - Asynchronous generation via client.aio.models.generate_content.
    - Timeout terproteksi dan error handling terstruktur.
    - Output paksa JSON terstruktur via response_mime_type='application/json'.
    - Dukungan injeksi mock client untuk pengujian automated testing tanpa API key sungguhan.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        client: Optional[Any] = None,
    ):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or settings.GEMINI_MODEL_NAME or "gemini-2.5-flash"
        self.timeout_seconds = (
            timeout_seconds
            if timeout_seconds is not None
            else getattr(settings, "GEMINI_TIMEOUT_SECONDS", 10.0)
        )

        if client is not None:
            # Client diinjeksi secara eksplisit (terutama untuk unit testing)
            self.client = client
        else:
            if not GENAI_SDK_AVAILABLE:
                raise ImportError(
                    "Paket 'google-genai' belum terinstal. Jalankan 'pip install google-genai'."
                )
            if not self.api_key:
                raise ValueError(
                    "GEMINI_API_KEY wajib dikonfigurasi di environment (.env) untuk menggunakan Gemini."
                )

            # Konfigurasi batas waktu HTTP dan pembatasan retry bawaan SDK
            http_options = None
            if hasattr(types, "HttpOptions"):
                retry_options = None
                if hasattr(types, "HttpRetryOptions"):
                    # Nonaktifkan retry loop bawaan (cukup 1 percobaan) agar 503/429
                    # langsung memicu fallback deterministik tanpa memakan waktu puluhan detik
                    retry_options = types.HttpRetryOptions(attempts=1)

                timeout_ms = max(1000, int(self.timeout_seconds * 1000))
                http_options = types.HttpOptions(
                    timeout=timeout_ms,
                    retry_options=retry_options,
                )

            if http_options is not None:
                self.client = genai.Client(api_key=self.api_key, http_options=http_options)
            else:
                self.client = genai.Client(api_key=self.api_key)

    @property
    def provider_name(self) -> str:
        """Mengembalikan nama model Gemini aktif (misal 'gemini-2.5-flash')."""
        return self.model_name

    async def generate_summary_json(
        self,
        system_prompt: str,
        user_prompt: str,
        valid_item_refs: Dict[str, Any],
        context: Dict[str, Any],
    ) -> str:
        """Menghasilkan respon ringkasan JSON terstruktur secara asinkron dari Gemini API."""
        try:
            # Konfigurasi parameter generasi
            config_kwargs: Dict[str, Any] = {
                "system_instruction": system_prompt,
                "response_mime_type": "application/json",
                "temperature": 0.2,
            }

            if types is not None:
                config = types.GenerateContentConfig(**config_kwargs)
            else:  # Fallback untuk mock client di test environment
                config = config_kwargs

            # Pemanggilan asinkron ke Gemini API dengan timeout
            coroutine = self.client.aio.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
                config=config,
            )

            response = await asyncio.wait_for(coroutine, timeout=self.timeout_seconds)

            if not response or not hasattr(response, "text") or not response.text:
                raise ValueError("Respon dari Gemini API kosong atau tidak memiliki atribut text.")

            return response.text

        except asyncio.TimeoutError:
            err_msg = f"Panggilan Gemini API timeout setelah {self.timeout_seconds} detik."
            logger.error(err_msg)
            raise TimeoutError(err_msg)
        except Exception as e:
            err_msg = f"Gagal mengeksekusi Gemini API ({self.model_name}): {str(e)}"
            logger.error(err_msg)
            raise RuntimeError(err_msg) from e
