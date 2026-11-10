"""Router agregasi untuk seluruh endpoint API v1."""

from fastapi import APIRouter

from .endpoints import chat, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(chat.router)

