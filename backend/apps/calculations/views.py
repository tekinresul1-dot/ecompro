"""
Calculations App - Views
"""

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import OrderItemCalculation, DailyProfitSummary, ProductProfitSummary
from .serializers import (
    OrderItemCalculationSerializer,
    OrderItemCalculationSummarySerializer,
    DailyProfitSummarySerializer,
    ProductProfitSummarySerializer,
    CalculationBreakdownSerializer,
)
from .services import get_calculation_service


class OrderItemCalculationView(generics.RetrieveAPIView):
    """
    Get calculation details for an order item.
    """
    serializer_class = OrderItemCalculationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return OrderItemCalculation.objects.filter(
            order_item__order__seller_account__user=self.request.user
        ).select_related('order_item', 'order_item__order')


class OrderItemCalculationByOrderView(generics.ListAPIView):
    """
    Get all calculations for an order.
    """
    serializer_class = OrderItemCalculationSummarySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        order_id = self.kwargs.get('order_id')
        return OrderItemCalculation.objects.filter(
            order_item__order_id=order_id,
            order_item__order__seller_account__user=self.request.user
        ).select_related('order_item', 'order_item__order')


class CalculationBreakdownView(APIView):
    """
    Get detailed calculation breakdown for an order item.
    
    Returns structured data for frontend display.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        try:
            calc = OrderItemCalculation.objects.get(
                pk=pk,
                order_item__order__seller_account__user=request.user
            )
        except OrderItemCalculation.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Hesaplama bulunamadı.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        breakdown = CalculationBreakdownSerializer.from_calculation(calc)
        
        return Response({
            'success': True,
            'data': {
                'order_number': calc.order_item.order.trendyol_order_number,
                'order_date': calc.order_item.order.order_date,
                'item': {
                    'barcode': calc.order_item.barcode,
                    'product_name': calc.order_item.product_name,
                    'quantity': calc.order_item.quantity,
                },
                'calculation': breakdown,
            }
        })


class TriggerCalculationView(APIView):
    """
    Trigger calculation for an order or order item.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, order_id):
        from apps.orders.models import Order
        
        try:
            order = Order.objects.get(
                pk=order_id,
                seller_account__user=request.user
            )
        except Order.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Sipariş bulunamadı.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        service = get_calculation_service()
        calcs = service.calculate_order(order)
        
        return Response({
            'success': True,
            'message': f'{len(calcs)} kalem için hesaplama yapıldı.',
            'data': {
                'order_id': order_id,
                'items_calculated': len(calcs),
            }
        })


class RecalculateProductView(APIView):
    """
    Recalculate all order items for a product.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, product_id):
        from apps.products.models import Product
        
        try:
            product = Product.objects.get(
                pk=product_id,
                seller_account__user=request.user
            )
        except Product.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Ürün bulunamadı.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        service = get_calculation_service()
        count = service.recalculate_for_product(product_id)
        
        # Update product summary
        service.update_product_summary(product_id)
        
        return Response({
            'success': True,
            'message': f'{count} sipariş kalemi yeniden hesaplandı.',
            'data': {
                'product_id': product_id,
                'barcode': product.barcode,
                'items_recalculated': count,
            }
        })


class DailySummaryListView(generics.ListAPIView):
    """
    List daily profit summaries.
    """
    serializer_class = DailyProfitSummarySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = DailyProfitSummary.objects.filter(
            seller_account__user=self.request.user
        ).select_related('seller_account')
        
        params = self.request.query_params
        
        seller_account = params.get('seller_account')
        if seller_account:
            queryset = queryset.filter(seller_account_id=seller_account)
        
        start_date = params.get('start_date')
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        
        end_date = params.get('end_date')
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        return queryset.order_by('-date')


class ProductProfitListView(generics.ListAPIView):
    """
    List product profit summaries.
    """
    serializer_class = ProductProfitSummarySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = ProductProfitSummary.objects.filter(
            product__seller_account__user=self.request.user
        ).select_related('product')
        
        params = self.request.query_params
        
        seller_account = params.get('seller_account')
        if seller_account:
            queryset = queryset.filter(product__seller_account_id=seller_account)
        
        # Filter by profitability
        profitable = params.get('profitable')
        if profitable is not None:
            queryset = queryset.filter(is_profitable=profitable.lower() == 'true')
        
        # Ordering
        order_by = params.get('order_by', '-total_profit')
        if order_by in ['-total_profit', 'total_profit', '-average_margin', 
                        'average_margin', '-total_quantity_sold']:
            queryset = queryset.order_by(order_by)
        
        return queryset


class LossProductsView(generics.ListAPIView):
    """
    List products with negative profit (loss-making).
    """
    serializer_class = ProductProfitSummarySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = ProductProfitSummary.objects.filter(
            product__seller_account__user=self.request.user,
            is_profitable=False
        ).select_related('product')
        
        seller_account = self.request.query_params.get('seller_account')
        if seller_account:
            queryset = queryset.filter(product__seller_account_id=seller_account)
        
        return queryset.order_by('total_profit')[:50]


class TopProfitableProductsView(generics.ListAPIView):
    """
    List most profitable products.
    """
    serializer_class = ProductProfitSummarySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = ProductProfitSummary.objects.filter(
            product__seller_account__user=self.request.user,
            is_profitable=True
        ).select_related('product')
        
        seller_account = self.request.query_params.get('seller_account')
        if seller_account:
            queryset = queryset.filter(product__seller_account_id=seller_account)
        
        return queryset.order_by('-total_profit')[:50]
