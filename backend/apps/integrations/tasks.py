"""
Integration Celery Tasks

Background tasks for order synchronization and calculations.
"""

import logging
from datetime import datetime, timedelta
from celery import shared_task

from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def sync_seller_orders(
    self,
    seller_id: int,
    sync_type: str = 'incremental',
    start_date: datetime = None,
    end_date: datetime = None
):
    """
    Sync orders for a specific seller account.
    
    Args:
        seller_id: SellerAccount ID
        sync_type: 'full' or 'incremental'
        start_date: Optional start date for full sync
        end_date: Optional end date
    """
    from apps.sellers.models import SellerAccount
    from apps.integrations.trendyol import OrderSyncService
    
    try:
        seller = SellerAccount.objects.get(pk=seller_id)
    except SellerAccount.DoesNotExist:
        logger.error(f'Seller account {seller_id} not found')
        return
    
    try:
        service = OrderSyncService(seller)
        fetched, created, updated = service.sync_orders(
            start_date=start_date,
            end_date=end_date,
            sync_type=sync_type
        )
        
        logger.info(
            f'Sync completed for seller {seller_id}: '
            f'{fetched} fetched, {created} created, {updated} updated'
        )
        
        # Trigger calculations for new orders
        calculate_uncalculated_items.delay(seller_id)
        
        return {
            'success': True,
            'fetched': fetched,
            'created': created,
            'updated': updated
        }
        
    except Exception as e:
        logger.exception(f'Sync failed for seller {seller_id}: {e}')
        raise self.retry(exc=e)


@shared_task
def sync_all_seller_orders():
    """
    Sync orders for all active seller accounts.
    Called periodically by Celery Beat.
    """
    from apps.sellers.models import SellerAccount
    
    active_sellers = SellerAccount.objects.filter(
        is_active=True
    ).values_list('id', flat=True)
    
    for seller_id in active_sellers:
        sync_seller_orders.delay(seller_id, sync_type='incremental')
    
    logger.info(f'Queued sync for {len(active_sellers)} sellers')


@shared_task(bind=True, max_retries=2)
def calculate_uncalculated_items(self, seller_id: int, limit: int = 1000):
    """
    Calculate profits for uncalculated order items.
    """
    from apps.calculations.services import get_calculation_service
    
    try:
        service = get_calculation_service()
        processed, errors = service.calculate_uncalculated_items(
            seller_account_id=seller_id,
            limit=limit
        )
        
        logger.info(
            f'Calculated {processed} items for seller {seller_id}, {errors} errors'
        )
        
        # Update daily summaries
        update_daily_summaries.delay(seller_id)
        
        return {'processed': processed, 'errors': errors}
        
    except Exception as e:
        logger.exception(f'Calculation failed for seller {seller_id}: {e}')
        raise self.retry(exc=e)


@shared_task
def update_daily_summaries(seller_id: int, days: int = 7):
    """
    Update daily profit summaries for recent days.
    """
    from apps.calculations.services import get_calculation_service
    
    service = get_calculation_service()
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    count = service.update_daily_summaries_range(
        seller_account_id=seller_id,
        start_date=start_date,
        end_date=end_date
    )
    
    logger.info(f'Updated {count} daily summaries for seller {seller_id}')


@shared_task
def recalculate_daily_summaries():
    """
    Recalculate all daily summaries.
    Called daily by Celery Beat.
    """
    from apps.sellers.models import SellerAccount
    
    for seller_id in SellerAccount.objects.filter(is_active=True).values_list('id', flat=True):
        update_daily_summaries.delay(seller_id, days=7)


@shared_task
def update_product_summaries(seller_id: int):
    """
    Update profit summaries for all products of a seller.
    """
    from apps.products.models import Product
    from apps.calculations.services import get_calculation_service
    
    service = get_calculation_service()
    
    product_ids = Product.objects.filter(
        seller_account_id=seller_id,
        has_cost_data=True
    ).values_list('id', flat=True)
    
    for product_id in product_ids:
        service.update_product_summary(product_id)
    
    logger.info(f'Updated {len(product_ids)} product summaries for seller {seller_id}')
