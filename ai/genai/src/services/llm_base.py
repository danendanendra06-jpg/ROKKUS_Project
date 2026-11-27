"""Interface abstrak untuk penyedia kecerdasan buatan (LLM Provider)."""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..schemas.chat import AssistantMessage
from ..schemas.inventory import InventoryItem


class BaseLLMService(ABC):
    """Kontrak dasar layanan LLM (Mock atau Gemini).

    Memungkinkan controller API tetap netral terhadap provider yang digunakan.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Nama identitas provider (misal: 'mock' atau 'gemini')."""
        pass

    @abstractmethod
    async def generate_response(
        self,
        user_query: str,
        context_items: List[InventoryItem],
        store_name: str,
        category_hint: Optional[str] = None,
    ) -> AssistantMessage:
        """Menghasilkan respon berbasis konteks inventaris.

        Args:
            user_query: Pertanyaan pengguna.
            context_items: Daftar item inventaris relevan hasil retrieval.
            store_name: Nama toko/unit usaha.
            category_hint: Petunjuk kategori yang diminta jika ada.

        Returns:
            AssistantMessage: Objek jawaban terstruktur dan metadata.
        """
        pass

