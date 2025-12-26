"""
Sellers App - Admin Configuration
"""

from django.contrib import admin
from .models import SellerAccount, SellerSyncLog


@admin.register(SellerAccount)
class SellerAccountAdmin(admin.ModelAdmin):
    list_display = ['shop_name', 'seller_id', 'user', 'is_active', 'sync_status', 'last_sync_at', 'total_orders_synced']
    list_filter = ['is_active', 'sync_status', 'created_at']
    search_fields = ['shop_name', 'seller_id', 'user__email']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'last_sync_at', 'last_sync_order_date', 'total_orders_synced']
    
    fieldsets = (
        ('Genel', {'fields': ('user', 'shop_name', 'shop_url', 'seller_id')}),
        ('API Bilgileri', {'fields': ('api_key', 'api_secret')}),
        ('Varsayılan Değerler', {'fields': ('default_commission_rate', 'default_cargo_cost')}),
        ('Durum', {'fields': ('is_active', 'sync_status', 'last_sync_error')}),
        ('Senkronizasyon', {'fields': ('last_sync_at', 'last_sync_order_date', 'total_orders_synced')}),
        ('Tarihler', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(SellerSyncLog)
class SellerSyncLogAdmin(admin.ModelAdmin):
    list_display = ['seller_account', 'status', 'sync_type', 'started_at', 'orders_fetched', 'duration_seconds']
    list_filter = ['status', 'sync_type', 'started_at']
    search_fields = ['seller_account__shop_name']
    ordering = ['-started_at']
    readonly_fields = ['seller_account', 'status', 'sync_type', 'started_at', 'completed_at',
                       'orders_fetched', 'orders_created', 'orders_updated', 'items_processed',
                       'error_message', 'error_details']
