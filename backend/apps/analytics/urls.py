"""Analytics App - URL Configuration"""

from django.urls import path
from .views import (
    DashboardView,
    DailyChartDataView,
    MonthlyChartDataView,
    CostBreakdownView,
    ProductProfitChartView,
)

app_name = 'analytics'

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('daily/', DailyChartDataView.as_view(), name='daily_chart'),
    path('monthly/', MonthlyChartDataView.as_view(), name='monthly_chart'),
    path('cost-breakdown/', CostBreakdownView.as_view(), name='cost_breakdown'),
    path('products/', ProductProfitChartView.as_view(), name='product_chart'),
]
