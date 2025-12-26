"""
Products App - Serializers
"""

from rest_framework import serializers
from .models import Product, ProductCostHistory, BulkCostUpload


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for product listing and detail."""
    
    effective_commission_rate = serializers.SerializerMethodField()
    product_cost_incl_vat = serializers.ReadOnlyField()
    seller_name = serializers.CharField(source='seller_account.shop_name', read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'barcode', 'product_code', 'trendyol_product_id',
            'title', 'brand', 'category', 'category_id',
            'product_cost_excl_vat', 'product_cost_incl_vat',
            'purchase_vat_rate', 'sales_vat_rate',
            'commission_rate', 'effective_commission_rate',
            'is_active', 'has_cost_data',
            'cost_updated_at', 'last_order_date', 'total_quantity_sold',
            'seller_name', 'seller_account',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'product_cost_incl_vat', 'has_cost_data',
            'cost_updated_at', 'last_order_date', 'total_quantity_sold',
            'created_at', 'updated_at'
        ]
    
    def get_effective_commission_rate(self, obj):
        return obj.get_effective_commission_rate()


class ProductCostUpdateSerializer(serializers.Serializer):
    """Serializer for updating product cost."""
    
    product_cost_excl_vat = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=True,
        help_text='Ürün maliyeti (KDV hariç, TL)'
    )
    purchase_vat_rate = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        default=20.00,
        help_text='Alış KDV oranı (%)'
    )
    sales_vat_rate = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        help_text='Satış KDV oranı (%)'
    )
    commission_rate = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        allow_null=True,
        help_text='Komisyon oranı (%). Boşsa satıcı varsayılanı kullanılır.'
    )


class ProductCostHistorySerializer(serializers.ModelSerializer):
    """Serializer for cost history."""
    
    class Meta:
        model = ProductCostHistory
        fields = ['id', 'cost_excl_vat', 'vat_rate', 'effective_date', 'created_at']


class BulkCostUploadSerializer(serializers.ModelSerializer):
    """Serializer for bulk upload status."""
    
    class Meta:
        model = BulkCostUpload
        fields = [
            'id', 'file_name', 'status',
            'total_rows', 'processed_rows', 'success_count', 'error_count',
            'error_details', 'created_at', 'processed_at'
        ]
        read_only_fields = [
            'id', 'status', 'total_rows', 'processed_rows',
            'success_count', 'error_count', 'error_details',
            'created_at', 'processed_at'
        ]


class BulkCostUploadCreateSerializer(serializers.Serializer):
    """Serializer for creating bulk upload."""
    
    seller_account = serializers.IntegerField(
        required=True,
        help_text='Satıcı hesabı ID'
    )
    file = serializers.FileField(
        required=True,
        help_text='Excel dosyası (.xlsx)'
    )
    
    def validate_file(self, value):
        """Validate file type."""
        if not value.name.endswith(('.xlsx', '.xls')):
            raise serializers.ValidationError(
                'Sadece Excel dosyaları (.xlsx, .xls) kabul edilir.'
            )
        # Max 5MB
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError(
                'Dosya boyutu 5MB\'dan küçük olmalıdır.'
            )
        return value


class ProductListFilterSerializer(serializers.Serializer):
    """Serializer for product list filters."""
    
    seller_account = serializers.IntegerField(required=False)
    has_cost_data = serializers.BooleanField(required=False)
    is_active = serializers.BooleanField(required=False)
    search = serializers.CharField(required=False, max_length=100)
    category = serializers.CharField(required=False, max_length=255)
    brand = serializers.CharField(required=False, max_length=255)
