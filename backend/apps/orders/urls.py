"""
Orders App - URL Configuration
"""

from django.urls import path
from .views import (
    OrderListView,
    OrderDetailView,
    OrderItemsView,
    OrderSummaryView,
    RecentOrdersView,
    OrdersByProductView,
)

app_name = 'orders'

urlpatterns = [
    path('', OrderListView.as_view(), name='list'),
    path('summary/', OrderSummaryView.as_view(), name='summary'),
    path('recent/', RecentOrdersView.as_view(), name='recent'),
    path('<int:pk>/', OrderDetailView.as_view(), name='detail'),
    path('<int:pk>/items/', OrderItemsView.as_view(), name='items'),
    path('by-product/<str:barcode>/', OrdersByProductView.as_view(), name='by_product'),
]
