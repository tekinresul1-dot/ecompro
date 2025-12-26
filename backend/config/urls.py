"""
URL Configuration for Trendyol Profitability SaaS

The `urlpatterns` list routes URLs to views.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API v1 endpoints
    path('api/v1/', include([
        # Authentication
        path('auth/', include('apps.accounts.urls')),
        
        # Seller Accounts
        path('sellers/', include('apps.sellers.urls')),
        
        # Products
        path('products/', include('apps.products.urls')),
        
        # Orders
        path('orders/', include('apps.orders.urls')),
        
        # Calculations
        path('calculations/', include('apps.calculations.urls')),
        
        # Analytics & Dashboard
        path('analytics/', include('apps.analytics.urls')),
    ])),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
