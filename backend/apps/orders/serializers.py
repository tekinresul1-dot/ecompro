"""
Orders App - Serializers
"""

from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for order items."""
    
    line_total = serializers.ReadOnlyField()
    product_title = serializers.CharField(source='product.title', read_only=True, allow_null=True)
    has_cost_data = serializers.BooleanField(source='product.has_cost_data', read_only=True, default=False)
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'trendyol_line_id', 'barcode', 'product_code',
            'product_name', 'product_title', 'product_size', 'product_color',
            'quantity', 'unit_price', 'original_price', 'discount_amount', 'line_total',
            'commission_rate', 'commission_amount',
            'cargo_cost', 'platform_service_fee',
            'item_status', 'return_reason',
            'is_calculated', 'has_cost_data',
            'product'
        ]


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for order listing."""
    
    item_count = serializers.ReadOnlyField()
    seller_name = serializers.CharField(source='seller_account.shop_name', read_only=True)
    is_revenue_order = serializers.ReadOnlyField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'trendyol_order_id', 'trendyol_order_number',
            'order_date', 'status', 'is_revenue_order',
            'cargo_company', 'cargo_tracking_number',
            'shipped_at', 'delivered_at',
            'total_price', 'total_discount',
            'item_count', 'seller_name', 'seller_account',
            'created_at'
        ]


class OrderDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single order view."""
    
    items = OrderItemSerializer(many=True, read_only=True)
    item_count = serializers.ReadOnlyField()
    seller_name = serializers.CharField(source='seller_account.shop_name', read_only=True)
    is_revenue_order = serializers.ReadOnlyField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'trendyol_order_id', 'trendyol_order_number',
            'order_date', 'status', 'is_revenue_order',
            'cargo_company', 'cargo_tracking_number', 'cargo_provider_name',
            'shipped_at', 'delivered_at',
            'shipment_package_id', 'invoice_number',
            'total_price', 'total_discount',
            'item_count', 'items',
            'seller_name', 'seller_account',
            'synced_at', 'created_at'
        ]


class OrderFilterSerializer(serializers.Serializer):
    """Serializer for order filters."""
    
    seller_account = serializers.IntegerField(required=False)
    status = serializers.ChoiceField(choices=Order.STATUS_CHOICES, required=False)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    search = serializers.CharField(required=False, max_length=100)
    barcode = serializers.CharField(required=False, max_length=100)


class OrderSummarySerializer(serializers.Serializer):
    """Serializer for order summary statistics."""
    
    total_orders = serializers.IntegerField()
    total_items = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_discount = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    by_status = serializers.DictField(
        child=serializers.IntegerField()
    )
