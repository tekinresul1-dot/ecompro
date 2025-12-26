"""
Sellers App - Serializers
"""

from rest_framework import serializers
from .models import SellerAccount, SellerSyncLog


class SellerAccountSerializer(serializers.ModelSerializer):
    """Serializer for seller account listing and detail."""
    
    # Mask credentials in responses
    api_key_masked = serializers.SerializerMethodField()
    api_secret_masked = serializers.SerializerMethodField()
    
    class Meta:
        model = SellerAccount
        fields = [
            'id', 'seller_id', 'shop_name', 'shop_url',
            'api_key_masked', 'api_secret_masked',
            'default_commission_rate', 'default_cargo_cost',
            'is_active', 'sync_status', 'last_sync_at',
            'last_sync_order_date', 'last_sync_error',
            'total_orders_synced', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'sync_status', 'last_sync_at', 'last_sync_order_date',
            'last_sync_error', 'total_orders_synced', 'created_at', 'updated_at'
        ]
    
    def get_api_key_masked(self, obj):
        """Return masked API key."""
        if obj.api_key:
            return '••••••••' + obj.api_key[-4:] if len(obj.api_key) > 4 else '••••••••'
        return None
    
    def get_api_secret_masked(self, obj):
        """Return masked API secret."""
        if obj.api_secret:
            return '••••••••' + obj.api_secret[-4:] if len(obj.api_secret) > 4 else '••••••••'
        return None


class SellerAccountCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new seller account."""
    
    class Meta:
        model = SellerAccount
        fields = [
            'seller_id', 'api_key', 'api_secret',
            'shop_name', 'shop_url',
            'default_commission_rate', 'default_cargo_cost'
        ]
    
    def validate_seller_id(self, value):
        """Check if seller already exists for this user."""
        user = self.context['request'].user
        if SellerAccount.objects.filter(user=user, seller_id=value).exists():
            raise serializers.ValidationError(
                'Bu satıcı hesabı zaten eklenmiş.'
            )
        return value
    
    def create(self, validated_data):
        """Create seller account with current user."""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class SellerAccountUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating seller account."""
    
    # Make credentials optional for update
    api_key = serializers.CharField(required=False, write_only=True)
    api_secret = serializers.CharField(required=False, write_only=True)
    
    class Meta:
        model = SellerAccount
        fields = [
            'shop_name', 'shop_url', 'api_key', 'api_secret',
            'default_commission_rate', 'default_cargo_cost',
            'is_active'
        ]
    
    def update(self, instance, validated_data):
        """Update seller account, only update credentials if provided."""
        # Only update credentials if new values are provided
        api_key = validated_data.pop('api_key', None)
        api_secret = validated_data.pop('api_secret', None)
        
        if api_key:
            instance.api_key = api_key
        if api_secret:
            instance.api_secret = api_secret
        
        return super().update(instance, validated_data)


class SellerSyncLogSerializer(serializers.ModelSerializer):
    """Serializer for sync log entries."""
    
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = SellerSyncLog
        fields = [
            'id', 'status', 'sync_type',
            'started_at', 'completed_at', 'duration',
            'date_range_start', 'date_range_end',
            'orders_fetched', 'orders_created', 'orders_updated',
            'items_processed', 'error_message'
        ]
    
    def get_duration(self, obj):
        """Return formatted duration."""
        seconds = obj.duration_seconds
        if seconds:
            return f'{seconds:.1f} saniye'
        return None


class TriggerSyncSerializer(serializers.Serializer):
    """Serializer for manual sync trigger."""
    
    sync_type = serializers.ChoiceField(
        choices=['full', 'incremental'],
        default='incremental'
    )
    start_date = serializers.DateTimeField(
        required=False,
        help_text='Tam senkronizasyon için başlangıç tarihi'
    )
    end_date = serializers.DateTimeField(
        required=False,
        help_text='Tam senkronizasyon için bitiş tarihi'
    )
