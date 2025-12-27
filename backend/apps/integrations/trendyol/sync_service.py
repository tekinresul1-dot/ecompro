"""
Trendyol Order Sync Service

Handles fetching orders from Trendyol and storing them in the database.
Supports both full and incremental synchronization.
"""

import logging
from datetime import datetime, timedelta, timezone as dt_timezone
from typing import Optional, Tuple
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.sellers.models import SellerAccount, SellerSyncLog
from apps.orders.models import Order, OrderItem
from apps.products.models import Product
from .client import TrendyolClient

logger = logging.getLogger(__name__)


logger = logging.getLogger(__name__)


class ProductSyncService:
    """
    Service for synchronizing products from Trendyol.
    """
    
    def __init__(self, seller_account: SellerAccount):
        self.seller_account = seller_account
        self.client = TrendyolClient(
            seller_id=seller_account.seller_id,
            api_key=seller_account.get_decrypted_api_key(),
            api_secret=seller_account.get_decrypted_api_secret()
        )
    
    def sync_products(self) -> dict:
        """
        Synchronize products from Trendyol.
        
        Returns:
            Dict with results
        """
        total_fetched = 0
        total_updated = 0
        total_created = 0
        
        try:
            # Fetch all products (pagination handled by client if implemented, else manual loop)
            # Since client.get_products handles simple get, we might need a loop here or use a get_all_products method
            # For now let's implement a simple loop similar to orders
            
            page = 0
            size = 100
            
            while True:
                response = self.client.get_products(page=page, size=size)
                products = response.get('content', [])
                
                if not products:
                    break
                
                for product_data in products:
                    total_fetched += 1
                    _, created = self._process_product(product_data)
                    
                    if created:
                        total_created += 1
                    else:
                        total_updated += 1
                
                # Check for next page
                total_pages = response.get('totalPages', 0)
                if page >= total_pages - 1:
                    break
                    
                page += 1
                
            logger.info(
                f'Product sync completed for {self.seller_account}: '
                f'{total_fetched} fetched, {total_created} created, {total_updated} updated'
            )
            
            return {
                'success': True,
                'products_synced': total_fetched,
                'products_created': total_created,
                'products_updated': total_updated
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.exception(f'Product sync failed for {self.seller_account}: {error_msg}')
            raise
    
    @transaction.atomic
    def _process_product(self, product_data: dict) -> Tuple[Product, bool]:
        """Process a single product from Trendyol API."""
        barcode = product_data.get('barcode', '')
        if not barcode:
            return None, False
            
        # Extract images
        images = product_data.get('images', [])
        image_url = images[0].get('url', '') if images else ''
        
        defaults = {
            'trendyol_product_id': str(product_data.get('id', '')),
            'title': product_data.get('title', ''),
            'brand': product_data.get('brand', {}).get('name', ''),
            'category': product_data.get('category', {}).get('name', ''),
            'category_id': str(product_data.get('category', {}).get('id', '')),
            'image_url': image_url,
            'color': product_data.get('attributes', {}).get('color', ''), # Often unstandardized
            'size': product_data.get('attributes', {}).get('size', ''),   # Often unstandardized
            # Try to populate fields if available in attributes list structure
            'stock': product_data.get('quantity', 0),
            'product_code': product_data.get('productCode', ''),
            'desi': Decimal(str(product_data.get('dimensionalWeight', 0))),
            'sale_price': Decimal(str(product_data.get('salePrice', 0))),
            'list_price': Decimal(str(product_data.get('listPrice', 0))),
            'vat_rate': Decimal(str(product_data.get('vatRate', 0))),
        }
        
        # Helper to find attribute value
        def get_attr_value(attrs, name):
            for attr in attrs:
                if attr.get('attributeName', '').lower() == name.lower():
                    return attr.get('attributeValue', '')
            return ''
            
        # Parse attributes list if 'attributes' is a list
        attributes = product_data.get('attributes', [])
        if isinstance(attributes, list):
            defaults['color'] = get_attr_value(attributes, 'Renk')
            defaults['size'] = get_attr_value(attributes, 'Beden')
        
        # Update or create
        product, created = Product.objects.update_or_create(
            seller_account=self.seller_account,
            barcode=barcode,
            defaults={
                'trendyol_product_id': defaults['trendyol_product_id'],
                'title': defaults['title'],
                'brand': defaults['brand'],
                'category': defaults['category'],
                'category_id': defaults['category_id'],
                'image_url': defaults['image_url'],
                'product_code': defaults['product_code'],
                'stock': defaults['stock'],
                'color': defaults['color'],
                'size': defaults['size'],
                'desi': defaults['desi'],
                'sales_vat_rate': defaults['vat_rate'] if defaults['vat_rate'] > 0 else 20.00,
            }
        )
        
        return product, created

    def enrich_products_from_web(self, limit=50):
        """
        Fallback method to enrich product details from public web.
        Used when API permissions are restricted.
        """
        import requests
        import re
        import os
        try:
            import cloudscraper
        except ImportError:
            cloudscraper = None
        
        # Debug logging
        def log_debug(msg):
            try:
                with open('debug_enrich.log', 'a') as f:
                    f.write(f"{datetime.now()}: {msg}\n")
            except:
                pass

        log_debug("Starting enrichment process with CloudScraper...")
        
        if not cloudscraper:
             logger.error("Cloudscraper module not found!")
             log_debug("Cloudscraper module not found!")
             return 0

        scraper = cloudscraper.create_scraper() 
        
        # 0. ID Recovery: Populate missing IDs from OrderItems if possible
        products_missing_id = Product.objects.filter(
             seller_account=self.seller_account,
             trendyol_product_id=''
        )
        count_recovered = 0
        for p in products_missing_id:
             item = p.order_items.first()
             if item and item.raw_data:
                  content_id = str(item.raw_data.get('contentId', '') or item.raw_data.get('productCode', ''))
                  if content_id:
                       p.trendyol_product_id = content_id
                       p.save(update_fields=['trendyol_product_id'])
                       count_recovered += 1
        
        log_debug(f"Recovered IDs for {count_recovered} products")

        products = Product.objects.filter(
            seller_account=self.seller_account
        ) 
        
        # Filter for products missing essential info
        target_products = []
        for p in products:
            if not p.image_url or not p.brand or p.brand == '---':
                target_products.append(p)
                
        if not target_products:
            log_debug("No target products found for enrichment.")
            return 0
            
        logger.info(f"Attempting to enrich {len(target_products)} products from public web using CloudScraper...")
        log_debug(f"Targeting {len(target_products)} products")
        
        count = 0
        
        for product in target_products[:limit]:
            try:
                response = None
                
                # Strategy 1: Direct ID URL
                if product.trendyol_product_id:
                    url = f"https://www.trendyol.com/p-{product.trendyol_product_id}"
                    try:
                        resp = scraper.get(url, timeout=10)
                        if resp.status_code == 200:
                            response = resp
                    except Exception as e:
                        log_debug(f"ID fetch failed for {product.barcode}: {e}")
                
                # Strategy 2: Barcode Search URL (Fallback)
                if not response:
                    url = f"https://www.trendyol.com/sr?q={product.barcode}"
                    try:
                        resp = scraper.get(url, timeout=10)
                        if resp.status_code == 200:
                            response = resp
                    except Exception as e:
                        log_debug(f"Barcode fetch failed for {product.barcode}: {e}")

                if response and response.status_code == 200:
                    html = response.text
                    updated = False
                    
                    # 1. Try OG:Image
                    if not product.image_url:
                        img_match = re.search(r'property="og:image"\s+content="([^"]+)"', html)
                        if img_match:
                            img_url = img_match.group(1)
                            if 'ty-passport' not in img_url:
                                product.image_url = img_url
                                updated = True
                            
                    # 2. Try Brand from JSON-LD or meta or Title
                    if not product.brand or product.brand == '---':
                         brand_match = re.search(r'"brand":{"@type":"Brand","name":"([^"]+)"', html)
                         if not brand_match:
                             brand_match = re.search(r'property="product:brand"\s+content="([^"]+)"', html)
                         
                         if brand_match:
                             product.brand = brand_match.group(1)
                             updated = True
                             
                    if updated:
                        product.save(update_fields=['image_url', 'brand'])
                        count += 1
                        log_debug(f"Enriched {product.barcode}")
                    else:
                        log_debug(f"No details found in HTML for {product.barcode}")
                else:
                    log_debug(f"Failed to get 200 OK for {product.barcode} (Status: {getattr(response, 'status_code', 'N/A')})")
                        
            except Exception as e:
                logger.warning(f"Failed to enrich product {product.barcode}: {e}")
                log_debug(f"Exception for {product.barcode}: {e}")
                continue
                
        log_debug(f"Finished enrichment. Total enriched: {count}")
        return count


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
        order_date = datetime.fromtimestamp(order_date_ms / 1000, tz=dt_timezone.utc)
        
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
                order_data['shipmentDate'] / 1000, tz=dt_timezone.utc
            )
        if order_data.get('deliveryDate'):
            order.delivered_at = datetime.fromtimestamp(
                order_data['deliveryDate'] / 1000, tz=dt_timezone.utc
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
        # DEBUG: Log raw data
        try:
            with open('debug_line_data.json', 'a') as f:
                import json
                f.write(json.dumps(line_data, default=str) + "\n---\n")
        except:
            pass

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
