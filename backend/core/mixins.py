"""
Model Mixins for Trendyol Profitability SaaS

Reusable model mixins for common functionality.
"""

from django.db import models


class TimestampMixin(models.Model):
    """
    Adds created_at and updated_at timestamp fields.
    """
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Oluşturulma Tarihi')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Güncellenme Tarihi')
    
    class Meta:
        abstract = True


class SoftDeleteMixin(models.Model):
    """
    Adds soft delete functionality.
    Records are marked as deleted instead of being removed from database.
    """
    is_deleted = models.BooleanField(default=False, verbose_name='Silindi')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='Silinme Tarihi')
    
    class Meta:
        abstract = True
    
    def soft_delete(self):
        """Mark the record as deleted."""
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])
    
    def restore(self):
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])


class UserOwnedMixin(models.Model):
    """
    Mixin for models that belong to a specific user.
    Provides tenant isolation at the model level.
    """
    # Note: This requires the User model to be imported in the implementing model
    # user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    
    class Meta:
        abstract = True


class AuditMixin(TimestampMixin):
    """
    Extended audit mixin that tracks who created/modified records.
    """
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created',
        verbose_name='Oluşturan'
    )
    updated_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated',
        verbose_name='Güncelleyen'
    )
    
    class Meta:
        abstract = True
