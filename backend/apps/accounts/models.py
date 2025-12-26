"""
Accounts App - Models

Custom User model and authentication-related models.
"""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.mixins import TimestampMixin
from core.validators import validate_phone_number


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with the given email and password."""
        if not email:
            raise ValueError(_('Email adresi zorunludur.'))
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser is_staff=True olmalıdır.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser is_superuser=True olmalıdır.'))
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser, TimestampMixin):
    """
    Custom User model for Trendyol Profitability SaaS.
    
    Uses email as the primary identifier instead of username.
    Each user can have multiple Trendyol seller accounts.
    """
    
    # Remove username field, use email instead
    username = None
    email = models.EmailField(
        _('Email Adresi'),
        unique=True,
        error_messages={
            'unique': _('Bu email adresi zaten kayıtlı.'),
        }
    )
    
    # Profile fields
    first_name = models.CharField(_('Ad'), max_length=150)
    last_name = models.CharField(_('Soyad'), max_length=150)
    company_name = models.CharField(
        _('Şirket Adı'),
        max_length=255,
        blank=True
    )
    phone = models.CharField(
        _('Telefon'),
        max_length=20,
        blank=True,
        validators=[validate_phone_number]
    )
    
    # Default settings for calculations
    default_vat_rate = models.DecimalField(
        _('Varsayılan KDV Oranı'),
        max_digits=5,
        decimal_places=2,
        default=20.00,
        help_text=_('Yeni ürünler için varsayılan KDV oranı (%)')
    )
    
    # Preferences
    email_notifications = models.BooleanField(
        _('Email Bildirimleri'),
        default=True
    )
    
    # Status
    is_verified = models.BooleanField(
        _('Email Doğrulandı'),
        default=False
    )
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        db_table = 'users'
        verbose_name = _('Kullanıcı')
        verbose_name_plural = _('Kullanıcılar')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f'{self.first_name} {self.last_name}'.strip()
        return full_name or self.email
    
    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name or self.email.split('@')[0]
    
    @property
    def seller_count(self):
        """Return the number of connected seller accounts."""
        return self.seller_accounts.filter(is_active=True).count()


class UserActivity(models.Model):
    """
    Track user activities for audit and analytics.
    """
    
    ACTIVITY_TYPES = [
        ('login', 'Giriş'),
        ('logout', 'Çıkış'),
        ('seller_add', 'Satıcı Hesabı Ekleme'),
        ('seller_sync', 'Satıcı Senkronizasyonu'),
        ('cost_update', 'Maliyet Güncelleme'),
        ('export', 'Rapor İndirme'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    activity_type = models.CharField(
        _('Aktivite Tipi'),
        max_length=50,
        choices=ACTIVITY_TYPES
    )
    description = models.TextField(
        _('Açıklama'),
        blank=True
    )
    ip_address = models.GenericIPAddressField(
        _('IP Adresi'),
        null=True,
        blank=True
    )
    user_agent = models.TextField(
        _('User Agent'),
        blank=True
    )
    metadata = models.JSONField(
        _('Ek Bilgiler'),
        default=dict,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_activities'
        verbose_name = _('Kullanıcı Aktivitesi')
        verbose_name_plural = _('Kullanıcı Aktiviteleri')
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.user.email} - {self.activity_type}'
