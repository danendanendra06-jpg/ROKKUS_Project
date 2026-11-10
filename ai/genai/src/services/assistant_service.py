"""Orchestrator utama untuk memadukan konteks inventaris dengan engine LLM."""

from typing import List, Optional

from .llm_base import BaseLLMService
from ..repositories.base import BaseInventoryRepository
from ..schemas.chat import ChatRequest, ChatResponse, AssistantMessage
from ..schemas.inventory import InventoryItem


class AssistantService:
    """Layanan orkestrasi asisten inventaris (Application Service).

    Bertanggung jawab:
    1. Mengambil data inventaris yang relevan sesuai filter permintaan.
    2. Menyuntikkan konteks data ke LLM Service.
    3. Mengembalikan respons percakapan terpadu.
    """

    def __init__(
        self,
        repository: BaseInventoryRepository,
        llm_service: BaseLLMService,
    ):
        self.repository = repository
        self.llm_service = llm_service

    def _retrieve_context(self, request: ChatRequest) -> List[InventoryItem]:
        """Mengambil dan memfilter item inventaris sebagai basis konteks."""
        items = self.repository.get_all_items()

        # Filter kategori jika ada
        if request.category_filter:
            target_cat = request.category_filter.strip().lower()
            items = [i for i in items if i.category.strip().lower() == target_cat]

        # Filter status jika ada
        if request.status_filter:
            items = [i for i in items if i.status == request.status_filter]

        return items

    async def handle_chat(self, request: ChatRequest) -> ChatResponse:
        """Memproses permintaan chat pengguna secara menyeluruh."""
        snapshot = self.repository.get_snapshot()
        store_name = snapshot.store.name

        # 1. Retrieval context
        context_items = self._retrieve_context(request)

        # 2. LLM response generation
        assistant_message: AssistantMessage = await self.llm_service.generate_response(
            user_query=request.message,
            context_items=context_items,
            store_name=store_name,
            category_hint=request.category_filter,
        )

        return ChatResponse(
            status="success",
            data=assistant_message,
        )

