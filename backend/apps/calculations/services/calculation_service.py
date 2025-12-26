"""
Calculation Service

High-level service for calculating and storing order item profits.
"""

import logging
from typing import List, Optional, Tuple
from decimal import Decimal
from datetime import date, timedelta

from django.db import transaction
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone

from apps.orders.models import Order, OrderItem
from apps.calculations.models import (
    OrderItemCalculation,
    DailyProfitSummary,
    ProductProfitSummary,
)
from .profit_calculator import ProfitCalculator, CalculationResult, get_calculator

logger = logging.getLogger(__name__)


class CalculationService:
    """
    Service for calculating and storing profit data.
    """
    
    def __init__(self, calculator: Optional[ProfitCalculator] = None):
        self.calculator = calculator or get_calculator()
    
    @transaction.atomic
    def calculate_order_item(self, order_item: OrderItem) -> OrderItemCalculation:
        """
        Calculate and store profit for a single order item.
        
        Args:
            order_item: OrderItem to calculate
            
        Returns:
            OrderItemCalculation model instance
        """
        # Link product if not already linked
        if not order_item.product:
            order_item.link_product()
        
        # Calculate
        result = self.calculator.calculate_for_order_item(order_item)
        
        # Store or update
        calc, created = OrderItemCalculation.objects.update_or_create(
            order_item=order_item,
            defaults={
                # Revenue
                'gross_sale_price': result.gross_sale_price,
                'discount_amount': result.discount_amount,
                'net_sale_price': result.net_sale_price,
                
                # Product cost
                'product_cost_excl_vat': result.product_cost_excl_vat,
                'purchase_vat_rate': result.purchase_vat_rate,
                'purchase_vat': result.purchase_vat,
                'product_cost_incl_vat': result.product_cost_incl_vat,
                
                # Sales VAT
                'sales_vat_rate': result.sales_vat_rate,
                'sales_vat': result.sales_vat,
                'net_sale_price_excl_vat': result.net_sale_price_excl_vat,
                
                # Commission
                'commission_rate': result.commission_rate,
                'commission_amount_excl_vat': result.commission_amount_excl_vat,
                'commission_vat_rate': result.commission_vat_rate,
                'commission_vat': result.commission_vat,
                'commission_total': result.commission_total,
                
                # Cargo
                'cargo_cost_excl_vat': result.cargo_cost_excl_vat,
                'cargo_vat_rate': result.cargo_vat_rate,
                'cargo_vat': result.cargo_vat,
                'cargo_cost_total': result.cargo_cost_total,
                
                # Platform fee
                'platform_fee_excl_vat': result.platform_fee_excl_vat,
                'platform_fee_vat_rate': result.platform_fee_vat_rate,
                'platform_fee_vat': result.platform_fee_vat,
                'platform_fee_total': result.platform_fee_total,
                
                # Withholding
                'withholding_tax_rate': result.withholding_tax_rate,
                'withholding_tax': result.withholding_tax,
                
                # VAT
                'total_output_vat': result.total_output_vat,
                'total_input_vat': result.total_input_vat,
                'net_vat_payable': result.net_vat_payable,
                
                # Totals
                'total_trendyol_deductions': result.total_trendyol_deductions,
                'total_cost': result.total_cost,
                
                # Profit
                'net_profit': result.net_profit,
                'profit_margin_percent': result.profit_margin_percent,
                
                # Flags
                'is_profitable': result.is_profitable,
                'has_cost_data': result.has_cost_data,
                'calculation_notes': result.calculation_notes,
            }
        )
        
        # Mark order item as calculated
        order_item.is_calculated = True
        order_item.save(update_fields=['is_calculated'])
        
        return calc
    
    def calculate_order(self, order: Order) -> List[OrderItemCalculation]:
        """
        Calculate profits for all items in an order.
        
        Args:
            order: Order to process
            
        Returns:
            List of OrderItemCalculation instances
        """
        results = []
        for item in order.items.all():
            if item.is_revenue_item:
                calc = self.calculate_order_item(item)
                results.append(calc)
        return results
    
    def calculate_uncalculated_items(
        self,
        seller_account_id: int,
        limit: int = 1000
    ) -> Tuple[int, int]:
        """
        Calculate profits for uncalculated order items.
        
        Args:
            seller_account_id: Seller account to process
            limit: Maximum items to process
            
        Returns:
            Tuple of (processed_count, error_count)
        """
        items = OrderItem.objects.filter(
            order__seller_account_id=seller_account_id,
            is_calculated=False,
            item_status='active'
        ).select_related('order', 'product')[:limit]
        
        processed = 0
        errors = 0
        
        for item in items:
            try:
                self.calculate_order_item(item)
                processed += 1
            except Exception as e:
                logger.error(f'Error calculating item {item.id}: {e}')
                errors += 1
        
        return processed, errors
    
    @transaction.atomic
    def recalculate_for_product(self, product_id: int) -> int:
        """
        Recalculate all order items for a product.
        
        Useful when product cost is updated.
        
        Args:
            product_id: Product ID
            
        Returns:
            Number of items recalculated
        """
        items = OrderItem.objects.filter(
            product_id=product_id,
            item_status='active'
        ).select_related('order', 'product')
        
        count = 0
        for item in items:
            self.calculate_order_item(item)
            count += 1
        
        return count
    
    @transaction.atomic
    def update_daily_summary(self, seller_account_id: int, target_date: date) -> DailyProfitSummary:
        """
        Update or create daily profit summary.
        
        Args:
            seller_account_id: Seller account
            target_date: Date to summarize
            
        Returns:
            DailyProfitSummary instance
        """
        # Get all calculations for the date
        calcs = OrderItemCalculation.objects.filter(
            order_item__order__seller_account_id=seller_account_id,
            order_item__order__order_date__date=target_date,
            order_item__item_status='active'
        )
        
        # Aggregate
        agg = calcs.aggregate(
            total_items=Count('id'),
            total_revenue=Sum('net_sale_price'),
            total_revenue_excl_vat=Sum('net_sale_price_excl_vat'),
            total_product_cost=Sum('product_cost_excl_vat'),
            total_commission=Sum('commission_amount_excl_vat'),
            total_cargo=Sum('cargo_cost_excl_vat'),
            total_platform=Sum('platform_fee_excl_vat'),
            total_vat=Sum('net_vat_payable'),
            total_cost=Sum('total_cost'),
            total_profit=Sum('net_profit'),
            items_with_cost=Count('id', filter=Q(has_cost_data=True)),
            items_without_cost=Count('id', filter=Q(has_cost_data=False)),
        )
        
        # Count orders
        order_count = Order.objects.filter(
            seller_account_id=seller_account_id,
            order_date__date=target_date
        ).count()
        
        # Calculate average margin
        total_revenue_excl_vat = agg['total_revenue_excl_vat'] or Decimal('0')
        total_profit = agg['total_profit'] or Decimal('0')
        
        if total_revenue_excl_vat > 0:
            avg_margin = (total_profit / total_revenue_excl_vat) * 100
        else:
            avg_margin = Decimal('0')
        
        # Update or create summary
        summary, _ = DailyProfitSummary.objects.update_or_create(
            seller_account_id=seller_account_id,
            date=target_date,
            defaults={
                'total_orders': order_count,
                'total_items': agg['total_items'] or 0,
                'total_revenue': agg['total_revenue'] or Decimal('0'),
                'total_revenue_excl_vat': total_revenue_excl_vat,
                'total_product_cost': agg['total_product_cost'] or Decimal('0'),
                'total_commission': agg['total_commission'] or Decimal('0'),
                'total_cargo_cost': agg['total_cargo'] or Decimal('0'),
                'total_platform_fee': agg['total_platform'] or Decimal('0'),
                'total_vat_payable': agg['total_vat'] or Decimal('0'),
                'total_cost': agg['total_cost'] or Decimal('0'),
                'total_profit': total_profit,
                'average_margin': avg_margin,
                'items_with_cost': agg['items_with_cost'] or 0,
                'items_without_cost': agg['items_without_cost'] or 0,
            }
        )
        
        return summary
    
    def update_daily_summaries_range(
        self,
        seller_account_id: int,
        start_date: date,
        end_date: date
    ) -> int:
        """
        Update daily summaries for a date range.
        
        Args:
            seller_account_id: Seller account
            start_date: Start date
            end_date: End date
            
        Returns:
            Number of days updated
        """
        count = 0
        current = start_date
        
        while current <= end_date:
            self.update_daily_summary(seller_account_id, current)
            current += timedelta(days=1)
            count += 1
        
        return count
    
    @transaction.atomic
    def update_product_summary(self, product_id: int) -> ProductProfitSummary:
        """
        Update profit summary for a product.
        
        Args:
            product_id: Product ID
            
        Returns:
            ProductProfitSummary instance
        """
        from apps.products.models import Product
        
        product = Product.objects.get(pk=product_id)
        
        # All-time stats
        calcs = OrderItemCalculation.objects.filter(
            order_item__product_id=product_id,
            order_item__item_status='active'
        )
        
        all_time = calcs.aggregate(
            total_qty=Sum('order_item__quantity'),
            total_revenue=Sum('net_sale_price_excl_vat'),
            total_cost=Sum('total_cost'),
            total_profit=Sum('net_profit'),
        )
        
        # Last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        last_30 = calcs.filter(
            order_item__order__order_date__gte=thirty_days_ago
        ).aggregate(
            qty=Sum('order_item__quantity'),
            profit=Sum('net_profit'),
        )
        
        # Calculate averages
        total_qty = all_time['total_qty'] or 0
        total_profit = all_time['total_profit'] or Decimal('0')
        total_revenue = all_time['total_revenue'] or Decimal('0')
        
        if total_qty > 0:
            avg_profit_per_item = total_profit / total_qty
        else:
            avg_profit_per_item = Decimal('0')
        
        if total_revenue > 0:
            avg_margin = (total_profit / total_revenue) * 100
        else:
            avg_margin = Decimal('0')
        
        summary, _ = ProductProfitSummary.objects.update_or_create(
            product_id=product_id,
            defaults={
                'total_quantity_sold': total_qty,
                'total_revenue': total_revenue,
                'total_cost': all_time['total_cost'] or Decimal('0'),
                'total_profit': total_profit,
                'average_profit_per_item': avg_profit_per_item,
                'average_margin': avg_margin,
                'is_profitable': total_profit > 0,
                'last_30_days_quantity': last_30['qty'] or 0,
                'last_30_days_profit': last_30['profit'] or Decimal('0'),
            }
        )
        
        return summary


# Convenience function
def get_calculation_service() -> CalculationService:
    """Get a calculation service instance."""
    return CalculationService()
