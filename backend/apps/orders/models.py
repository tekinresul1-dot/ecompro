"""
Orders App - Models

Order and order item models for Trendyol orders.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from core.mixins import TimestampMixin


class Order(TimestampMixin, models.Model):
    """
    Trendyol order header.
    
    Stores order-level information fetched from Trendyol API.
    """
    
    STATUS_CHOICES = [
        ('Created', 'Oluşturuldu'),
        ('Picking', 'Hazırlanıyor'),
        ('Invoiced', 'Faturalandı'),
        ('Shipped', 'Kargoya Verildi'),
        ('Delivered', 'Teslim Edildi'),
        ('Cancelled', 'İptal'),
        ('Returned', 'İade'),
        ('UnDelivered', 'Teslim Edilemedi'),
        ('UnDeliveredAndReturned', 'Teslim Edilemedi ve İade'),
    ]
    
    seller_account = models.ForeignKey(
        'sellers.SellerAccount',
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name=_('Satıcı Hesabı')
    )
    
    # Trendyol order identifiers
    trendyol_order_id = models.CharField(
        _('Trendyol Sipariş ID'),
        max_length=100,
        db_index=True
    )
    trendyol_order_number = models.CharField(
        _('Sipariş Numarası'),
        max_length=100,
        unique=True,
        db_index=True
    )
    
    # Order details
    order_date = models.DateTimeField(
        _('Sipariş Tarihi'),
        db_index=True
    )
    status = models.CharField(
        _('Durum'),
        max_length=50,
        choices=STATUS_CHOICES,
        db_index=True
    )
    
    # Customer info (hashed/anonymized for privacy)
    customer_id = models.CharField(
        _('Müşteri ID'),
        max_length=100,
        blank=True
    )
    
    # Shipping info
    cargo_company = models.CharField(
        _('Kargo Şirketi'),
        max_length=100,
        blank=True
    )
    cargo_tracking_number = models.CharField(
        _('Kargo Takip No'),
        max_length=100,
        blank=True
    )
    cargo_provider_name = models.CharField(
        _('Kargo Sağlayıcı'),
        max_length=100,
        blank=True
    )
    
    # Timestamps from Trendyol
    shipment_package_id = models.CharField(
        _('Gönderi Paket ID'),
        max_length=100,
        blank=True
    )
    shipped_at = models.DateTimeField(
        _('Kargoya Verilme Tarihi'),
        null=True,
        blank=True
    )
    delivered_at = models.DateTimeField(
        _('Teslim Tarihi'),
        null=True,
        blank=True
    )
    
    # Invoice info
    invoice_number = models.CharField(
        _('Fatura Numarası'),
        max_length=100,
        blank=True
    )
    
    # Aggregate values (calculated from items)
    total_price = models.DecimalField(
        _('Toplam Tutar'),
        max_digits=14,
        decimal_places=2,
        default=0
    )
    total_discount = models.DecimalField(
        _('Toplam İndirim'),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    
    # Raw API response for debugging/auditing
    raw_data = models.JSONField(
        _('Ham Veri'),
        default=dict,
        blank=True
    )
    
    # Sync tracking
    synced_at = models.DateTimeField(
        _('Senkronizasyon Tarihi'),
        auto_now=True
    )
    last_modified_date = models.DateTimeField(
        _('Son Değişiklik Tarihi'),
        null=True,
        blank=True,
        help_text=_('Trendyol\'daki son değişiklik tarihi')
    )
    
    class Meta:
        db_table = 'orders'
        verbose_name = _('Sipariş')
        verbose_name_plural = _('Siparişler')
        ordering = ['-order_date']
        indexes = [
            models.Index(fields=['seller_account', 'order_date']),
            models.Index(fields=['seller_account', 'status']),
            models.Index(fields=['trendyol_order_number']),
        ]
    
    def __str__(self):
        return f'{self.trendyol_order_number} - {self.status}'
    
    @property
    def item_count(self):
        """Number of items in this order."""
        return self.items.count()
    
    @property
    def is_completed(self):
        """Check if order is in a final state."""
        return self.status in ['Delivered', 'Cancelled', 'Returned', 'UnDeliveredAndReturned']
    
    @property
    def is_revenue_order(self):
        """Check if order generates revenue (not cancelled/returned)."""
        return self.status in ['Created', 'Picking', 'Invoiced', 'Shipped', 'Delivered']


class OrderItem(models.Model):
    """
    Individual line item in an order.
    
    Contains product details, pricing, and Trendyol deductions.
    This is the primary entity for profit calculations.
    """
    
    ITEM_STATUS_CHOICES = [
        ('active', 'Aktif'),
        ('cancelled', 'İptal'),
        ('returned', 'İade'),
    ]
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Sipariş')
    )
    
    # Trendyol identifiers
    trendyol_line_id = models.CharField(
        _('Trendyol Line ID'),
        max_length=100
    )
    
    # Product reference
    barcode = models.CharField(
        _('Barkod'),
        max_length=100,
        db_index=True
    )
    product_code = models.CharField(
        _('Model Kodu'),
        max_length=100,
        blank=True
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='order_items',
        verbose_name=_('Ürün')
    )
    
    # Product details (from Trendyol)
    product_name = models.CharField(
        _('Ürün Adı'),
        max_length=500
    )
    product_size = models.CharField(
        _('Beden'),
        max_length=50,
        blank=True
    )
    product_color = models.CharField(
        _('Renk'),
        max_length=100,
        blank=True
    )
    
    # Quantity
    quantity = models.PositiveIntegerField(
        _('Adet'),
        default=1
    )
    
    # Pricing (KDV dahil / VAT included)
    unit_price = models.DecimalField(
        _('Birim Fiyat'),
        max_digits=12,
        decimal_places=2,
        help_text=_('Satış fiyatı (KDV dahil)')
    )
    original_price = models.DecimalField(
        _('Orijinal Fiyat'),
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=_('İndirim öncesi fiyat')
    )
    discount_amount = models.DecimalField(
        _('İndirim Tutarı'),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    
    # Trendyol deductions
    commission_rate = models.DecimalField(
        _('Komisyon Oranı'),
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text=_('Trendyol komisyon oranı (%)')
    )
    commission_amount = models.DecimalField(
        _('Komisyon Tutarı'),
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=_('Trendyol tarafından kesilen komisyon')
    )
    cargo_cost = models.DecimalField(
        _('Kargo Maliyeti'),
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=_('Satıcıya yansıyan kargo maliyeti')
    )
    platform_service_fee = models.DecimalField(
        _('Platform Hizmet Bedeli'),
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=_('Trendyol platform hizmet ücreti')
    )
    
    # Additional Trendyol fields
    merchant_sku = models.CharField(
        _('Satıcı SKU'),
        max_length=100,
        blank=True
    )
    
    # Item status
    item_status = models.CharField(
        _('Kalem Durumu'),
        max_length=20,
        choices=ITEM_STATUS_CHOICES,
        default='active'
    )
    return_reason = models.CharField(
        _('İade Nedeni'),
        max_length=255,
        blank=True
    )
    
    # Calculation flag
    is_calculated = models.BooleanField(
        _('Hesaplandı'),
        default=False,
        help_text=_('Kar hesaplaması yapıldı mı?')
    )
    
    # Raw data
    raw_data = models.JSONField(
        _('Ham Veri'),
        default=dict,
        blank=True
    )
    
    class Meta:
        db_table = 'order_items'
        verbose_name = _('Sipariş Kalemi')
        verbose_name_plural = _('Sipariş Kalemleri')
        ordering = ['order', 'id']
        indexes = [
            models.Index(fields=['order', 'barcode']),
            models.Index(fields=['barcode']),
            models.Index(fields=['item_status']),
        ]
    
    def __str__(self):
        return f'{self.order.trendyol_order_number} - {self.barcode}'
    
    @property
    def line_total(self):
        """Calculate line total (unit_price * quantity - discount)."""
        return (self.unit_price * self.quantity) - self.discount_amount
    
    @property
    def is_revenue_item(self):
        """Check if this item generates revenue."""
        return self.item_status == 'active' and self.order.is_revenue_order
    
    def link_product(self):
        """
        Link this order item to a Product record.
        Creates the product if it doesn't exist.
        """
        from apps.products.models import Product
        
        # Extract VAT from raw data
        vat_rate_val = self.raw_data.get('vatBase', 0)
        try:
            vat_rate = int(vat_rate_val)
        except:
            vat_rate = 0
            
        content_id = str(self.raw_data.get('contentId', '') or self.raw_data.get('productCode', ''))
        
        defaults = {
            'product_code': self.product_code,
            'title': self.product_name,
            'trendyol_product_id': content_id,
            'image_url': '',
            'brand': '',
            'sales_vat_rate': vat_rate,
            'purchase_vat_rate': vat_rate, # Default assumption
        }
        
        product, created = Product.objects.get_or_create(
            seller_account=self.order.seller_account,
            barcode=self.barcode,
            defaults=defaults
        )
        
        if not created:
            updates = []
            if not product.title:
                product.title = self.product_name
                updates.append('title')
            
            # Recover ID if missing
            if not product.trendyol_product_id and content_id:
                product.trendyol_product_id = content_id
                updates.append('trendyol_product_id')
                
            # Update VAT if missing
            if product.sales_vat_rate == 0 and vat_rate > 0:
                product.sales_vat_rate = vat_rate
                updates.append('sales_vat_rate')
                
            if product.purchase_vat_rate == 0 and vat_rate > 0:
                 product.purchase_vat_rate = vat_rate
                 updates.append('purchase_vat_rate')
            
            if updates:
                product.save(update_fields=updates)
        
        self.product = product
        self.save(update_fields=['product'])
        
        return product
