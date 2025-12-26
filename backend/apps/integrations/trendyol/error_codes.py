"""
Trendyol API Error Codes and Turkish Messages
"""

TRENDYOL_ERROR_MESSAGES = {
    400: 'Geçersiz istek. Parametreleri kontrol edin.',
    401: 'Trendyol API kimlik doğrulaması başarısız. API anahtarlarınızı kontrol edin.',
    403: 'Bu işlem için yetkiniz yok. Satıcı hesabınızın durumunu kontrol edin.',
    404: 'İstenen kaynak bulunamadı.',
    429: 'Çok fazla istek gönderildi. Lütfen bir süre bekleyin.',
    500: 'Trendyol sunucusunda bir hata oluştu. Daha sonra tekrar deneyin.',
    502: 'Trendyol sunucusu yanıt vermiyor.',
    503: 'Trendyol servisi şu anda kullanılamıyor. Daha sonra tekrar deneyin.',
    504: 'Trendyol sunucusu zaman aşımına uğradı.',
}


# Order status mappings
ORDER_STATUS_MAP = {
    'Created': 'Oluşturuldu',
    'Picking': 'Hazırlanıyor',
    'Invoiced': 'Faturalandı',
    'Shipped': 'Kargoya Verildi',
    'Delivered': 'Teslim Edildi',
    'Cancelled': 'İptal',
    'Returned': 'İade',
    'UnDelivered': 'Teslim Edilemedi',
    'UnDeliveredAndReturned': 'Teslim Edilemedi ve İade',
}


# Return reason mappings
RETURN_REASON_MAP = {
    'customer_request': 'Müşteri isteği',
    'damaged': 'Hasarlı ürün',
    'wrong_product': 'Yanlış ürün',
    'defective': 'Kusurlu ürün',
    'size_exchange': 'Beden değişikliği',
    'not_as_described': 'Ürün açıklamaya uygun değil',
    'other': 'Diğer',
}
