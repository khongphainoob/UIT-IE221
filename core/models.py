"""
Abstract BaseModel for all domain entities in the Student Expense Analytics API.
Provides UUIDv4 primary key, audit timestamps, and soft-delete mechanism.
"""
import uuid
from django.db import models


class ActiveRecordQuerySet(models.QuerySet):
    """Custom QuerySet supporting soft delete filtering."""

    def active(self):
        return self.filter(is_deleted=False)

    def soft_delete(self):
        return self.update(is_deleted=True)


class ActiveRecordManager(models.Manager):
    """Default Manager returning only non-deleted records unless explicitly requested."""

    def get_queryset(self):
        return ActiveRecordQuerySet(self.model, using=self._db).filter(is_deleted=False)


class BaseModel(models.Model):
    """
    Abstract base model that all domain models must inherit from (OOP Principle).
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Định danh duy nhất chuẩn UUIDv4",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Thời điểm khởi tạo bản ghi",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Thời điểm cập nhật bản ghi gần nhất",
    )
    is_deleted = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Cờ đánh dấu xóa mềm (Soft Delete)",
    )

    objects = ActiveRecordManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def soft_delete(self, using=None):
        """Perform soft deletion instead of physical SQL DELETE."""
        self.is_deleted = True
        self.save(update_fields=["is_deleted", "updated_at"], using=using)

    def restore(self, using=None):
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.save(update_fields=["is_deleted", "updated_at"], using=using)


# Alias tương thích 1:1 với Sơ đồ lớp StarUML (Mục 2 - Kế thừa)
TimeStampedSoftDeleteModel = BaseModel


