"""
Calculations App - URL Configuration
"""

from django.urls import path
from .views import (
    OrderItemCalculationView,
    OrderItemCalculationByOrderView,
    CalculationBreakdownView,
    TriggerCalculationView,
    RecalculateProductView,
    DailySummaryListView,
    ProductProfitListView,
    LossProductsView,
    TopProfitableProductsView,
)

app_name = 'calculations'

urlpatterns = [
    # Item calculations
    path('<int:pk>/', OrderItemCalculationView.as_view(), name='detail'),
    path('<int:pk>/breakdown/', CalculationBreakdownView.as_view(), name='breakdown'),
    path('order/<int:order_id>/', OrderItemCalculationByOrderView.as_view(), name='by_order'),
    
    # Trigger calculations
    path('trigger/order/<int:order_id>/', TriggerCalculationView.as_view(), name='trigger_order'),
    path('recalculate/product/<int:product_id>/', RecalculateProductView.as_view(), name='recalculate_product'),
    
    # Summaries
    path('daily/', DailySummaryListView.as_view(), name='daily_summaries'),
    path('products/', ProductProfitListView.as_view(), name='product_profits'),
    path('products/loss/', LossProductsView.as_view(), name='loss_products'),
    path('products/top/', TopProfitableProductsView.as_view(), name='top_products'),
]
