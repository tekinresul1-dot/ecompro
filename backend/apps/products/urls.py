"""
Products App - URL Configuration
"""

from django.urls import path
from .views import (
    ProductListView,
    ProductDetailView,
    ProductCostUpdateView,
    ProductCostHistoryView,
    BulkCostUploadView,
    BulkCostUploadStatusView,
    BulkCostUploadListView,
    ProductsWithoutCostView,
    ProductExportView,
)

app_name = 'products'

urlpatterns = [
    # Product CRUD
    path('', ProductListView.as_view(), name='list'),
    path('<int:pk>/', ProductDetailView.as_view(), name='detail'),
    path('<int:pk>/cost/', ProductCostUpdateView.as_view(), name='update_cost'),
    path('<int:pk>/cost-history/', ProductCostHistoryView.as_view(), name='cost_history'),
    
    # Bulk operations
    path('bulk-upload/', BulkCostUploadView.as_view(), name='bulk_upload'),
    path('bulk-upload/<int:pk>/status/', BulkCostUploadStatusView.as_view(), name='bulk_upload_status'),
    path('bulk-uploads/', BulkCostUploadListView.as_view(), name='bulk_upload_list'),
    
    # Special views
    path('without-cost/', ProductsWithoutCostView.as_view(), name='without_cost'),
    path('export/', ProductExportView.as_view(), name='export'),
]
