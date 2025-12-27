"""
Sellers App - Views
"""

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import SellerAccount, SellerSyncLog
from .serializers import (
    SellerAccountSerializer,
    SellerAccountCreateSerializer,
    SellerAccountUpdateSerializer,
    SellerSyncLogSerializer,
    TriggerSyncSerializer,
)


class SellerAccountListCreateView(generics.ListCreateAPIView):
    """
    List all seller accounts or create a new one.
    
    GET: List user's seller accounts
    POST: Add new seller account
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return only current user's seller accounts."""
        return SellerAccount.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return SellerAccountCreateSerializer
        return SellerAccountSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        seller = serializer.save()
        
        return Response({
            'success': True,
            'message': 'Satıcı hesabı başarıyla eklendi.',
            'data': SellerAccountSerializer(seller).data
        }, status=status.HTTP_201_CREATED)


class SellerAccountDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a seller account.
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return SellerAccount.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return SellerAccountUpdateSerializer
        return SellerAccountSerializer
    
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response({
            'success': True,
            'message': 'Satıcı hesabı güncellendi.',
            'data': response.data
        })
    
    def destroy(self, request, *args, **kwargs):
        seller = self.get_object()
        shop_name = seller.shop_name
        seller.delete()
        
        return Response({
            'success': True,
            'message': f'{shop_name} satıcı hesabı silindi.'
        }, status=status.HTTP_200_OK)


class TriggerSyncView(APIView):
    """
    Trigger manual sync for a seller account.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        try:
            seller = SellerAccount.objects.get(pk=pk, user=request.user)
        except SellerAccount.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Satıcı hesabı bulunamadı.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if not seller.is_active:
            return Response({
                'success': False,
                'message': 'Bu satıcı hesabı aktif değil.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if seller.sync_status == 'syncing':
            return Response({
                'success': False,
                'message': 'Senkronizasyon zaten devam ediyor.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = TriggerSyncSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Update status
        seller.mark_sync_started()
        
        # Import settings to check DEBUG mode
        from django.conf import settings
        
        sync_type = serializer.validated_data.get('sync_type', 'incremental')
        start_date = serializer.validated_data.get('start_date')
        end_date = serializer.validated_data.get('end_date')
        
        if settings.DEBUG:
            # Run synchronously in development (no Celery/Redis needed)
            try:
                from apps.integrations.trendyol.sync_service import OrderSyncService, ProductSyncService
                
                # 1. Sync Products (Full details: images, brand, category, etc.)
                # This might fail if API key doesn't have product permissions
                products_result = {'products_synced': 0}
                product_sync_error = None
                
                try:
                    product_service = ProductSyncService(seller)
                    products_result = product_service.sync_products()
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Product sync failed: {str(e)}")
                    product_sync_error = str(e)
                
                # 2. Sync Orders
                order_service = OrderSyncService(seller)
                orders_fetched, orders_created, orders_updated = order_service.sync_orders(
                    sync_type=sync_type,
                    start_date=start_date,
                    end_date=end_date
                )
                
                msg = f'Senkronizasyon tamamlandı. {orders_fetched} sipariş çekildi.'
                if products_result['products_synced'] > 0:
                    msg += f' {products_result["products_synced"]} ürün detayları güncellendi.'
                elif product_sync_error:
                    msg += f' (Ürün senkronizasyonu uyarısı: {product_sync_error})'
                
                # 3. Enrich Products from Web (Fallback)
                try:
                    # Provide robustness: try to enrich missing details (images/brands)
                    # even if API failed or returned partial data
                    enrich_service = ProductSyncService(seller)
                    enriched_count = enrich_service.enrich_products_from_web()
                    if enriched_count > 0:
                        msg += f' {enriched_count} eksik ürün için bilgiler web\'den tamamlandı.'
                except Exception as e:
                    logger.warning(f"Enrichment failed: {e}")
                
                return Response({
                    'success': True,
                    'message': msg,
                    'data': {
                        'seller_id': seller.id,
                        'sync_status': seller.sync_status,
                        'products_synced': products_result.get('products_synced', 0),
                        'orders_fetched': orders_fetched,
                        'orders_created': orders_created,
                        'orders_updated': orders_updated,
                        'product_sync_error': product_sync_error
                    }
                })
            except Exception as e:
                import traceback
                error_detail = traceback.format_exc()
                logger_msg = f'Sync error: {str(e)}\n{error_detail}'
                seller.mark_sync_failed(str(e))
                return Response({
                    'success': False,
                    'message': f'Senkronizasyon hatası: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            # Queue the sync task in production
            from apps.integrations.tasks import sync_seller_orders
            sync_seller_orders.delay(
                seller_id=seller.id,
                sync_type=sync_type,
                start_date=start_date,
                end_date=end_date,
            )
            
            return Response({
                'success': True,
                'message': 'Senkronizasyon başlatıldı.',
                'data': {
                    'seller_id': seller.id,
                    'sync_status': seller.sync_status,
                }
            })


class SellerSyncStatusView(APIView):
    """
    Get sync status for a seller account.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        try:
            seller = SellerAccount.objects.get(pk=pk, user=request.user)
        except SellerAccount.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Satıcı hesabı bulunamadı.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'success': True,
            'data': {
                'seller_id': seller.id,
                'shop_name': seller.shop_name,
                'sync_status': seller.sync_status,
                'last_sync_at': seller.last_sync_at,
                'last_sync_error': seller.last_sync_error,
                'total_orders_synced': seller.total_orders_synced,
            }
        })


class SellerSyncLogsView(generics.ListAPIView):
    """
    List sync logs for a seller account.
    """
    serializer_class = SellerSyncLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        seller_id = self.kwargs.get('pk')
        return SellerSyncLog.objects.filter(
            seller_account__user=self.request.user,
            seller_account_id=seller_id
        ).order_by('-started_at')[:50]


class TestCredentialsView(APIView):
    """
    Test Trendyol API credentials for a seller account.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        try:
            seller = SellerAccount.objects.get(pk=pk, user=request.user)
        except SellerAccount.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Satıcı hesabı bulunamadı.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Test credentials by making a simple API call
        from apps.integrations.trendyol.client import TrendyolClient
        
        try:
            client = TrendyolClient(
                seller_id=seller.seller_id,
                api_key=seller.get_decrypted_api_key(),
                api_secret=seller.get_decrypted_api_secret()
            )
            # Try to fetch a small amount of data to verify credentials
            result = client.test_connection()
            
            return Response({
                'success': True,
                'message': 'API kimlik bilgileri doğrulandı.',
                'data': result
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'API bağlantısı başarısız: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
