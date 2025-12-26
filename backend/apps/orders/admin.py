"""
Orders App - Admin Configuration
"""

from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['trendyol_line_id', 'barcode', 'product_name', 'quantity',
                       'unit_price', 'discount_amount', 'commission_rate', 'commission_amount',
                       'cargo_cost', 'platform_service_fee', 'item_status']
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['trendyol_order_number', 'seller_account', 'order_date', 'status', 'total_price', 'item_count']
    list_filter = ['status', 'seller_account', 'order_date']
    search_fields = ['trendyol_order_number', 'trendyol_order_id']
    ordering = ['-order_date']
    readonly_fields = ['trendyol_order_id', 'trendyol_order_number', 'order_date',
                       'status', 'cargo_company', 'cargo_tracking_number',
                       'shipped_at', 'delivered_at', 'total_price', 'total_discount',
                       'synced_at', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    
    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = 'Kalem Sayısı'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'barcode', 'product_name', 'quantity', 'unit_price', 'item_status', 'is_calculated']
    list_filter = ['item_status', 'is_calculated', 'order__seller_account']
    search_fields = ['barcode', 'product_name', 'order__trendyol_order_number']
    ordering = ['-order__order_date']
    readonly_fields = ['order', 'trendyol_line_id', 'barcode', 'product_code',
                       'product_name', 'quantity', 'unit_price', 'discount_amount',
                       'commission_rate', 'commission_amount', 'cargo_cost',
                       'platform_service_fee', 'item_status']
