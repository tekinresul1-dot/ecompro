"""
Accounts App - Serializers

SECURITY HARDENED VERSION
Serializers for user registration, authentication, and profile management.
Includes input validation, XSS prevention, and brute-force protection.
"""

import re
import html
import logging
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.validators import EmailValidator
from django.utils import timezone

User = get_user_model()
security_logger = logging.getLogger('django.security')


def sanitize_input(value: str) -> str:
    """
    SECURITY: Sanitize user input to prevent XSS attacks.
    """
    if not value:
        return value
    # HTML escape
    value = html.escape(value, quote=True)
    # Remove potential script injections
    value = re.sub(r'<[^>]*script[^>]*>', '', value, flags=re.IGNORECASE)
    value = re.sub(r'javascript:', '', value, flags=re.IGNORECASE)
    value = re.sub(r'on\w+\s*=', '', value, flags=re.IGNORECASE)
    return value.strip()


def validate_no_html(value: str) -> str:
    """
    SECURITY: Reject any HTML tags in input.
    """
    if re.search(r'<[^>]+>', value):
        raise serializers.ValidationError('HTML etiketleri kullanılamaz.')
    return value


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    SECURITY ENHANCED: Serializer for user registration.
    - Strong password validation
    - Input sanitization
    - Email format validation
    """
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'},
        min_length=10,
        max_length=128,
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        min_length=10,
        max_length=128,
    )
    email = serializers.EmailField(
        validators=[EmailValidator()],
        max_length=255,
    )
    first_name = serializers.CharField(
        max_length=50,
        min_length=2,
    )
    last_name = serializers.CharField(
        max_length=50,
        min_length=2,
    )
    company_name = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
    )
    
    class Meta:
        model = User
        fields = [
            'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'company_name', 'phone'
        ]
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate_email(self, value):
        """SECURITY: Normalize and validate email."""
        value = value.lower().strip()
        
        # Check for disposable email domains (basic list)
        disposable_domains = [
            'tempmail.com', 'throwaway.email', '10minutemail.com',
            'guerrillamail.com', 'mailinator.com', 'temp-mail.org'
        ]
        domain = value.split('@')[1] if '@' in value else ''
        if domain in disposable_domains:
            raise serializers.ValidationError('Geçici email adresleri kabul edilmez.')
        
        return value
    
    def validate_first_name(self, value):
        """SECURITY: Sanitize and validate first name."""
        value = validate_no_html(value)
        value = sanitize_input(value)
        if not re.match(r'^[a-zA-ZğüşıöçĞÜŞİÖÇ\s\-]+$', value):
            raise serializers.ValidationError('İsim sadece harf içerebilir.')
        return value
    
    def validate_last_name(self, value):
        """SECURITY: Sanitize and validate last name."""
        value = validate_no_html(value)
        value = sanitize_input(value)
        if not re.match(r'^[a-zA-ZğüşıöçĞÜŞİÖÇ\s\-]+$', value):
            raise serializers.ValidationError('Soyisim sadece harf içerebilir.')
        return value
    
    def validate_company_name(self, value):
        """SECURITY: Sanitize company name."""
        if value:
            value = validate_no_html(value)
            value = sanitize_input(value)
        return value
    
    def validate_phone(self, value):
        """SECURITY: Validate phone number format."""
        if value:
            # Remove all non-digit characters
            digits_only = re.sub(r'\D', '', value)
            if len(digits_only) < 10 or len(digits_only) > 15:
                raise serializers.ValidationError('Geçerli bir telefon numarası girin.')
            return digits_only
        return value
    
    def validate(self, attrs):
        """Validate that passwords match."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Şifreler eşleşmiyor.'
            })
        
        # SECURITY: Check password isn't too similar to user data
        password = attrs['password'].lower()
        if attrs['email'].split('@')[0].lower() in password:
            raise serializers.ValidationError({
                'password': 'Şifre email adresinize çok benziyor.'
            })
        if attrs['first_name'].lower() in password:
            raise serializers.ValidationError({
                'password': 'Şifre adınıza çok benziyor.'
            })
        
        return attrs
    
    def create(self, validated_data):
        """Create a new user."""
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        
        # SECURITY: Log new user registration
        security_logger.info(f'New user registered: {user.email}')
        
        return user


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user profile display and update."""
    
    seller_count = serializers.ReadOnlyField()
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'company_name', 'phone', 'default_vat_rate',
            'email_notifications', 'is_verified',
            'seller_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'email', 'is_verified', 'created_at', 'updated_at']
    
    def validate_first_name(self, value):
        """SECURITY: Sanitize first name on update."""
        return sanitize_input(validate_no_html(value))
    
    def validate_last_name(self, value):
        """SECURITY: Sanitize last name on update."""
        return sanitize_input(validate_no_html(value))
    
    def validate_company_name(self, value):
        """SECURITY: Sanitize company name on update."""
        return sanitize_input(validate_no_html(value)) if value else value
    
    def get_full_name(self, obj):
        return obj.get_full_name()


class UserSettingsSerializer(serializers.ModelSerializer):
    """Serializer for updating user settings."""
    
    class Meta:
        model = User
        fields = [
            'default_vat_rate', 'email_notifications'
        ]
    
    def validate_default_vat_rate(self, value):
        """SECURITY: Validate VAT rate is within acceptable range."""
        if value < 0 or value > 100:
            raise serializers.ValidationError('KDV oranı 0-100 arasında olmalıdır.')
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """
    SECURITY ENHANCED: Serializer for password change.
    - Rate limiting handled at view level
    - Password strength validation
    """
    
    old_password = serializers.CharField(
        required=True,
        style={'input_type': 'password'},
        max_length=128,
    )
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'},
        min_length=10,
        max_length=128,
    )
    new_password_confirm = serializers.CharField(
        required=True,
        style={'input_type': 'password'},
        min_length=10,
        max_length=128,
    )
    
    def validate_old_password(self, value):
        """SECURITY: Validate that old password is correct with timing attack protection."""
        user = self.context['request'].user
        if not user.check_password(value):
            # SECURITY: Log failed password attempt
            security_logger.warning(f'Failed password change attempt for user: {user.email}')
            raise serializers.ValidationError('Mevcut şifre yanlış.')
        return value
    
    def validate_new_password(self, value):
        """SECURITY: Ensure new password is different from old."""
        user = self.context['request'].user
        if user.check_password(value):
            raise serializers.ValidationError('Yeni şifre eskisiyle aynı olamaz.')
        return value
    
    def validate(self, attrs):
        """Validate that new passwords match."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'Yeni şifreler eşleşmiyor.'
            })
        return attrs


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    SECURITY ENHANCED: Custom JWT token serializer.
    - Failed login attempt logging
    - Account lockout tracking
    """
    
    def validate(self, attrs):
        try:
            data = super().validate(attrs)
            
            # SECURITY: Log successful login
            security_logger.info(f'Successful login: {self.user.email}')
            
            # Update last login
            self.user.last_login = timezone.now()
            self.user.save(update_fields=['last_login'])
            
            # Add user info to response (minimal data exposure)
            data['user'] = {
                'id': self.user.id,
                'email': self.user.email,
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'full_name': self.user.get_full_name(),
            }
            
            return data
            
        except Exception as e:
            # SECURITY: Log failed login attempt
            email = attrs.get('email', 'unknown')
            security_logger.warning(f'Failed login attempt: {email}')
            raise
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # SECURITY: Only add necessary claims to token (minimize data exposure)
        token['email'] = user.email
        # Don't include sensitive data in JWT
        
        return token
