"""
Orders App - Views
"""

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import Order, OrderItem
from .serializers import (
    OrderSerializer,
    OrderDetailSerializer,
    OrderItemSerializer,
    OrderSummarySerializer,
)


class OrderListView(generics.ListAPIView):
    """
    List orders with filtering support.
    
    Filters:
    - seller_account: Filter by seller
    - status: Filter by order status
    - start_date: Orders from this date
    - end_date: Orders until this date
    - search: Search by order number
    - barcode: Search by product barcode
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Order.objects.filter(
            seller_account__user=user
        ).select_related('seller_account')
        
        params = self.request.query_params
        
        seller_account = params.get('seller_account')
        if seller_account:
            queryset = queryset.filter(seller_account_id=seller_account)
        
        order_status = params.get('status')
        if order_status:
            queryset = queryset.filter(status=order_status)
        
        start_date = params.get('start_date')
        if start_date:
            queryset = queryset.filter(order_date__date__gte=start_date)
        
        end_date = params.get('end_date')
        if end_date:
            queryset = queryset.filter(order_date__date__lte=end_date)
        
        search = params.get('search')
        if search:
            queryset = queryset.filter(trendyol_order_number__icontains=search)
        
        barcode = params.get('barcode')
        if barcode:
            queryset = queryset.filter(items__barcode=barcode).distinct()
        
        return queryset.order_by('-order_date')


class OrderDetailView(generics.RetrieveAPIView):
    """
    Get order details with all items.
    """
    serializer_class = OrderDetailSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Order.objects.filter(
            seller_account__user=self.request.user
        ).prefetch_related('items', 'items__product')


class OrderItemsView(generics.ListAPIView):
    """
    Get items for a specific order.
    """
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        order_id = self.kwargs.get('pk')
        return OrderItem.objects.filter(
            order_id=order_id,
            order__seller_account__user=self.request.user
        ).select_related('product')


class OrderSummaryView(APIView):
    """
    Get order summary statistics.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        params = request.query_params
        
        queryset = Order.objects.filter(seller_account__user=user)
        
        # Apply filters
        seller_account = params.get('seller_account')
        if seller_account:
            queryset = queryset.filter(seller_account_id=seller_account)
        
        start_date = params.get('start_date')
        if start_date:
            queryset = queryset.filter(order_date__date__gte=start_date)
        
        end_date = params.get('end_date')
        if end_date:
            queryset = queryset.filter(order_date__date__lte=end_date)
        
        # Calculate summary
        summary = queryset.aggregate(
            total_orders=Count('id'),
            total_revenue=Sum('total_price'),
            total_discount=Sum('total_discount'),
        )
        
        total_items = OrderItem.objects.filter(
            order__in=queryset
        ).aggregate(total=Sum('quantity'))['total'] or 0
        
        # Count by status
        status_counts = queryset.values('status').annotate(
            count=Count('id')
        )
        by_status = {item['status']: item['count'] for item in status_counts}
        
        data = {
            'total_orders': summary['total_orders'] or 0,
            'total_items': total_items,
            'total_revenue': summary['total_revenue'] or 0,
            'total_discount': summary['total_discount'] or 0,
            'by_status': by_status,
        }
        
        return Response({
            'success': True,
            'data': data
        })


class RecentOrdersView(generics.ListAPIView):
    """
    Get recent orders (last 7 days).
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        seven_days_ago = timezone.now() - timedelta(days=7)
        return Order.objects.filter(
            seller_account__user=self.request.user,
            order_date__gte=seven_days_ago
        ).select_related('seller_account').order_by('-order_date')[:50]


class OrdersByProductView(generics.ListAPIView):
    """
    Get orders containing a specific product (by barcode).
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        barcode = self.kwargs.get('barcode')
        return Order.objects.filter(
            seller_account__user=self.request.user,
            items__barcode=barcode
        ).distinct().order_by('-order_date')[:100]
