"""
Calculations App - Serializers
"""

from rest_framework import serializers
from decimal import Decimal

from .models import OrderItemCalculation, DailyProfitSummary, ProductProfitSummary


class OrderItemCalculationSerializer(serializers.ModelSerializer):
    """Serializer for detailed calculation display."""
    
    order_number = serializers.CharField(
        source='order_item.order.trendyol_order_number',
        read_only=True
    )
    barcode = serializers.CharField(source='order_item.barcode', read_only=True)
    product_name = serializers.CharField(source='order_item.product_name', read_only=True)
    quantity = serializers.IntegerField(source='order_item.quantity', read_only=True)
    
    class Meta:
        model = OrderItemCalculation
        fields = [
            'id', 'order_number', 'barcode', 'product_name', 'quantity',
            'calculated_at',
            
            # Revenue
            'gross_sale_price', 'discount_amount', 'net_sale_price',
            'net_sale_price_excl_vat', 'sales_vat_rate', 'sales_vat',
            
            # Product cost
            'product_cost_excl_vat', 'purchase_vat_rate', 'purchase_vat',
            'product_cost_incl_vat',
            
            # Commission
            'commission_rate', 'commission_amount_excl_vat',
            'commission_vat_rate', 'commission_vat', 'commission_total',
            
            # Cargo
            'cargo_cost_excl_vat', 'cargo_vat_rate', 'cargo_vat', 'cargo_cost_total',
            
            # Platform
            'platform_fee_excl_vat', 'platform_fee_vat_rate',
            'platform_fee_vat', 'platform_fee_total',
            
            # Withholding
            'withholding_tax_rate', 'withholding_tax',
            
            # VAT
            'total_output_vat', 'total_input_vat', 'net_vat_payable',
            
            # Totals
            'total_trendyol_deductions', 'total_cost',
            'net_profit', 'profit_margin_percent',
            
            # Flags
            'is_profitable', 'has_cost_data', 'calculation_notes',
        ]


class OrderItemCalculationSummarySerializer(serializers.ModelSerializer):
    """Compact serializer for calculation listings."""
    
    order_number = serializers.CharField(
        source='order_item.order.trendyol_order_number',
        read_only=True
    )
    order_date = serializers.DateTimeField(
        source='order_item.order.order_date',
        read_only=True
    )
    barcode = serializers.CharField(source='order_item.barcode', read_only=True)
    product_name = serializers.CharField(source='order_item.product_name', read_only=True)
    quantity = serializers.IntegerField(source='order_item.quantity', read_only=True)
    
    class Meta:
        model = OrderItemCalculation
        fields = [
            'id', 'order_number', 'order_date',
            'barcode', 'product_name', 'quantity',
            'net_sale_price_excl_vat', 'total_cost', 'net_profit',
            'profit_margin_percent', 'is_profitable', 'has_cost_data',
        ]


class DailyProfitSummarySerializer(serializers.ModelSerializer):
    """Serializer for daily summary."""
    
    seller_name = serializers.CharField(
        source='seller_account.shop_name',
        read_only=True
    )
    
    class Meta:
        model = DailyProfitSummary
        fields = [
            'id', 'date', 'seller_name',
            'total_orders', 'total_items',
            'total_revenue', 'total_revenue_excl_vat',
            'total_product_cost', 'total_commission',
            'total_cargo_cost', 'total_platform_fee',
            'total_vat_payable', 'total_cost', 'total_profit',
            'average_margin',
            'items_with_cost', 'items_without_cost',
            'calculated_at',
        ]


class ProductProfitSummarySerializer(serializers.ModelSerializer):
    """Serializer for product profit summary."""
    
    barcode = serializers.CharField(source='product.barcode', read_only=True)
    product_name = serializers.CharField(source='product.title', read_only=True)
    product_cost = serializers.DecimalField(
        source='product.product_cost_excl_vat',
        max_digits=12,
        decimal_places=2,
        read_only=True
    )
    
    class Meta:
        model = ProductProfitSummary
        fields = [
            'id', 'barcode', 'product_name', 'product_cost',
            'total_quantity_sold', 'total_revenue', 'total_cost', 'total_profit',
            'average_profit_per_item', 'average_margin', 'is_profitable',
            'last_30_days_quantity', 'last_30_days_profit',
            'calculated_at',
        ]


class CalculationBreakdownSerializer(serializers.Serializer):
    """Serializer for calculation breakdown (front-end display)."""
    
    # Revenue section
    revenue = serializers.DictField()
    # Product cost section  
    product_cost = serializers.DictField()
    # Commission section
    commission = serializers.DictField()
    # Cargo section
    cargo = serializers.DictField()
    # Platform section
    platform_fee = serializers.DictField()
    # VAT settlement section
    vat_settlement = serializers.DictField()
    # Summary section
    summary = serializers.DictField()
    # Audit info
    audit = serializers.DictField()
    
    @classmethod
    def from_calculation(cls, calc: OrderItemCalculation) -> dict:
        """Create breakdown from calculation model."""
        return {
            'revenue': {
                'gross_sale_price': str(calc.gross_sale_price),
                'discount_amount': str(calc.discount_amount),
                'net_sale_price': str(calc.net_sale_price),
                'net_sale_price_excl_vat': str(calc.net_sale_price_excl_vat),
                'sales_vat': str(calc.sales_vat),
                'sales_vat_rate': str(calc.sales_vat_rate),
            },
            'product_cost': {
                'cost_excl_vat': str(calc.product_cost_excl_vat),
                'purchase_vat': str(calc.purchase_vat),
                'cost_incl_vat': str(calc.product_cost_incl_vat),
                'vat_rate': str(calc.purchase_vat_rate),
            },
            'commission': {
                'rate': str(calc.commission_rate),
                'amount_excl_vat': str(calc.commission_amount_excl_vat),
                'vat': str(calc.commission_vat),
                'total': str(calc.commission_total),
            },
            'cargo': {
                'cost_excl_vat': str(calc.cargo_cost_excl_vat),
                'vat': str(calc.cargo_vat),
                'total': str(calc.cargo_cost_total),
            },
            'platform_fee': {
                'fee_excl_vat': str(calc.platform_fee_excl_vat),
                'vat': str(calc.platform_fee_vat),
                'total': str(calc.platform_fee_total),
            },
            'vat_settlement': {
                'output_vat': str(calc.total_output_vat),
                'input_vat': str(calc.total_input_vat),
                'net_vat_payable': str(calc.net_vat_payable),
                'note': 'Ödenecek KDV (Hesaplanan - İndirilecek)',
            },
            'summary': {
                'total_trendyol_deductions': str(calc.total_trendyol_deductions),
                'total_cost': str(calc.total_cost),
                'net_profit': str(calc.net_profit),
                'profit_margin_percent': str(calc.profit_margin_percent),
                'is_profitable': calc.is_profitable,
            },
            'audit': {
                'calculated_at': calc.calculated_at.isoformat(),
                'calculation_version': calc.calculation_version,
                'has_cost_data': calc.has_cost_data,
                'notes': calc.calculation_notes,
            },
        }
