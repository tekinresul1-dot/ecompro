"""
Trendyol Order Sync Service

Handles fetching orders from Trendyol and storing them in the database.
Supports both full and incremental synchronization.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.sellers.models import SellerAccount, SellerSyncLog
from apps.orders.models import Order, OrderItem
from apps.products.models import Product
from .client import TrendyolClient

logger = logging.getLogger(__name__)


class OrderSyncService:
    """
    Service for synchronizing orders from Trendyol.
    """
    
    def __init__(self, seller_account: SellerAccount):
        self.seller_account = seller_account
        self.client = TrendyolClient(
            seller_id=seller_account.seller_id,
            api_key=seller_account.get_decrypted_api_key(),
            api_secret=seller_account.get_decrypted_api_secret()
        )
    
    def sync_orders(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        sync_type: str = 'incremental'
    ) -> Tuple[int, int, int]:
        """
        Synchronize orders from Trendyol.
        
        Args:
            start_date: Start of date range (for full sync)
            end_date: End of date range
            sync_type: 'full' or 'incremental'
            
        Returns:
            Tuple of (fetched, created, updated)
        """
        # Determine date range
        if sync_type == 'incremental' and self.seller_account.last_sync_order_date:
            start_date = self.seller_account.last_sync_order_date - timedelta(hours=1)
        elif not start_date:
            start_date = timezone.now() - timedelta(days=30)
        
        if not end_date:
            end_date = timezone.now()
        
        # Create sync log
        sync_log = SellerSyncLog.objects.create(
            seller_account=self.seller_account,
            status='started',
            sync_type=sync_type,
            date_range_start=start_date,
            date_range_end=end_date
        )
        
        fetched = 0
        created = 0
        updated = 0
        items_processed = 0
        last_order_date = None
        
        try:
            for order_data in self.client.get_all_orders(start_date, end_date):
                fetched += 1
                
                order, was_created, item_count = self._process_order(order_data)
                
                if was_created:
                    created += 1
                else:
                    updated += 1
                
                items_processed += item_count
                
                if order.order_date:
                    if not last_order_date or order.order_date > last_order_date:
                        last_order_date = order.order_date
            
            # Update seller account
            self.seller_account.mark_sync_completed(
                order_count=created,
                last_order_date=last_order_date
            )
            
            # Update sync log
            sync_log.mark_completed(
                orders_fetched=fetched,
                orders_created=created,
                orders_updated=updated,
                items_processed=items_processed
            )
            
            logger.info(
                f'Sync completed for {self.seller_account}: '
                f'{fetched} fetched, {created} created, {updated} updated'
            )
            
        except Exception as e:
            error_msg = str(e)
            logger.exception(f'Sync failed for {self.seller_account}: {error_msg}')
            
            self.seller_account.mark_sync_failed(error_msg)
            sync_log.mark_failed(error_msg)
            
            raise
        
        return fetched, created, updated
    
    @transaction.atomic
    def _process_order(self, order_data: dict) -> Tuple[Order, bool, int]:
        """
        Process a single order from Trendyol API.
        
        Returns:
            Tuple of (Order, was_created, item_count)
        """
        order_number = str(order_data.get('orderNumber', ''))
        
        # Parse order date
        order_date_ms = order_data.get('orderDate', 0)
        order_date = datetime.fromtimestamp(order_date_ms / 1000, tz=timezone.utc)
        
        # Get or create order
        order, created = Order.objects.update_or_create(
            trendyol_order_number=order_number,
            defaults={
                'seller_account': self.seller_account,
                'trendyol_order_id': str(order_data.get('id', '')),
                'order_date': order_date,
                'status': order_data.get('status', 'Created'),
                'cargo_company': order_data.get('cargoProviderName', ''),
                'cargo_tracking_number': order_data.get('cargoTrackingNumber', ''),
                'cargo_provider_name': order_data.get('cargoProviderName', ''),
                'shipment_package_id': str(order_data.get('shipmentPackageId', '')),
                'invoice_number': order_data.get('invoiceNumber', ''),
                'total_price': Decimal(str(order_data.get('totalPrice', 0))),
                'total_discount': Decimal(str(order_data.get('totalDiscount', 0))),
                'raw_data': order_data,
            }
        )
        
        # Process shipment dates
        if order_data.get('shipmentDate'):
            order.shipped_at = datetime.fromtimestamp(
                order_data['shipmentDate'] / 1000, tz=timezone.utc
            )
        if order_data.get('deliveryDate'):
            order.delivered_at = datetime.fromtimestamp(
                order_data['deliveryDate'] / 1000, tz=timezone.utc
            )
        order.save()
        
        # Process order items
        item_count = 0
        lines = order_data.get('lines', [])
        
        for line_data in lines:
            self._process_order_item(order, line_data)
            item_count += 1
        
        return order, created, item_count
    
    def _process_order_item(self, order: Order, line_data: dict) -> OrderItem:
        """Process a single order item."""
        line_id = str(line_data.get('id', ''))
        barcode = str(line_data.get('barcode', ''))
        
        # Calculate discount
        original_price = Decimal(str(line_data.get('price', 0)))
        sale_price = Decimal(str(line_data.get('salePrice', 0) or line_data.get('price', 0)))
        discount = original_price - sale_price
        
        # Get commission info
        commission_rate = Decimal('0')
        commission_amount = Decimal('0')
        cargo_cost = Decimal('0')
        platform_fee = Decimal('0')
        
        # Trendyol may return these in different fields
        if 'commissionRate' in line_data:
            commission_rate = Decimal(str(line_data['commissionRate']))
        if 'tyCommission' in line_data:
            commission_amount = Decimal(str(line_data['tyCommission']))
        if 'tyShipmentCost' in line_data:
            cargo_cost = Decimal(str(line_data['tyShipmentCost']))
        if 'tyServiceFee' in line_data:
            platform_fee = Decimal(str(line_data['tyServiceFee']))
        
        item, _ = OrderItem.objects.update_or_create(
            order=order,
            trendyol_line_id=line_id,
            defaults={
                'barcode': barcode,
                'product_code': line_data.get('merchantSku', ''),
                'product_name': line_data.get('productName', ''),
                'product_size': line_data.get('productSize', ''),
                'product_color': line_data.get('productColor', ''),
                'quantity': int(line_data.get('quantity', 1)),
                'unit_price': sale_price,
                'original_price': original_price,
                'discount_amount': discount,
                'commission_rate': commission_rate,
                'commission_amount': commission_amount,
                'cargo_cost': cargo_cost,
                'platform_service_fee': platform_fee,
                'merchant_sku': line_data.get('merchantSku', ''),
                'raw_data': line_data,
            }
        )
        
        # Link to product
        item.link_product()
        
        return item
