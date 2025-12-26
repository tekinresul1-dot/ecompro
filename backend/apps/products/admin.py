"""
Products App - Admin Configuration
"""

from django.contrib import admin
from .models import Product, ProductCostHistory, BulkCostUpload


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['barcode', 'title', 'seller_account', 'product_cost_excl_vat', 'has_cost_data', 'total_quantity_sold']
    list_filter = ['seller_account', 'has_cost_data', 'is_active', 'brand']
    search_fields = ['barcode', 'product_code', 'title']
    ordering = ['-last_order_date']
    readonly_fields = ['created_at', 'updated_at', 'cost_updated_at', 'last_order_date', 'total_quantity_sold']


@admin.register(ProductCostHistory)
class ProductCostHistoryAdmin(admin.ModelAdmin):
    list_display = ['product', 'cost_excl_vat', 'vat_rate', 'effective_date', 'created_at']
    list_filter = ['effective_date', 'created_at']
    search_fields = ['product__barcode', 'product__title']
    ordering = ['-effective_date']
    readonly_fields = ['product', 'cost_excl_vat', 'vat_rate', 'effective_date', 'created_at']


@admin.register(BulkCostUpload)
class BulkCostUploadAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'seller_account', 'status', 'success_count', 'error_count', 'created_at']
    list_filter = ['status', 'created_at']
    ordering = ['-created_at']
    readonly_fields = ['seller_account', 'file_name', 'file_path', 'status',
                       'total_rows', 'processed_rows', 'success_count', 'error_count',
                       'error_details', 'created_at', 'processed_at']
