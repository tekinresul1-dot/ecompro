"""
Validators for Trendyol Profitability SaaS

Custom validation functions for data integrity.
"""

import re
from decimal import Decimal, InvalidOperation
from django.core.exceptions import ValidationError


def validate_barcode(value: str) -> None:
    """
    Validate product barcode format.
    Accepts EAN-13, EAN-8, UPC-A, and custom alphanumeric codes.
    """
    if not value:
        raise ValidationError('Barkod boş olamaz.')
    
    # Allow alphanumeric with some special chars
    if not re.match(r'^[A-Za-z0-9\-_]{3,50}$', value):
        raise ValidationError(
            'Barkod 3-50 karakter uzunluğunda olmalı ve sadece '
            'harf, rakam, tire ve alt çizgi içermelidir.'
        )


def validate_positive_decimal(value: Decimal) -> None:
    """Validate that a decimal value is positive."""
    if value is not None and value < 0:
        raise ValidationError('Değer sıfır veya pozitif olmalıdır.')


def validate_percentage(value: Decimal) -> None:
    """Validate that a value is a valid percentage (0-100)."""
    if value is not None:
        if value < 0 or value > 100:
            raise ValidationError('Yüzde değeri 0-100 arasında olmalıdır.')


def validate_vat_rate(value: Decimal) -> None:
    """
    Validate VAT rate.
    Turkish VAT rates: 1%, 10%, 20%
    """
    valid_rates = [Decimal('0'), Decimal('1'), Decimal('10'), Decimal('20')]
    if value not in valid_rates:
        raise ValidationError(
            f'Geçersiz KDV oranı. Geçerli değerler: {", ".join(map(str, valid_rates))}'
        )


def validate_trendyol_seller_id(value: str) -> None:
    """Validate Trendyol seller ID format."""
    if not value:
        raise ValidationError('Satıcı ID boş olamaz.')
    
    # Trendyol seller IDs are typically numeric
    if not re.match(r'^\d{4,20}$', value):
        raise ValidationError(
            'Geçersiz Trendyol satıcı ID formatı. '
            '4-20 haneli sayısal değer olmalıdır.'
        )


def validate_api_key(value: str) -> None:
    """Basic validation for API key format."""
    if not value or len(value) < 10:
        raise ValidationError('API anahtarı en az 10 karakter olmalıdır.')


def validate_currency_amount(value: Decimal) -> None:
    """Validate currency amount has reasonable precision."""
    if value is None:
        return
    
    try:
        # Check decimal places
        if abs(value.as_tuple().exponent) > 4:
            raise ValidationError(
                'Para birimi değeri en fazla 4 ondalık basamak içerebilir.'
            )
        
        # Check reasonable range (max 1 billion TRY)
        if abs(value) > Decimal('1000000000'):
            raise ValidationError('Değer çok büyük.')
            
    except InvalidOperation:
        raise ValidationError('Geçersiz sayısal değer.')


def validate_phone_number(value: str) -> None:
    """Validate Turkish phone number format."""
    if not value:
        return
    
    # Remove common formatting characters
    cleaned = re.sub(r'[\s\-\(\)]', '', value)
    
    # Turkish mobile: 05XX XXX XX XX or +90 5XX XXX XX XX
    pattern = r'^(\+90|0)?5\d{9}$'
    if not re.match(pattern, cleaned):
        raise ValidationError(
            'Geçersiz telefon numarası formatı. '
            'Örnek: 05XX XXX XX XX veya +90 5XX XXX XX XX'
        )
