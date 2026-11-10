"""Endpoint untuk interaksi AI Inventory Assistant."""

from fastapi import APIRouter, Depends, HTTPException, status

from ....repositories.mock_inventory import MockInventoryRepository
from ....services.assistant_service import AssistantService
from ....services.mock_llm import MockLLMService
from ....schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/assistant", tags=["Assistant"])


def get_assistant_service() -> AssistantService:
    """Dependency provider untuk AssistantService dengan Mock implementation.

    Desain modular ini memungkinkan penggantian MockLLMService dengan
    GeminiLLMService di masa depan tanpa memodifikasi endpoint.
    """
    repo = MockInventoryRepository()
    llm = MockLLMService()
    return AssistantService(repository=repo, llm_service=llm)


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Interaksi percakapan dengan AI Inventory Assistant",
    description=(
        "Menerima pertanyaan seputar stok operasional UMKM ROKKUS dan mengembalikan "
        "rekomendasi berbasis data inventaris. Pada tahap prototipe ini, respons "
        "dihasilkan oleh MockLLMService dengan provider bernilai 'mock'."
    ),
)
async def chat_with_assistant(
    request: ChatRequest,
    service: AssistantService = Depends(get_assistant_service),
) -> ChatResponse:
    """Memproses pesan pengguna dan menghasilkan rekomendasi stok."""
    try:
        return await service.handle_chat(request)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Kesalahan data internal: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan saat memproses permintaan AI: {str(e)}",
        )

