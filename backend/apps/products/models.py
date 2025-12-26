"""
Products App - Models

Product catalog with cost tracking for profitability analysis.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from core.mixins import TimestampMixin
from core.validators import validate_barcode, validate_positive_decimal, validate_percentage


class Product(TimestampMixin, models.Model):
    """
    Product with cost information for profit calculations.
    
    Each product is linked to a seller account.
    Product costs can be updated over time, with history tracking.
    """
    
    seller_account = models.ForeignKey(
        'sellers.SellerAccount',
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name=_('Satıcı Hesabı')
    )
    
    # Product identifiers
    barcode = models.CharField(
        _('Barkod'),
        max_length=100,
        validators=[validate_barcode],
        db_index=True
    )
    product_code = models.CharField(
        _('Model Kodu'),
        max_length=100,
        blank=True,
        db_index=True
    )
    trendyol_product_id = models.CharField(
        _('Trendyol Ürün ID'),
        max_length=100,
        blank=True
    )
    
    # Product details
    title = models.CharField(
        _('Ürün Adı'),
        max_length=500
    )
    brand = models.CharField(
        _('Marka'),
        max_length=255,
        blank=True
    )
    category = models.CharField(
        _('Kategori'),
        max_length=500,
        blank=True
    )
    category_id = models.CharField(
        _('Kategori ID'),
        max_length=50,
        blank=True
    )
    
    # Cost information (KDV hariç / excluding VAT)
    product_cost_excl_vat = models.DecimalField(
        _('Ürün Maliyeti (KDV Hariç)'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[validate_positive_decimal],
        help_text=_('Ürün alış maliyeti, KDV hariç (TL)')
    )
    purchase_vat_rate = models.DecimalField(
        _('Alış KDV Oranı'),
        max_digits=5,
        decimal_places=2,
        default=20.00,
        validators=[validate_percentage],
        help_text=_('Ürün alış KDV oranı (%)')
    )
    
    # Commission rate (can override seller default)
    commission_rate = models.DecimalField(
        _('Komisyon Oranı'),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[validate_percentage],
        help_text=_('Trendyol kategori komisyon oranı (%). Boşsa satıcı varsayılanı kullanılır.')
    )
    
    # Sales VAT rate (usually 20% in Turkey)
    sales_vat_rate = models.DecimalField(
        _('Satış KDV Oranı'),
        max_digits=5,
        decimal_places=2,
        default=20.00,
        validators=[validate_percentage],
        help_text=_('Satış KDV oranı (%)')
    )
    
    # Status
    is_active = models.BooleanField(
        _('Aktif'),
        default=True
    )
    has_cost_data = models.BooleanField(
        _('Maliyet Verisi Var'),
        default=False,
        help_text=_('Maliyet bilgisi girilmiş mi?')
    )
    
    # Tracking
    cost_updated_at = models.DateTimeField(
        _('Maliyet Güncelleme Tarihi'),
        null=True,
        blank=True
    )
    last_order_date = models.DateTimeField(
        _('Son Sipariş Tarihi'),
        null=True,
        blank=True
    )
    total_quantity_sold = models.PositiveIntegerField(
        _('Toplam Satış Adedi'),
        default=0
    )
    
    class Meta:
        db_table = 'products'
        verbose_name = _('Ürün')
        verbose_name_plural = _('Ürünler')
        ordering = ['-last_order_date', 'title']
        unique_together = ['seller_account', 'barcode']
        indexes = [
            models.Index(fields=['seller_account', 'barcode']),
            models.Index(fields=['seller_account', 'product_code']),
        ]
    
    def __str__(self):
        return f'{self.title} ({self.barcode})'
    
    def save(self, *args, **kwargs):
        """Update has_cost_data flag based on cost value."""
        self.has_cost_data = self.product_cost_excl_vat is not None
        super().save(*args, **kwargs)
    
    def update_cost(self, cost_excl_vat, vat_rate=None, track_history=True):
        """
        Update product cost with optional history tracking.
        
        Args:
            cost_excl_vat: New cost excluding VAT
            vat_rate: Optional new VAT rate
            track_history: Whether to create a history record
        """
        from django.utils import timezone
        
        if track_history and self.product_cost_excl_vat is not None:
            # Create history record before updating
            ProductCostHistory.objects.create(
                product=self,
                cost_excl_vat=self.product_cost_excl_vat,
                vat_rate=self.purchase_vat_rate,
                effective_date=self.cost_updated_at.date() if self.cost_updated_at else timezone.now().date()
            )
        
        self.product_cost_excl_vat = cost_excl_vat
        if vat_rate is not None:
            self.purchase_vat_rate = vat_rate
        self.cost_updated_at = timezone.now()
        self.has_cost_data = True
        self.save(update_fields=['product_cost_excl_vat', 'purchase_vat_rate', 'cost_updated_at', 'has_cost_data'])
    
    def get_effective_commission_rate(self):
        """Get commission rate, falling back to seller default."""
        if self.commission_rate is not None:
            return self.commission_rate
        return self.seller_account.default_commission_rate
    
    @property
    def product_cost_incl_vat(self):
        """Calculate cost including VAT."""
        if self.product_cost_excl_vat is None:
            return None
        from decimal import Decimal
        vat = self.product_cost_excl_vat * (self.purchase_vat_rate / Decimal('100'))
        return self.product_cost_excl_vat + vat


class ProductCostHistory(models.Model):
    """
    Historical record of product cost changes.
    Useful for auditing and recalculations.
    """
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='cost_history',
        verbose_name=_('Ürün')
    )
    
    cost_excl_vat = models.DecimalField(
        _('Maliyet (KDV Hariç)'),
        max_digits=12,
        decimal_places=2
    )
    vat_rate = models.DecimalField(
        _('KDV Oranı'),
        max_digits=5,
        decimal_places=2
    )
    
    effective_date = models.DateField(
        _('Geçerlilik Tarihi'),
        help_text=_('Bu maliyetin geçerli olduğu tarih')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'product_cost_history'
        verbose_name = _('Maliyet Geçmişi')
        verbose_name_plural = _('Maliyet Geçmişleri')
        ordering = ['-effective_date', '-created_at']
    
    def __str__(self):
        return f'{self.product.barcode} - {self.cost_excl_vat} TL ({self.effective_date})'


class BulkCostUpload(TimestampMixin, models.Model):
    """
    Track bulk cost uploads via Excel.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Beklemede'),
        ('processing', 'İşleniyor'),
        ('completed', 'Tamamlandı'),
        ('failed', 'Başarısız'),
    ]
    
    seller_account = models.ForeignKey(
        'sellers.SellerAccount',
        on_delete=models.CASCADE,
        related_name='bulk_uploads'
    )
    
    file_name = models.CharField(
        _('Dosya Adı'),
        max_length=255
    )
    file_path = models.FileField(
        _('Dosya'),
        upload_to='bulk_uploads/%Y/%m/'
    )
    
    status = models.CharField(
        _('Durum'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Results
    total_rows = models.PositiveIntegerField(default=0)
    processed_rows = models.PositiveIntegerField(default=0)
    success_count = models.PositiveIntegerField(default=0)
    error_count = models.PositiveIntegerField(default=0)
    
    error_details = models.JSONField(
        _('Hata Detayları'),
        default=list,
        blank=True
    )
    
    processed_at = models.DateTimeField(
        _('İşlenme Tarihi'),
        null=True,
        blank=True
    )
    
    class Meta:
        db_table = 'bulk_cost_uploads'
        verbose_name = _('Toplu Yükleme')
        verbose_name_plural = _('Toplu Yüklemeler')
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.file_name} - {self.status}'
