"""
Sellers App - Models

Trendyol seller account models with encrypted API credentials.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from core.mixins import TimestampMixin
from core.encryption import encrypt_credential, decrypt_credential
from core.validators import validate_trendyol_seller_id, validate_api_key


class SellerAccount(TimestampMixin, models.Model):
    """
    Trendyol seller account linked to a user.
    
    Users can have multiple seller accounts.
    API credentials are stored encrypted.
    """
    
    SYNC_STATUS_CHOICES = [
        ('idle', 'Beklemede'),
        ('syncing', 'Senkronize Ediliyor'),
        ('completed', 'Tamamlandı'),
        ('error', 'Hata'),
    ]
    
    # Owner
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='seller_accounts',
        verbose_name=_('Kullanıcı')
    )
    
    # Trendyol credentials
    seller_id = models.CharField(
        _('Satıcı ID'),
        max_length=100,
        validators=[validate_trendyol_seller_id],
        help_text=_('Trendyol Satıcı Panel\'den alınan Satıcı ID')
    )
    api_key = models.TextField(
        _('API Anahtarı'),
        help_text=_('Trendyol API anahtarı (şifreli saklanır)')
    )
    api_secret = models.TextField(
        _('API Secret'),
        help_text=_('Trendyol API secret (şifreli saklanır)')
    )
    
    # Shop info
    shop_name = models.CharField(
        _('Mağaza Adı'),
        max_length=255
    )
    shop_url = models.URLField(
        _('Mağaza URL'),
        blank=True
    )
    
    # Default rates for this seller
    default_commission_rate = models.DecimalField(
        _('Varsayılan Komisyon Oranı'),
        max_digits=5,
        decimal_places=2,
        default=12.00,
        help_text=_('Kategori bazlı oran yoksa kullanılacak varsayılan komisyon (%)')
    )
    default_cargo_cost = models.DecimalField(
        _('Varsayılan Kargo Maliyeti'),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_('Varsayılan kargo maliyeti (KDV hariç, TL)')
    )
    
    # Status
    is_active = models.BooleanField(
        _('Aktif'),
        default=True
    )
    
    # Sync tracking
    sync_status = models.CharField(
        _('Senkronizasyon Durumu'),
        max_length=20,
        choices=SYNC_STATUS_CHOICES,
        default='idle'
    )
    last_sync_at = models.DateTimeField(
        _('Son Senkronizasyon'),
        null=True,
        blank=True
    )
    last_sync_order_date = models.DateTimeField(
        _('Son Senkronize Edilen Sipariş Tarihi'),
        null=True,
        blank=True,
        help_text=_('Incremental sync için referans tarih')
    )
    last_sync_error = models.TextField(
        _('Son Senkronizasyon Hatası'),
        blank=True
    )
    total_orders_synced = models.PositiveIntegerField(
        _('Toplam Senkronize Sipariş'),
        default=0
    )
    
    class Meta:
        db_table = 'seller_accounts'
        verbose_name = _('Satıcı Hesabı')
        verbose_name_plural = _('Satıcı Hesapları')
        ordering = ['-created_at']
        # Ensure user can't add same seller twice
        unique_together = ['user', 'seller_id']
    
    def __str__(self):
        return f'{self.shop_name} ({self.seller_id})'
    
    def save(self, *args, **kwargs):
        """Encrypt API credentials before saving."""
        # Check if this is an update with new credentials
        if self.pk:
            try:
                old_instance = SellerAccount.objects.get(pk=self.pk)
                # Only encrypt if values changed (new values won't be encrypted yet)
                if self.api_key != old_instance.api_key and not self._is_encrypted(self.api_key):
                    self.api_key = encrypt_credential(self.api_key)
                if self.api_secret != old_instance.api_secret and not self._is_encrypted(self.api_secret):
                    self.api_secret = encrypt_credential(self.api_secret)
            except SellerAccount.DoesNotExist:
                pass
        else:
            # New instance - encrypt credentials
            if not self._is_encrypted(self.api_key):
                self.api_key = encrypt_credential(self.api_key)
            if not self._is_encrypted(self.api_secret):
                self.api_secret = encrypt_credential(self.api_secret)
        
        super().save(*args, **kwargs)
    
    def _is_encrypted(self, value: str) -> bool:
        """Check if a value appears to be Fernet encrypted."""
        # Fernet tokens start with 'gAAAAA' when base64 encoded
        return value.startswith('gAAAAA') if value else False
    
    def get_decrypted_api_key(self) -> str:
        """Get decrypted API key."""
        return decrypt_credential(self.api_key)
    
    def get_decrypted_api_secret(self) -> str:
        """Get decrypted API secret."""
        return decrypt_credential(self.api_secret)
    
    @property
    def is_credentials_valid(self) -> bool:
        """Check if credentials appear to be set."""
        return bool(self.api_key and self.api_secret)
    
    def mark_sync_started(self):
        """Mark sync as started."""
        from django.utils import timezone
        self.sync_status = 'syncing'
        self.last_sync_error = ''
        self.save(update_fields=['sync_status', 'last_sync_error'])
    
    def mark_sync_completed(self, order_count: int = 0, last_order_date=None):
        """Mark sync as completed."""
        from django.utils import timezone
        self.sync_status = 'completed'
        self.last_sync_at = timezone.now()
        self.total_orders_synced += order_count
        if last_order_date:
            self.last_sync_order_date = last_order_date
        self.save(update_fields=[
            'sync_status', 'last_sync_at', 'total_orders_synced', 'last_sync_order_date'
        ])
    
    def mark_sync_failed(self, error_message: str):
        """Mark sync as failed with error."""
        self.sync_status = 'error'
        self.last_sync_error = error_message
        self.save(update_fields=['sync_status', 'last_sync_error'])


class SellerSyncLog(models.Model):
    """
    Log of sync operations for a seller account.
    Useful for debugging and monitoring.
    """
    
    STATUS_CHOICES = [
        ('started', 'Başladı'),
        ('completed', 'Tamamlandı'),
        ('failed', 'Başarısız'),
    ]
    
    seller_account = models.ForeignKey(
        SellerAccount,
        on_delete=models.CASCADE,
        related_name='sync_logs'
    )
    
    status = models.CharField(
        _('Durum'),
        max_length=20,
        choices=STATUS_CHOICES
    )
    
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Sync details
    sync_type = models.CharField(
        _('Senkronizasyon Tipi'),
        max_length=20,
        choices=[
            ('full', 'Tam Senkronizasyon'),
            ('incremental', 'Artımlı Senkronizasyon'),
            ('manual', 'Manuel Senkronizasyon'),
        ],
        default='incremental'
    )
    
    date_range_start = models.DateTimeField(
        _('Tarih Aralığı Başlangıç'),
        null=True,
        blank=True
    )
    date_range_end = models.DateTimeField(
        _('Tarih Aralığı Bitiş'),
        null=True,
        blank=True
    )
    
    # Results
    orders_fetched = models.PositiveIntegerField(default=0)
    orders_created = models.PositiveIntegerField(default=0)
    orders_updated = models.PositiveIntegerField(default=0)
    items_processed = models.PositiveIntegerField(default=0)
    
    # Errors
    error_message = models.TextField(blank=True)
    error_details = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'seller_sync_logs'
        verbose_name = _('Senkronizasyon Logu')
        verbose_name_plural = _('Senkronizasyon Logları')
        ordering = ['-started_at']
    
    def __str__(self):
        return f'{self.seller_account} - {self.started_at}'
    
    def mark_completed(self, orders_fetched=0, orders_created=0, orders_updated=0, items_processed=0):
        """Mark sync log as completed with results."""
        from django.utils import timezone
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.orders_fetched = orders_fetched
        self.orders_created = orders_created
        self.orders_updated = orders_updated
        self.items_processed = items_processed
        self.save()
    
    def mark_failed(self, error_message: str, error_details: dict = None):
        """Mark sync log as failed."""
        from django.utils import timezone
        self.status = 'failed'
        self.completed_at = timezone.now()
        self.error_message = error_message
        if error_details:
            self.error_details = error_details
        self.save()
    
    @property
    def duration_seconds(self):
        """Calculate sync duration in seconds."""
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
