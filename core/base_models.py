"""
Re-export BaseModel, TimeStampedSoftDeleteModel, ActiveRecordManager, and ActiveRecordQuerySet
so modules can import from either `core.base_models` or `core.models`.
"""
from core.models import (
    ActiveRecordManager,
    ActiveRecordQuerySet,
    BaseModel,
    TimeStampedSoftDeleteModel,
)

__all__ = [
    "BaseModel",
    "TimeStampedSoftDeleteModel",
    "ActiveRecordManager",
    "ActiveRecordQuerySet",
]
