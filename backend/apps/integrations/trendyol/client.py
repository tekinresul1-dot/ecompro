"""
Trendyol API Client

Handles communication with Trendyol Merchant API.
Includes rate limiting, error handling, and automatic retries.
"""

import time
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
import requests
from requests.auth import HTTPBasicAuth

from django.conf import settings
from core.exceptions import (
    TrendyolAPIError,
    TrendyolAuthenticationError,
    TrendyolRateLimitError,
)
from .error_codes import TRENDYOL_ERROR_MESSAGES

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple rate limiter for API requests."""
    
    def __init__(self, max_requests: int = 5, period: float = 1.0):
        self.max_requests = max_requests
        self.period = period
        self.requests = []
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        now = time.time()
        # Remove old requests outside the window
        self.requests = [r for r in self.requests if now - r < self.period]
        
        if len(self.requests) >= self.max_requests:
            sleep_time = self.period - (now - self.requests[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        self.requests.append(time.time())


class TrendyolClient:
    """
    Trendyol Merchant API Client.
    
    Handles:
    - Authentication via API key/secret
    - Rate limiting
    - Error handling with Turkish messages
    - Pagination for order fetching
    """
    
    BASE_URL = "https://api.trendyol.com/sapigw"
    
    def __init__(
        self,
        seller_id: str,
        api_key: str,
        api_secret: str,
        rate_limit: int = 5
    ):
        self.seller_id = seller_id
        self.auth = HTTPBasicAuth(api_key, api_secret)
        self.rate_limiter = RateLimiter(max_requests=rate_limit)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': f'TrendyolProfitability-{seller_id}',
            'Content-Type': 'application/json',
        })
    
    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        retries: int = 3
    ) -> Dict:
        """Make an API request with rate limiting and error handling."""
        url = f"{self.BASE_URL}{endpoint}"
        
        for attempt in range(retries):
            try:
                self.rate_limiter.wait_if_needed()
                
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    auth=self.auth,
                    timeout=30
                )
                
                # Handle errors
                if response.status_code == 401:
                    raise TrendyolAuthenticationError(
                        TRENDYOL_ERROR_MESSAGES.get(401, 'Kimlik doğrulama hatası'),
                        status_code=401
                    )
                
                if response.status_code == 429:
                    if attempt < retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    raise TrendyolRateLimitError(
                        TRENDYOL_ERROR_MESSAGES.get(429, 'Rate limit aşıldı'),
                        status_code=429
                    )
                
                if response.status_code >= 400:
                    error_msg = TRENDYOL_ERROR_MESSAGES.get(
                        response.status_code,
                        f'API hatası: {response.status_code}'
                    )
                    raise TrendyolAPIError(
                        error_msg,
                        status_code=response.status_code
                    )
                
                return response.json()
                
            except requests.RequestException as e:
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise TrendyolAPIError(
                    f'Bağlantı hatası: {str(e)}',
                    status_code=503
                )
        
        raise TrendyolAPIError('Maksimum deneme sayısına ulaşıldı')
    
    def test_connection(self) -> Dict:
        """Test API connection with a simple request."""
        try:
            result = self.get_orders(
                start_date=datetime.now() - timedelta(days=1),
                end_date=datetime.now(),
                size=1
            )
            return {
                'success': True,
                'message': 'Bağlantı başarılı',
                'total_orders': result.get('totalElements', 0)
            }
        except Exception as e:
            raise TrendyolAPIError(f'Bağlantı testi başarısız: {str(e)}')
    
    def get_orders(
        self,
        start_date: datetime,
        end_date: datetime,
        page: int = 0,
        size: int = 200,
        status: Optional[str] = None,
        order_by_field: str = 'CreatedDate',
        order_by_direction: str = 'ASC'
    ) -> Dict:
        """
        Fetch orders for a date range.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            page: Page number (0-indexed)
            size: Page size (max 200)
            status: Filter by order status
            order_by_field: Field to sort by
            order_by_direction: ASC or DESC
            
        Returns:
            Dict with orders and pagination info
        """
        # Convert to milliseconds timestamp
        start_ts = int(start_date.timestamp() * 1000)
        end_ts = int(end_date.timestamp() * 1000)
        
        params = {
            'startDate': start_ts,
            'endDate': end_ts,
            'page': page,
            'size': min(size, 200),
            'orderByField': order_by_field,
            'orderByDirection': order_by_direction,
        }
        
        if status:
            params['status'] = status
        
        endpoint = f'/suppliers/{self.seller_id}/orders'
        return self._request('GET', endpoint, params=params)
    
    def get_all_orders(
        self,
        start_date: datetime,
        end_date: datetime,
        status: Optional[str] = None,
        callback=None
    ) -> List[Dict]:
        """
        Fetch all orders with automatic pagination.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            status: Filter by order status
            callback: Optional callback for progress updates
            
        Yields:
            Order dicts
        """
        page = 0
        total_fetched = 0
        
        while True:
            result = self.get_orders(
                start_date=start_date,
                end_date=end_date,
                page=page,
                status=status
            )
            
            orders = result.get('content', [])
            if not orders:
                break
            
            for order in orders:
                yield order
                total_fetched += 1
            
            if callback:
                callback(total_fetched, result.get('totalElements', 0))
            
            # Check if more pages
            total_pages = result.get('totalPages', 1)
            if page >= total_pages - 1:
                break
            
            page += 1
    
    def get_order_shipment_packages(self, shipment_package_id: str) -> Dict:
        """Get shipment package details."""
        endpoint = f'/suppliers/{self.seller_id}/orders/shipmentPackages/{shipment_package_id}'
        return self._request('GET', endpoint)
    
    def get_products(self, page: int = 0, size: int = 100) -> Dict:
        """Fetch products from Trendyol."""
        params = {
            'page': page,
            'size': min(size, 100),
        }
        endpoint = f'/suppliers/{self.seller_id}/products'
        return self._request('GET', endpoint, params=params)
