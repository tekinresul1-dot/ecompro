"""
Profit Calculator Service

THE CORE CALCULATION ENGINE for Trendyol order profitability.

This module implements exact Turkish accounting logic with:
- VAT settlement (Hesaplanan KDV - İndirilecek KDV)
- Commission on KDV-excluded prices
- All decimal operations with explicit rounding

FORMULA BREAKDOWN:

1. NET SALE PRICE (KDV Dahil):
   net_sale_price = unit_price × quantity - discount_amount

2. SALES VAT (Satış KDV'si):
   sales_vat = net_sale_price - (net_sale_price / (1 + sales_vat_rate))
   net_sale_price_excl_vat = net_sale_price - sales_vat

3. PRODUCT COST:
   purchase_vat = product_cost_excl_vat × purchase_vat_rate
   product_cost_incl_vat = product_cost_excl_vat + purchase_vat

4. COMMISSION (Trendyol applies on KDV-excluded sale price):
   commission_base = net_sale_price_excl_vat
   commission_amount_excl_vat = commission_base × commission_rate
   commission_vat = commission_amount_excl_vat × commission_vat_rate
   commission_total = commission_amount_excl_vat + commission_vat

5. CARGO COST:
   cargo_vat = cargo_cost_excl_vat × cargo_vat_rate
   cargo_cost_total = cargo_cost_excl_vat + cargo_vat

6. PLATFORM SERVICE FEE:
   platform_fee_vat = platform_fee_excl_vat × platform_fee_vat_rate
   platform_fee_total = platform_fee_excl_vat + platform_fee_vat

7. VAT SETTLEMENT (KDV Mahsuplaşma):
   total_output_vat = sales_vat  # Hesaplanan KDV
   total_input_vat = purchase_vat + commission_vat + cargo_vat + platform_fee_vat  # İndirilecek KDV
   net_vat_payable = total_output_vat - total_input_vat  # Ödenecek KDV (can be negative = refund)

8. TOTAL TRENDYOL DEDUCTIONS:
   total_trendyol_deductions = commission_total + cargo_cost_total + platform_fee_total

9. TOTAL COST:
   total_cost = product_cost_excl_vat + net_vat_payable + commission_amount_excl_vat + 
                cargo_cost_excl_vat + platform_fee_excl_vat + withholding_tax

10. NET PROFIT:
    net_profit = net_sale_price_excl_vat - total_cost

11. PROFIT MARGIN:
    profit_margin_percent = (net_profit / net_sale_price_excl_vat) × 100

"""

from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass, asdict
from typing import Optional, List
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class CalculationResult:
    """
    Complete profit calculation result.
    
    All monetary values are Decimal with 4 decimal places.
    """
    
    # Revenue
    gross_sale_price: Decimal
    discount_amount: Decimal
    net_sale_price: Decimal
    
    # Product cost
    product_cost_excl_vat: Decimal
    purchase_vat_rate: Decimal
    purchase_vat: Decimal
    product_cost_incl_vat: Decimal
    
    # Sales VAT
    sales_vat_rate: Decimal
    sales_vat: Decimal
    net_sale_price_excl_vat: Decimal
    
    # Commission
    commission_rate: Decimal
    commission_amount_excl_vat: Decimal
    commission_vat_rate: Decimal
    commission_vat: Decimal
    commission_total: Decimal
    
    # Cargo
    cargo_cost_excl_vat: Decimal
    cargo_vat_rate: Decimal
    cargo_vat: Decimal
    cargo_cost_total: Decimal
    
    # Platform fee
    platform_fee_excl_vat: Decimal
    platform_fee_vat_rate: Decimal
    platform_fee_vat: Decimal
    platform_fee_total: Decimal
    
    # Withholding tax
    withholding_tax_rate: Decimal
    withholding_tax: Decimal
    
    # VAT calculations
    total_output_vat: Decimal
    total_input_vat: Decimal
    net_vat_payable: Decimal
    
    # Totals
    total_trendyol_deductions: Decimal
    total_cost: Decimal
    
    # Profit
    net_profit: Decimal
    profit_margin_percent: Decimal
    
    # Flags
    is_profitable: bool
    has_cost_data: bool
    calculation_notes: str = ''
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return asdict(self)


class ProfitCalculator:
    """
    Deterministic profit calculator for Trendyol order items.
    
    All calculations use Decimal with explicit rounding for auditability.
    This ensures Excel-style accounting accuracy.
    """
    
    ROUNDING = ROUND_HALF_UP
    PRECISION = Decimal('0.0001')  # 4 decimal places
    DISPLAY_PRECISION = Decimal('0.01')  # 2 decimal places for display
    
    # Default rates
    DEFAULT_VAT_RATE = Decimal('20.00')
    DEFAULT_COMMISSION_VAT_RATE = Decimal('20.00')
    DEFAULT_CARGO_VAT_RATE = Decimal('20.00')
    DEFAULT_PLATFORM_VAT_RATE = Decimal('20.00')
    
    def __init__(
        self,
        default_vat_rate: Optional[Decimal] = None,
        default_commission_vat_rate: Optional[Decimal] = None,
    ):
        """
        Initialize calculator with default rates.
        
        Args:
            default_vat_rate: Default VAT rate for sales (%)
            default_commission_vat_rate: VAT rate on commission (%)
        """
        self.default_vat_rate = default_vat_rate or self.DEFAULT_VAT_RATE
        self.default_commission_vat_rate = (
            default_commission_vat_rate or self.DEFAULT_COMMISSION_VAT_RATE
        )
    
    def _to_decimal(self, value, default: Decimal = Decimal('0')) -> Decimal:
        """Safely convert any value to Decimal."""
        if value is None:
            return default
        try:
            if isinstance(value, Decimal):
                return value
            return Decimal(str(value))
        except Exception:
            return default
    
    def _round(self, value: Decimal) -> Decimal:
        """Round to calculation precision (4 decimal places)."""
        return value.quantize(self.PRECISION, self.ROUNDING)
    
    def _round_display(self, value: Decimal) -> Decimal:
        """Round to display precision (2 decimal places)."""
        return value.quantize(self.DISPLAY_PRECISION, self.ROUNDING)
    
    def _percent_to_decimal(self, percent: Decimal) -> Decimal:
        """Convert percentage to decimal (e.g., 20.00 -> 0.20)."""
        return percent / Decimal('100')
    
    def calculate(
        self,
        # Sale info
        unit_price: Decimal,
        quantity: int,
        discount_amount: Decimal = Decimal('0'),
        
        # Product cost
        product_cost_excl_vat: Optional[Decimal] = None,
        purchase_vat_rate: Decimal = Decimal('20.00'),
        
        # Rates
        sales_vat_rate: Decimal = Decimal('20.00'),
        commission_rate: Decimal = Decimal('12.00'),
        
        # Trendyol costs
        cargo_cost_excl_vat: Decimal = Decimal('0'),
        platform_fee_excl_vat: Decimal = Decimal('0'),
        
        # Optional
        withholding_tax_rate: Decimal = Decimal('0'),
        commission_vat_rate: Optional[Decimal] = None,
        cargo_vat_rate: Decimal = Decimal('20.00'),
        platform_vat_rate: Decimal = Decimal('20.00'),
    ) -> CalculationResult:
        """
        Calculate complete profit breakdown for a single order item.
        
        Args:
            unit_price: Unit sale price (KDV dahil / VAT included)
            quantity: Number of items
            discount_amount: Total discount applied
            product_cost_excl_vat: Product cost excluding VAT (None if unknown)
            purchase_vat_rate: VAT rate on product purchase (%)
            sales_vat_rate: VAT rate on sale (%)
            commission_rate: Trendyol commission rate (%)
            cargo_cost_excl_vat: Cargo cost excluding VAT
            platform_fee_excl_vat: Platform service fee excluding VAT
            withholding_tax_rate: Withholding tax rate (usually 0)
            commission_vat_rate: VAT rate on commission (defaults to 20%)
            cargo_vat_rate: VAT rate on cargo (defaults to 20%)
            platform_vat_rate: VAT rate on platform fee (defaults to 20%)
            
        Returns:
            CalculationResult with all calculated values
        """
        # Convert all inputs to Decimal
        unit_price = self._to_decimal(unit_price)
        quantity = int(quantity) if quantity else 1
        discount_amount = self._to_decimal(discount_amount)
        
        sales_vat_rate = self._to_decimal(sales_vat_rate, self.default_vat_rate)
        commission_rate = self._to_decimal(commission_rate)
        purchase_vat_rate = self._to_decimal(purchase_vat_rate, self.default_vat_rate)
        
        cargo_cost_excl_vat = self._to_decimal(cargo_cost_excl_vat)
        platform_fee_excl_vat = self._to_decimal(platform_fee_excl_vat)
        withholding_tax_rate = self._to_decimal(withholding_tax_rate)
        
        commission_vat_rate = self._to_decimal(
            commission_vat_rate, self.default_commission_vat_rate
        )
        cargo_vat_rate = self._to_decimal(cargo_vat_rate, self.DEFAULT_CARGO_VAT_RATE)
        platform_vat_rate = self._to_decimal(platform_vat_rate, self.DEFAULT_PLATFORM_VAT_RATE)
        
        # Flag for cost data availability
        has_cost_data = product_cost_excl_vat is not None
        if not has_cost_data:
            product_cost_excl_vat = Decimal('0')
        else:
            product_cost_excl_vat = self._to_decimal(product_cost_excl_vat)
        
        notes = []
        
        # =========================================================
        # 1. REVENUE CALCULATIONS
        # =========================================================
        gross_sale_price = self._round(unit_price * quantity)
        net_sale_price = self._round(gross_sale_price - discount_amount)
        
        # =========================================================
        # 2. EXTRACT SALES VAT
        # net_sale_price includes VAT, we need to extract it
        # Formula: VAT = net_sale_price - (net_sale_price / (1 + rate))
        # =========================================================
        vat_divisor = Decimal('1') + self._percent_to_decimal(sales_vat_rate)
        net_sale_price_excl_vat = self._round(net_sale_price / vat_divisor)
        sales_vat = self._round(net_sale_price - net_sale_price_excl_vat)
        
        # =========================================================
        # 3. PRODUCT COST WITH VAT
        # =========================================================
        purchase_vat = self._round(
            product_cost_excl_vat * self._percent_to_decimal(purchase_vat_rate)
        )
        product_cost_incl_vat = self._round(product_cost_excl_vat + purchase_vat)
        
        if not has_cost_data:
            notes.append('Ürün maliyeti girilmemiş, 0 olarak hesaplandı.')
        
        # =========================================================
        # 4. COMMISSION CALCULATION
        # Trendyol applies commission on KDV-excluded sale price
        # =========================================================
        commission_amount_excl_vat = self._round(
            net_sale_price_excl_vat * self._percent_to_decimal(commission_rate)
        )
        commission_vat = self._round(
            commission_amount_excl_vat * self._percent_to_decimal(commission_vat_rate)
        )
        commission_total = self._round(commission_amount_excl_vat + commission_vat)
        
        # =========================================================
        # 5. CARGO COST
        # =========================================================
        cargo_vat = self._round(
            cargo_cost_excl_vat * self._percent_to_decimal(cargo_vat_rate)
        )
        cargo_cost_total = self._round(cargo_cost_excl_vat + cargo_vat)
        
        # =========================================================
        # 6. PLATFORM SERVICE FEE
        # =========================================================
        platform_fee_vat = self._round(
            platform_fee_excl_vat * self._percent_to_decimal(platform_vat_rate)
        )
        platform_fee_total = self._round(platform_fee_excl_vat + platform_fee_vat)
        
        # =========================================================
        # 7. VAT SETTLEMENT (KDV MAHSUPLAŞMA)
        # This is critical for Turkish accounting!
        # Output VAT (sales) - Input VAT (purchases) = Net payable
        # =========================================================
        total_output_vat = sales_vat  # Hesaplanan KDV
        total_input_vat = self._round(
            purchase_vat + commission_vat + cargo_vat + platform_fee_vat
        )  # İndirilecek KDV
        net_vat_payable = self._round(total_output_vat - total_input_vat)  # Ödenecek KDV
        
        if net_vat_payable < 0:
            notes.append(f'KDV iade durumu: {abs(net_vat_payable)} TL')
        
        # =========================================================
        # 8. WITHHOLDING TAX (STOPAJ)
        # Usually 0 for most e-commerce sellers
        # =========================================================
        withholding_tax = self._round(
            net_sale_price_excl_vat * self._percent_to_decimal(withholding_tax_rate)
        )
        
        # =========================================================
        # 9. TOTAL TRENDYOL DEDUCTIONS
        # All Trendyol-retained amounts (with VAT)
        # =========================================================
        total_trendyol_deductions = self._round(
            commission_total + cargo_cost_total + platform_fee_total
        )
        
        # =========================================================
        # 10. TOTAL COST
        # Sum of all costs (using KDV-excluded where applicable)
        # Net VAT payable is added as it's an actual cash outflow
        # =========================================================
        total_cost = self._round(
            product_cost_excl_vat +
            net_vat_payable +
            commission_amount_excl_vat +
            cargo_cost_excl_vat +
            platform_fee_excl_vat +
            withholding_tax
        )
        
        # =========================================================
        # 11. NET PROFIT
        # Revenue (excl VAT) - Total Cost = Net Profit
        # =========================================================
        net_profit = self._round(net_sale_price_excl_vat - total_cost)
        
        # =========================================================
        # 12. PROFIT MARGIN
        # =========================================================
        if net_sale_price_excl_vat > 0:
            profit_margin_percent = self._round_display(
                (net_profit / net_sale_price_excl_vat) * Decimal('100')
            )
        else:
            profit_margin_percent = Decimal('0')
        
        is_profitable = net_profit > 0
        
        if not is_profitable and has_cost_data:
            notes.append('Bu ürün zarar ediyor!')
        
        return CalculationResult(
            # Revenue
            gross_sale_price=gross_sale_price,
            discount_amount=discount_amount,
            net_sale_price=net_sale_price,
            
            # Product cost
            product_cost_excl_vat=product_cost_excl_vat,
            purchase_vat_rate=purchase_vat_rate,
            purchase_vat=purchase_vat,
            product_cost_incl_vat=product_cost_incl_vat,
            
            # Sales VAT
            sales_vat_rate=sales_vat_rate,
            sales_vat=sales_vat,
            net_sale_price_excl_vat=net_sale_price_excl_vat,
            
            # Commission
            commission_rate=commission_rate,
            commission_amount_excl_vat=commission_amount_excl_vat,
            commission_vat_rate=commission_vat_rate,
            commission_vat=commission_vat,
            commission_total=commission_total,
            
            # Cargo
            cargo_cost_excl_vat=cargo_cost_excl_vat,
            cargo_vat_rate=cargo_vat_rate,
            cargo_vat=cargo_vat,
            cargo_cost_total=cargo_cost_total,
            
            # Platform fee
            platform_fee_excl_vat=platform_fee_excl_vat,
            platform_fee_vat_rate=platform_vat_rate,
            platform_fee_vat=platform_fee_vat,
            platform_fee_total=platform_fee_total,
            
            # Withholding
            withholding_tax_rate=withholding_tax_rate,
            withholding_tax=withholding_tax,
            
            # VAT
            total_output_vat=total_output_vat,
            total_input_vat=total_input_vat,
            net_vat_payable=net_vat_payable,
            
            # Totals
            total_trendyol_deductions=total_trendyol_deductions,
            total_cost=total_cost,
            
            # Profit
            net_profit=net_profit,
            profit_margin_percent=profit_margin_percent,
            
            # Flags
            is_profitable=is_profitable,
            has_cost_data=has_cost_data,
            calculation_notes=' | '.join(notes),
        )
    
    def calculate_for_order_item(self, order_item) -> CalculationResult:
        """
        Calculate profit for an OrderItem model instance.
        
        Automatically fetches product cost and rates from related models.
        
        Args:
            order_item: OrderItem model instance
            
        Returns:
            CalculationResult
        """
        # Get product cost if available
        product_cost = None
        purchase_vat_rate = self.default_vat_rate
        sales_vat_rate = self.default_vat_rate
        commission_rate = order_item.commission_rate or Decimal('12.00')
        
        if order_item.product and order_item.product.has_cost_data:
            product_cost = order_item.product.product_cost_excl_vat
            purchase_vat_rate = order_item.product.purchase_vat_rate
            sales_vat_rate = order_item.product.sales_vat_rate
            
            # Use product-specific commission rate if set
            if order_item.product.commission_rate:
                commission_rate = order_item.product.commission_rate
        
        # Extract cargo cost (from Trendyol, might need VAT extraction)
        cargo_cost = order_item.cargo_cost
        # Assuming cargo_cost from Trendyol is VAT-included, extract it
        cargo_cost_excl_vat = self._round(
            cargo_cost / (Decimal('1') + self._percent_to_decimal(Decimal('20')))
        )
        
        # Platform fee (from Trendyol)
        platform_fee = order_item.platform_service_fee
        platform_fee_excl_vat = self._round(
            platform_fee / (Decimal('1') + self._percent_to_decimal(Decimal('20')))
        )
        
        return self.calculate(
            unit_price=order_item.unit_price,
            quantity=order_item.quantity,
            discount_amount=order_item.discount_amount,
            product_cost_excl_vat=product_cost,
            purchase_vat_rate=purchase_vat_rate,
            sales_vat_rate=sales_vat_rate,
            commission_rate=commission_rate,
            cargo_cost_excl_vat=cargo_cost_excl_vat,
            platform_fee_excl_vat=platform_fee_excl_vat,
        )


# Singleton instance
_calculator: Optional[ProfitCalculator] = None


def get_calculator() -> ProfitCalculator:
    """Get the singleton calculator instance."""
    global _calculator
    if _calculator is None:
        _calculator = ProfitCalculator()
    return _calculator
