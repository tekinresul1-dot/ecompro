"""
Calculations App - Admin Configuration
"""

from django.contrib import admin
from .models import OrderItemCalculation, DailyProfitSummary, ProductProfitSummary


@admin.register(OrderItemCalculation)
class OrderItemCalculationAdmin(admin.ModelAdmin):
    list_display = [
        'order_item', 'net_sale_price', 'total_cost', 
        'net_profit', 'profit_margin_percent', 'is_profitable', 'has_cost_data'
    ]
    list_filter = ['is_profitable', 'has_cost_data', 'calculated_at']
    search_fields = ['order_item__barcode', 'order_item__order__trendyol_order_number']
    ordering = ['-calculated_at']
    readonly_fields = [
        'order_item', 'calculated_at',
        'gross_sale_price', 'discount_amount', 'net_sale_price',
        'net_sale_price_excl_vat', 'sales_vat', 'sales_vat_rate',
        'product_cost_excl_vat', 'purchase_vat', 'product_cost_incl_vat',
        'commission_rate', 'commission_amount_excl_vat', 'commission_vat', 'commission_total',
        'cargo_cost_excl_vat', 'cargo_vat', 'cargo_cost_total',
        'platform_fee_excl_vat', 'platform_fee_vat', 'platform_fee_total',
        'total_output_vat', 'total_input_vat', 'net_vat_payable',
        'total_trendyol_deductions', 'total_cost',
        'net_profit', 'profit_margin_percent',
        'is_profitable', 'has_cost_data', 'calculation_notes',
    ]
    
    fieldsets = (
        ('Sipariş Bilgisi', {
            'fields': ('order_item', 'calculated_at')
        }),
        ('Gelir', {
            'fields': ('gross_sale_price', 'discount_amount', 'net_sale_price', 
                       'net_sale_price_excl_vat', 'sales_vat', 'sales_vat_rate')
        }),
        ('Ürün Maliyeti', {
            'fields': ('product_cost_excl_vat', 'purchase_vat', 'product_cost_incl_vat')
        }),
        ('Komisyon', {
            'fields': ('commission_rate', 'commission_amount_excl_vat', 'commission_vat', 'commission_total')
        }),
        ('Kargo', {
            'fields': ('cargo_cost_excl_vat', 'cargo_vat', 'cargo_cost_total')
        }),
        ('Platform Ücreti', {
            'fields': ('platform_fee_excl_vat', 'platform_fee_vat', 'platform_fee_total')
        }),
        ('KDV Mahsup', {
            'fields': ('total_output_vat', 'total_input_vat', 'net_vat_payable')
        }),
        ('Kâr', {
            'fields': ('total_trendyol_deductions', 'total_cost', 'net_profit', 
                       'profit_margin_percent', 'is_profitable', 'has_cost_data', 'calculation_notes'),
            'classes': ('wide',)
        }),
    )


@admin.register(DailyProfitSummary)
class DailyProfitSummaryAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'seller_account', 'total_orders', 'total_items',
        'total_revenue', 'total_profit', 'average_margin'
    ]
    list_filter = ['seller_account', 'date']
    ordering = ['-date']
    date_hierarchy = 'date'


@admin.register(ProductProfitSummary)
class ProductProfitSummaryAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'total_quantity_sold', 'total_revenue',
        'total_profit', 'average_margin', 'is_profitable'
    ]
    list_filter = ['is_profitable']
    search_fields = ['product__barcode', 'product__title']
    ordering = ['-total_profit']
