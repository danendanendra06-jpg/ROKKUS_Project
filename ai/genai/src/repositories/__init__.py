"""Komponen akses data inventaris (Repository Pattern)."""
from .base import BaseInventoryRepository
from .mock_inventory import MockInventoryRepository

__all__ = ["BaseInventoryRepository", "MockInventoryRepository"]

