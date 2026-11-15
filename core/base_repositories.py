"""
Re-export BaseRepository so modules can import from either `core.base_repositories` or `core.repositories`.
"""
from core.repositories import BaseRepository

__all__ = ["BaseRepository"]
