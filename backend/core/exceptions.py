"""
Core Exceptions for Trendyol Profitability SaaS

Custom exception classes and DRF exception handler.
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


class TrendyolAPIError(Exception):
    """Base exception for Trendyol API errors."""
    
    def __init__(self, message, status_code=None, error_code=None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)


class TrendyolAuthenticationError(TrendyolAPIError):
    """Trendyol API authentication failed."""
    pass


class TrendyolRateLimitError(TrendyolAPIError):
    """Trendyol API rate limit exceeded."""
    pass


class CalculationError(Exception):
    """Error during profit calculation."""
    
    def __init__(self, message, field=None, order_item_id=None):
        self.message = message
        self.field = field
        self.order_item_id = order_item_id
        super().__init__(self.message)


class EncryptionError(Exception):
    """Error during encryption/decryption of sensitive data."""
    pass


class SyncError(Exception):
    """Error during data synchronization."""
    
    def __init__(self, message, seller_account_id=None, recoverable=True):
        self.message = message
        self.seller_account_id = seller_account_id
        self.recoverable = recoverable
        super().__init__(self.message)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides Turkish error messages
    and consistent error response format.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Customize the response data
        custom_response_data = {
            'success': False,
            'error': {
                'code': response.status_code,
                'message': get_turkish_error_message(response.status_code),
                'details': response.data,
            }
        }
        response.data = custom_response_data
        return response
    
    # Handle custom exceptions
    if isinstance(exc, TrendyolAPIError):
        return Response({
            'success': False,
            'error': {
                'code': exc.status_code or 502,
                'message': exc.message,
                'type': 'trendyol_api_error',
            }
        }, status=status.HTTP_502_BAD_GATEWAY)
    
    if isinstance(exc, CalculationError):
        return Response({
            'success': False,
            'error': {
                'code': 422,
                'message': exc.message,
                'field': exc.field,
                'type': 'calculation_error',
            }
        }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    
    if isinstance(exc, EncryptionError):
        return Response({
            'success': False,
            'error': {
                'code': 500,
                'message': 'Güvenlik hatası oluştu. Lütfen yöneticiyle iletişime geçin.',
                'type': 'encryption_error',
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Unhandled exception - return generic error
    return Response({
        'success': False,
        'error': {
            'code': 500,
            'message': 'Beklenmeyen bir hata oluştu.',
            'type': 'internal_error',
        }
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def get_turkish_error_message(status_code: int) -> str:
    """Return Turkish error message for HTTP status codes."""
    messages = {
        400: 'Geçersiz istek. Lütfen gönderilen verileri kontrol edin.',
        401: 'Kimlik doğrulaması gerekli. Lütfen giriş yapın.',
        403: 'Bu işlem için yetkiniz yok.',
        404: 'İstenen kaynak bulunamadı.',
        405: 'Bu HTTP metodu desteklenmiyor.',
        409: 'Çakışma hatası. Kaynak zaten mevcut.',
        422: 'İşlenemeyen veri. Lütfen girdileri kontrol edin.',
        429: 'Çok fazla istek. Lütfen bir süre bekleyin.',
        500: 'Sunucu hatası oluştu.',
        502: 'Harici servis hatası.',
        503: 'Servis şu anda kullanılamıyor.',
    }
    return messages.get(status_code, 'Bir hata oluştu.')
