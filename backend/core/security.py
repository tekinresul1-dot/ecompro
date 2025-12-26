"""
Core Security Middleware and Utilities

Provides additional security layers for the application.
"""

import logging
import re
from django.http import JsonResponse
from django.core.cache import cache
from django.utils import timezone

security_logger = logging.getLogger('django.security')


class SecurityMiddleware:
    """
    SECURITY: Additional security middleware for request validation.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Suspicious patterns that might indicate attacks
        self.suspicious_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'on\w+\s*=',
            r'union\s+select',
            r'--\s*$',
            r'/etc/passwd',
            r'\.\./',
            r'\x00',
        ]
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.suspicious_patterns]
    
    def __call__(self, request):
        # Check for suspicious request content
        if self._is_suspicious_request(request):
            security_logger.warning(
                f"Suspicious request blocked from IP: {self._get_client_ip(request)}"
            )
            return JsonResponse({
                'success': False,
                'message': 'Geçersiz istek.'
            }, status=400)
        
        response = self.get_response(request)
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response
    
    def _is_suspicious_request(self, request):
        """Check if request contains suspicious patterns."""
        # Check query string
        query_string = request.META.get('QUERY_STRING', '')
        if self._contains_suspicious_pattern(query_string):
            return True
        
        # Check path
        if self._contains_suspicious_pattern(request.path):
            return True
        
        return False
    
    def _contains_suspicious_pattern(self, text: str) -> bool:
        """Check if text contains any suspicious patterns."""
        for pattern in self.compiled_patterns:
            if pattern.search(text):
                return True
        return False
    
    def _get_client_ip(self, request):
        """Get client IP from request, handling proxies."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip


class LoginRateLimitMiddleware:
    """
    SECURITY: Rate limiting specifically for login attempts.
    Prevents brute-force attacks on authentication.
    """
    
    MAX_ATTEMPTS = 5  # Maximum login attempts
    LOCKOUT_TIME = 900  # 15 minutes lockout
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Only check login endpoint
        if request.path == '/api/v1/auth/login/' and request.method == 'POST':
            ip = self._get_client_ip(request)
            cache_key = f'login_attempts_{ip}'
            
            # Check if IP is locked out
            attempts = cache.get(cache_key, 0)
            if attempts >= self.MAX_ATTEMPTS:
                security_logger.warning(f"Login locked out for IP: {ip}")
                return JsonResponse({
                    'success': False,
                    'message': 'Çok fazla başarısız deneme. 15 dakika sonra tekrar deneyin.'
                }, status=429)
        
        response = self.get_response(request)
        
        # Track failed login attempts
        if request.path == '/api/v1/auth/login/' and request.method == 'POST':
            if response.status_code == 401:
                ip = self._get_client_ip(request)
                cache_key = f'login_attempts_{ip}'
                attempts = cache.get(cache_key, 0)
                cache.set(cache_key, attempts + 1, self.LOCKOUT_TIME)
                security_logger.info(f"Failed login attempt #{attempts + 1} from IP: {ip}")
            elif response.status_code == 200:
                # Successful login - clear attempts
                ip = self._get_client_ip(request)
                cache_key = f'login_attempts_{ip}'
                cache.delete(cache_key)
        
        return response
    
    def _get_client_ip(self, request):
        """Get client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')


class AuditLogMiddleware:
    """
    SECURITY: Audit logging for sensitive operations.
    """
    
    SENSITIVE_ENDPOINTS = [
        '/api/v1/auth/register/',
        '/api/v1/auth/change-password/',
        '/api/v1/sellers/',
        '/api/v1/products/bulk-upload/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if this is a sensitive endpoint
        is_sensitive = any(
            request.path.startswith(endpoint) 
            for endpoint in self.SENSITIVE_ENDPOINTS
        )
        
        response = self.get_response(request)
        
        # Log sensitive operations
        if is_sensitive and request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            user_email = 'anonymous'
            if hasattr(request, 'user') and request.user.is_authenticated:
                user_email = request.user.email
            
            security_logger.info(
                f"Sensitive operation: {request.method} {request.path} "
                f"by {user_email} from {self._get_client_ip(request)} "
                f"- Status: {response.status_code}"
            )
        
        return response
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')
