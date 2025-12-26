"""
Calculations App - Models

Stores detailed profit calculations for order items and aggregated summaries.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class OrderItemCalculation(models.Model):
    """
    Stores detailed profit calculation for each order item.
    
    This is the CORE accounting model. All amounts in TRY.
    Stored with 4 decimal places for precision, displayed with 2.
    
    CALCULATION FORMULA:
    1. net_sale_price = unit_price × quantity - discount_amount
    2. sales_vat = net_sale_price - (net_sale_price / (1 + vat_rate))
    3. commission = (net_sale_price - sales_vat) × commission_rate
    4. net_vat_payable = sales_vat - (purchase_vat + commission_vat + cargo_vat + platform_vat)
    5. total_cost = product_cost + net_vat_payable + commission + cargo + platform_fee + withholding
    6. net_profit = (net_sale_price - sales_vat) - total_cost
    """
    
    order_item = models.OneToOneField(
        'orders.OrderItem',
        on_delete=models.CASCADE,
        related_name='calculation',
        verbose_name=_('Sipariş Kalemi')
    )
    
    calculated_at = models.DateTimeField(
        _('Hesaplama Tarihi'),
        auto_now=True
    )
    
    # === REVENUE (Gelir) ===
    gross_sale_price = models.DecimalField(
        _('Brüt Satış'),
        max_digits=12,
        decimal_places=4,
        help_text=_('Birim fiyat × adet (KDV dahil)')
    )
    discount_amount = models.DecimalField(
        _('İndirim Tutarı'),
        max_digits=12,
        decimal_places=4,
        default=0
    )
    net_sale_price = models.DecimalField(
        _('Net Satış'),
        max_digits=12,
        decimal_places=4,
        help_text=_('Brüt satış - indirim (KDV dahil)')
    )
    
    # === PRODUCT COST (Ürün Maliyeti) ===
    product_cost_excl_vat = models.DecimalField(
        _('Ürün Maliyeti (KDV Hariç)'),
        max_digits=12,
        decimal_places=4,
        help_text=_('Ürün alış maliyeti, KDV hariç')
    )
    purchase_vat_rate = models.DecimalField(
        _('Alış KDV Oranı'),
        max_digits=5,
        decimal_places=2,
        default=20.00
    )
    purchase_vat = models.DecimalField(
        _('Alış KDV\'si'),
        max_digits=12,
        decimal_places=4,
        help_text=_('product_cost_excl_vat × purchase_vat_rate')
    )
    product_cost_incl_vat = models.DecimalField(
        _('Ürün Maliyeti (KDV Dahil)'),
        max_digits=12,
        decimal_places=4
    )
    
    # === SALES VAT (Satış KDV) ===
    sales_vat_rate = models.DecimalField(
        _('Satış KDV Oranı'),
        max_digits=5,
        decimal_places=2,
        default=20.00
    )
    sales_vat = models.DecimalField(
        _('Satış KDV\'si'),
        max_digits=12,
        decimal_places=4,
        help_text=_('Hesaplanan KDV (output VAT)')
    )
    net_sale_price_excl_vat = models.DecimalField(
        _('Net Satış (KDV Hariç)'),
        max_digits=12,
        decimal_places=4
    )
    
    # === COMMISSION (Komisyon) ===
    commission_rate = models.DecimalField(
        _('Komisyon Oranı'),
        max_digits=5,
        decimal_places=2
    )
    commission_amount_excl_vat = models.DecimalField(
        _('Komisyon (KDV Hariç)'),
        max_digits=12,
        decimal_places=4,
        help_text=_('net_sale_price_excl_vat × commission_rate')
    )
    commission_vat_rate = models.DecimalField(
        _('Komisyon KDV Oranı'),
        max_digits=5,
        decimal_places=2,
        default=20.00
    )
    commission_vat = models.DecimalField(
        _('Komisyon KDV\'si'),
        max_digits=12,
        decimal_places=4
    )
    commission_total = models.DecimalField(
        _('Komisyon Toplam'),
        max_digits=12,
        decimal_places=4,
        help_text=_('Komisyon + KDV')
    )
    
    # === CARGO COST (Kargo Maliyeti) ===
    cargo_cost_excl_vat = models.DecimalField(
        _('Kargo Maliyeti (KDV Hariç)'),
        max_digits=12,
        decimal_places=4,
        default=0
    )
    cargo_vat_rate = models.DecimalField(
        _('Kargo KDV Oranı'),
        max_digits=5,
        decimal_places=2,
        default=20.00
    )
    cargo_vat = models.DecimalField(
        _('Kargo KDV\'si'),
        max_digits=12,
        decimal_places=4,
        default=0
    )
    cargo_cost_total = models.DecimalField(
        _('Kargo Toplam'),
        max_digits=12,
        decimal_places=4,
        default=0
    )
    
    # === PLATFORM SERVICE FEE (Platform Hizmet Bedeli) ===
    platform_fee_excl_vat = models.DecimalField(
        _('Platform Ücreti (KDV Hariç)'),
        max_digits=12,
        decimal_places=4,
        default=0
    )
    platform_fee_vat_rate = models.DecimalField(
        _('Platform KDV Oranı'),
        max_digits=5,
        decimal_places=2,
        default=20.00
    )
    platform_fee_vat = models.DecimalField(
        _('Platform KDV\'si'),
        max_digits=12,
        decimal_places=4,
        default=0
    )
    platform_fee_total = models.DecimalField(
        _('Platform Toplam'),
        max_digits=12,
        decimal_places=4,
        default=0
    )
    
    # === WITHHOLDING TAX (Stopaj) ===
    withholding_tax_rate = models.DecimalField(
        _('Stopaj Oranı'),
        max_digits=5,
        decimal_places=4,
        default=0,
        help_text=_('Genellikle 0, bazı durumlar için uygulanır')
    )
    withholding_tax = models.DecimalField(
        _('Stopaj Tutarı'),
        max_digits=12,
        decimal_places=4,
        default=0
    )
    
    # === VAT CALCULATIONS (KDV Hesaplamaları) ===
    total_output_vat = models.DecimalField(
        _('Hesaplanan KDV'),
        max_digits=12,
        decimal_places=4,
        help_text=_('Satış KDV\'si (output)')
    )
    total_input_vat = models.DecimalField(
        _('İndirilecek KDV'),
        max_digits=12,
        decimal_places=4,
        help_text=_('Alış + Komisyon + Kargo + Platform KDV\'si (input)')
    )
    net_vat_payable = models.DecimalField(
        _('Ödenecek Net KDV'),
        max_digits=12,
        decimal_places=4,
        help_text=_('Hesaplanan - İndirilecek KDV (negatif = iade)')
    )
    
    # === TOTALS (Toplamlar) ===
    total_trendyol_deductions = models.DecimalField(
        _('Toplam Trendyol Kesintileri'),
        max_digits=12,
        decimal_places=4,
        help_text=_('Komisyon + Kargo + Platform (KDV dahil)')
    )
    total_cost = models.DecimalField(
        _('Toplam Maliyet'),
        max_digits=12,
        decimal_places=4,
        help_text=_('Tüm maliyet kalemleri toplamı')
    )
    
    # === PROFIT (Kâr) ===
    net_profit = models.DecimalField(
        _('Net Kâr'),
        max_digits=12,
        decimal_places=4
    )
    profit_margin_percent = models.DecimalField(
        _('Kâr Marjı (%)'),
        max_digits=7,
        decimal_places=2
    )
    
    # === AUDIT FLAGS ===
    is_profitable = models.BooleanField(
        _('Kârlı mı?'),
        default=True
    )
    has_cost_data = models.BooleanField(
        _('Maliyet Verisi Var'),
        default=False,
        help_text=_('Ürün maliyeti mevcut mu?')
    )
    calculation_version = models.CharField(
        _('Hesaplama Versiyonu'),
        max_length=10,
        default='1.0',
        help_text=_('Formül versiyon takibi')
    )
    calculation_notes = models.TextField(
        _('Hesaplama Notları'),
        blank=True,
        help_text=_('Hesaplama sırasında oluşan notlar/uyarılar')
    )
    
    class Meta:
        db_table = 'order_item_calculations'
        verbose_name = _('Sipariş Kalemi Hesaplaması')
        verbose_name_plural = _('Sipariş Kalemi Hesaplamaları')
        ordering = ['-calculated_at']
    
    def __str__(self):
        return f'{self.order_item} - {self.net_profit} TL'


class DailyProfitSummary(models.Model):
    """
    Aggregated daily profit summary for faster dashboard queries.
    
    Pre-calculated daily totals to avoid expensive real-time aggregations.
    """
    
    seller_account = models.ForeignKey(
        'sellers.SellerAccount',
        on_delete=models.CASCADE,
        related_name='daily_summaries',
        verbose_name=_('Satıcı Hesabı')
    )
    
    date = models.DateField(
        _('Tarih'),
        db_index=True
    )
    
    # Order counts
    total_orders = models.PositiveIntegerField(
        _('Toplam Sipariş'),
        default=0
    )
    total_items = models.PositiveIntegerField(
        _('Toplam Kalem'),
        default=0
    )
    
    # Revenue
    total_revenue = models.DecimalField(
        _('Toplam Gelir'),
        max_digits=14,
        decimal_places=2,
        default=0,
        help_text=_('Net satış (KDV dahil)')
    )
    total_revenue_excl_vat = models.DecimalField(
        _('Toplam Gelir (KDV Hariç)'),
        max_digits=14,
        decimal_places=2,
        default=0
    )
    
    # Costs
    total_product_cost = models.DecimalField(
        _('Toplam Ürün Maliyeti'),
        max_digits=14,
        decimal_places=2,
        default=0
    )
    total_commission = models.DecimalField(
        _('Toplam Komisyon'),
        max_digits=14,
        decimal_places=2,
        default=0
    )
    total_cargo_cost = models.DecimalField(
        _('Toplam Kargo'),
        max_digits=14,
        decimal_places=2,
        default=0
    )
    total_platform_fee = models.DecimalField(
        _('Toplam Platform Ücreti'),
        max_digits=14,
        decimal_places=2,
        default=0
    )
    total_vat_payable = models.DecimalField(
        _('Toplam Ödenecek KDV'),
        max_digits=14,
        decimal_places=2,
        default=0
    )
    
    # Profit
    total_cost = models.DecimalField(
        _('Toplam Maliyet'),
        max_digits=14,
        decimal_places=2,
        default=0
    )
    total_profit = models.DecimalField(
        _('Toplam Kâr'),
        max_digits=14,
        decimal_places=2,
        default=0
    )
    average_margin = models.DecimalField(
        _('Ortalama Marj (%)'),
        max_digits=7,
        decimal_places=2,
        default=0
    )
    
    # Data quality
    items_with_cost = models.PositiveIntegerField(
        _('Maliyetli Kalem Sayısı'),
        default=0
    )
    items_without_cost = models.PositiveIntegerField(
        _('Maliyetsiz Kalem Sayısı'),
        default=0
    )
    
    # Tracking
    calculated_at = models.DateTimeField(
        _('Hesaplama Tarihi'),
        auto_now=True
    )
    
    class Meta:
        db_table = 'daily_profit_summaries'
        verbose_name = _('Günlük Kâr Özeti')
        verbose_name_plural = _('Günlük Kâr Özetleri')
        unique_together = ['seller_account', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['seller_account', 'date']),
        ]
    
    def __str__(self):
        return f'{self.seller_account.shop_name} - {self.date}'


class ProductProfitSummary(models.Model):
    """
    Aggregated profit summary per product.
    
    Useful for identifying most/least profitable products.
    """
    
    product = models.OneToOneField(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='profit_summary',
        verbose_name=_('Ürün')
    )
    
    # Totals (all time)
    total_quantity_sold = models.PositiveIntegerField(
        _('Toplam Satış Adedi'),
        default=0
    )
    total_revenue = models.DecimalField(
        _('Toplam Gelir'),
        max_digits=14,
        decimal_places=2,
        default=0
    )
    total_cost = models.DecimalField(
        _('Toplam Maliyet'),
        max_digits=14,
        decimal_places=2,
        default=0
    )
    total_profit = models.DecimalField(
        _('Toplam Kâr'),
        max_digits=14,
        decimal_places=2,
        default=0
    )
    
    # Averages
    average_profit_per_item = models.DecimalField(
        _('Kalem Başı Ortalama Kâr'),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    average_margin = models.DecimalField(
        _('Ortalama Marj (%)'),
        max_digits=7,
        decimal_places=2,
        default=0
    )
    
    # Status
    is_profitable = models.BooleanField(
        _('Kârlı mı?'),
        default=True
    )
    
    # Period (last 30 days)
    last_30_days_quantity = models.PositiveIntegerField(
        _('Son 30 Gün Satış'),
        default=0
    )
    last_30_days_profit = models.DecimalField(
        _('Son 30 Gün Kâr'),
        max_digits=14,
        decimal_places=2,
        default=0
    )
    
    calculated_at = models.DateTimeField(
        _('Hesaplama Tarihi'),
        auto_now=True
    )
    
    class Meta:
        db_table = 'product_profit_summaries'
        verbose_name = _('Ürün Kâr Özeti')
        verbose_name_plural = _('Ürün Kâr Özetleri')
        ordering = ['-total_profit']
    
    def __str__(self):
        return f'{self.product.barcode} - {self.total_profit} TL'
