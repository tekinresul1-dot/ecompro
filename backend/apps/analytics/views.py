"""
Analytics App - Dashboard and Reporting Views
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Avg, Q, F
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from apps.orders.models import Order, OrderItem
from apps.calculations.models import (
    OrderItemCalculation,
    DailyProfitSummary,
    ProductProfitSummary,
)
from apps.products.models import Product


class DashboardView(APIView):
    """
    Main dashboard data endpoint.
    Returns comprehensive summary statistics.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        params = request.query_params
        
        # Date range
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
        if params.get('start_date'):
            from datetime import datetime
            start_date = datetime.strptime(params['start_date'], '%Y-%m-%d').date()
        if params.get('end_date'):
            from datetime import datetime
            end_date = datetime.strptime(params['end_date'], '%Y-%m-%d').date()
        
        # Filter by seller
        seller_filter = {}
        if params.get('seller_account'):
            seller_filter['seller_account_id'] = params['seller_account']
        
        # Get daily summaries
        summaries = DailyProfitSummary.objects.filter(
            seller_account__user=user,
            date__gte=start_date,
            date__lte=end_date,
            **seller_filter
        )
        
        # Aggregate totals
        totals = summaries.aggregate(
            total_revenue=Sum('total_revenue'),
            total_cost=Sum('total_cost'),
            total_profit=Sum('total_profit'),
            total_orders=Sum('total_orders'),
            total_items=Sum('total_items'),
            total_commission=Sum('total_commission'),
            total_cargo=Sum('total_cargo_cost'),
            total_platform=Sum('total_platform_fee'),
            items_with_cost=Sum('items_with_cost'),
            items_without_cost=Sum('items_without_cost'),
        )
        
        # Calculate averages
        total_revenue = totals['total_revenue'] or Decimal('0')
        total_profit = totals['total_profit'] or Decimal('0')
        
        if total_revenue > 0:
            avg_margin = (total_profit / total_revenue) * 100
        else:
            avg_margin = Decimal('0')
        
        # Top profitable products
        top_products = ProductProfitSummary.objects.filter(
            product__seller_account__user=user,
            is_profitable=True,
            **{f'product__{k}': v for k, v in seller_filter.items()}
        ).select_related('product').order_by('-total_profit')[:5]
        
        # Loss-making products
        loss_products = ProductProfitSummary.objects.filter(
            product__seller_account__user=user,
            is_profitable=False,
            **{f'product__{k}': v for k, v in seller_filter.items()}
        ).select_related('product').order_by('total_profit')[:5]
        
        return Response({
            'success': True,
            'data': {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                },
                'summary': {
                    'total_revenue': str(total_revenue),
                    'total_cost': str(totals['total_cost'] or 0),
                    'net_profit': str(total_profit),
                    'average_profit_margin': str(round(avg_margin, 2)),
                    'total_orders': totals['total_orders'] or 0,
                    'total_items': totals['total_items'] or 0,
                },
                'cost_breakdown': {
                    'product_cost': str(totals['total_cost'] or 0),
                    'commission': str(totals['total_commission'] or 0),
                    'cargo': str(totals['total_cargo'] or 0),
                    'platform_fee': str(totals['total_platform'] or 0),
                },
                'data_quality': {
                    'items_with_cost': totals['items_with_cost'] or 0,
                    'items_without_cost': totals['items_without_cost'] or 0,
                },
                'top_profitable_products': [
                    {
                        'barcode': p.product.barcode,
                        'product_name': p.product.title,
                        'total_profit': str(p.total_profit),
                        'avg_margin': str(p.average_margin),
                        'quantity_sold': p.total_quantity_sold,
                    }
                    for p in top_products
                ],
                'loss_making_products': [
                    {
                        'barcode': p.product.barcode,
                        'product_name': p.product.title,
                        'total_loss': str(p.total_profit),
                        'avg_margin': str(p.average_margin),
                        'quantity_sold': p.total_quantity_sold,
                    }
                    for p in loss_products
                ],
            }
        })


class DailyChartDataView(APIView):
    """Daily profit chart data."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        params = request.query_params
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
        if params.get('start_date'):
            from datetime import datetime
            start_date = datetime.strptime(params['start_date'], '%Y-%m-%d').date()
        if params.get('end_date'):
            from datetime import datetime
            end_date = datetime.strptime(params['end_date'], '%Y-%m-%d').date()
        
        queryset = DailyProfitSummary.objects.filter(
            seller_account__user=user,
            date__gte=start_date,
            date__lte=end_date,
        )
        
        if params.get('seller_account'):
            queryset = queryset.filter(seller_account_id=params['seller_account'])
        
        # Aggregate by date
        data = queryset.values('date').annotate(
            revenue=Sum('total_revenue'),
            cost=Sum('total_cost'),
            profit=Sum('total_profit'),
            orders=Sum('total_orders'),
        ).order_by('date')
        
        return Response({
            'success': True,
            'data': [
                {
                    'date': item['date'].isoformat(),
                    'revenue': str(item['revenue'] or 0),
                    'cost': str(item['cost'] or 0),
                    'profit': str(item['profit'] or 0),
                    'orders': item['orders'] or 0,
                }
                for item in data
            ]
        })


class MonthlyChartDataView(APIView):
    """Monthly profit chart data."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from django.db.models.functions import TruncMonth
        
        user = request.user
        params = request.query_params
        
        queryset = DailyProfitSummary.objects.filter(
            seller_account__user=user,
        )
        
        if params.get('seller_account'):
            queryset = queryset.filter(seller_account_id=params['seller_account'])
        
        data = queryset.annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            revenue=Sum('total_revenue'),
            cost=Sum('total_cost'),
            profit=Sum('total_profit'),
            orders=Sum('total_orders'),
        ).order_by('month')
        
        return Response({
            'success': True,
            'data': [
                {
                    'month': item['month'].strftime('%Y-%m'),
                    'revenue': str(item['revenue'] or 0),
                    'cost': str(item['cost'] or 0),
                    'profit': str(item['profit'] or 0),
                    'orders': item['orders'] or 0,
                }
                for item in data
            ]
        })


class CostBreakdownView(APIView):
    """Cost breakdown for pie chart."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        params = request.query_params
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
        if params.get('start_date'):
            from datetime import datetime
            start_date = datetime.strptime(params['start_date'], '%Y-%m-%d').date()
        if params.get('end_date'):
            from datetime import datetime
            end_date = datetime.strptime(params['end_date'], '%Y-%m-%d').date()
        
        queryset = DailyProfitSummary.objects.filter(
            seller_account__user=user,
            date__gte=start_date,
            date__lte=end_date,
        )
        
        if params.get('seller_account'):
            queryset = queryset.filter(seller_account_id=params['seller_account'])
        
        totals = queryset.aggregate(
            product_cost=Sum('total_product_cost'),
            commission=Sum('total_commission'),
            cargo=Sum('total_cargo_cost'),
            platform=Sum('total_platform_fee'),
            vat=Sum('total_vat_payable'),
        )
        
        return Response({
            'success': True,
            'data': [
                {'name': 'Ürün Maliyeti', 'value': float(totals['product_cost'] or 0)},
                {'name': 'Komisyon', 'value': float(totals['commission'] or 0)},
                {'name': 'Kargo', 'value': float(totals['cargo'] or 0)},
                {'name': 'Platform Ücreti', 'value': float(totals['platform'] or 0)},
                {'name': 'KDV', 'value': float(totals['vat'] or 0)},
            ]
        })


class ProductProfitChartView(APIView):
    """Product profit distribution chart."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        params = request.query_params
        
        queryset = ProductProfitSummary.objects.filter(
            product__seller_account__user=user,
        ).select_related('product')
        
        if params.get('seller_account'):
            queryset = queryset.filter(product__seller_account_id=params['seller_account'])
        
        # Top 10 by profit
        top_10 = queryset.order_by('-total_profit')[:10]
        
        return Response({
            'success': True,
            'data': [
                {
                    'barcode': p.product.barcode,
                    'name': p.product.title[:30],
                    'profit': float(p.total_profit),
                    'quantity': p.total_quantity_sold,
                }
                for p in top_10
            ]
        })
