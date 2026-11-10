"""
Generic BaseRepository implementing the Repository Pattern over Django ORM.
Decouples business services from direct QuerySet manipulation.
"""
from typing import Any, Dict, Generic, Optional, Type, TypeVar
from uuid import UUID
from django.db.models import QuerySet
from core.exceptions import ResourceNotFoundException
from core.models import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseRepository(Generic[T]):
    """
    Generic Data Access Layer (DAL) with Soft-Delete awareness.
    Subclasses must specify `model_class`.
    """

    model_class: Type[T]

    def __init__(self, model_class: Optional[Type[T]] = None):
        if model_class is not None:
            self.model_class = model_class
        if not getattr(self, "model_class", None):
            raise ValueError(f"{self.__class__.__name__} must define `model_class`.")

    def get_queryset(self) -> QuerySet[T]:
        """Return active (non-deleted) records queryset."""
        return self.model_class.objects.filter(is_deleted=False)

    def list_all(self, **filters: Any) -> QuerySet[T]:
        """Filter active records by keyword arguments."""
        return self.get_queryset().filter(**filters)

    def filter_active(self, **filters: Any) -> QuerySet[T]:
        """Alias chuẩn StarUML (`filter_active`) để lọc các bản ghi chưa bị xóa mềm."""
        return self.list_all(**filters)

    def get_by_id(self, record_id: UUID | str, **extra_filters: Any) -> T:
        """Retrieve a single active record by UUID or raise ResourceNotFoundException."""
        try:
            return self.get_queryset().get(id=record_id, **extra_filters)
        except self.model_class.DoesNotExist as exc:
            raise ResourceNotFoundException(
                f"Không tìm thấy {self.model_class.__name__} với ID={record_id}."
            ) from exc

    def find_by_id(self, record_id: UUID | str, **extra_filters: Any) -> Optional[T]:
        """Retrieve a single active record by UUID or return None."""
        return self.get_queryset().filter(id=record_id, **extra_filters).first()

    def create(self, **data: Any) -> T:
        """Instantiate and persist a new model record."""
        instance = self.model_class(**data)
        instance.full_clean()
        instance.save()
        return instance

    def update(self, instance: T, **data: Any) -> T:
        """Update fields on an existing model instance."""
        for attr, value in data.items():
            setattr(instance, attr, value)
        instance.full_clean()
        instance.save()
        return instance

    def soft_delete(self, instance: T) -> T:
        """Mark an existing instance as soft-deleted."""
        instance.soft_delete()
        return instance

