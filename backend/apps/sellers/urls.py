"""
Sellers App - URL Configuration
"""

from django.urls import path
from .views import (
    SellerAccountListCreateView,
    SellerAccountDetailView,
    TriggerSyncView,
    SellerSyncStatusView,
    SellerSyncLogsView,
    TestCredentialsView,
)

app_name = 'sellers'

urlpatterns = [
    # CRUD
    path('', SellerAccountListCreateView.as_view(), name='list_create'),
    path('<int:pk>/', SellerAccountDetailView.as_view(), name='detail'),
    
    # Sync operations
    path('<int:pk>/sync/', TriggerSyncView.as_view(), name='trigger_sync'),
    path('<int:pk>/sync-status/', SellerSyncStatusView.as_view(), name='sync_status'),
    path('<int:pk>/sync-logs/', SellerSyncLogsView.as_view(), name='sync_logs'),
    
    # Validation
    path('<int:pk>/test-credentials/', TestCredentialsView.as_view(), name='test_credentials'),
]
