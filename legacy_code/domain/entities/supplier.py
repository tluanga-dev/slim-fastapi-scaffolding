from typing import Optional, List
from datetime import datetime
from decimal import Decimal

from ..value_objects.supplier_type import SupplierType, SupplierTier, PaymentTerms
from .base import BaseEntity


class Supplier(BaseEntity):
    """Supplier domain entity representing a business partner that provides inventory."""
    
    def __init__(
        self,
        supplier_code: str,
        company_name: str,
        supplier_type: SupplierType,
        contact_person: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None,
        tax_id: Optional[str] = None,
        payment_terms: Optional[PaymentTerms] = None,
        credit_limit: Optional[Decimal] = None,
        supplier_tier: Optional[SupplierTier] = None,
        is_active: bool = True,
        created_by: Optional[str] = None,
        **kwargs
    ):
        # Set internal attributes first to avoid property conflicts
        self._supplier_code = supplier_code
        self._company_name = company_name
        self._supplier_type = supplier_type
        self._contact_person = contact_person
        self._email = email
        self._phone = phone
        self._address = address
        self._tax_id = tax_id
        self._payment_terms = payment_terms or PaymentTerms.NET30
        self._credit_limit = credit_limit or Decimal('0')
        self._supplier_tier = supplier_tier or SupplierTier.STANDARD
        self._is_active = is_active
        
        # Now call super().__init__ with the filtered kwargs
        base_kwargs = {k: v for k, v in kwargs.items() 
                      if k in ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']}
        base_kwargs['is_active'] = is_active
        super().__init__(**base_kwargs)
        
        # Performance metrics
        self._total_orders = 0
        self._total_spend = Decimal('0')
        self._average_delivery_days = 0
        self._quality_rating = Decimal('0')
        self._last_order_date: Optional[datetime] = None
        
        if created_by:
            self._created_by = created_by

    @property
    def supplier_code(self) -> str:
        return self._supplier_code

    @property
    def company_name(self) -> str:
        return self._company_name

    @property
    def supplier_type(self) -> SupplierType:
        return self._supplier_type

    @property
    def contact_person(self) -> Optional[str]:
        return self._contact_person

    @property
    def email(self) -> Optional[str]:
        return self._email

    @property
    def phone(self) -> Optional[str]:
        return self._phone

    @property
    def address(self) -> Optional[str]:
        return self._address

    @property
    def tax_id(self) -> Optional[str]:
        return self._tax_id

    @property
    def payment_terms(self) -> PaymentTerms:
        return self._payment_terms

    @property
    def credit_limit(self) -> Decimal:
        return self._credit_limit

    @property
    def supplier_tier(self) -> SupplierTier:
        return self._supplier_tier

    @property
    def is_active(self) -> bool:
        return self._is_active
    
    @is_active.setter
    def is_active(self, value: bool) -> None:
        self._is_active = value

    @property
    def total_orders(self) -> int:
        return self._total_orders

    @property
    def total_spend(self) -> Decimal:
        return self._total_spend

    @property
    def average_delivery_days(self) -> int:
        return self._average_delivery_days

    @property
    def quality_rating(self) -> Decimal:
        return self._quality_rating

    @property
    def last_order_date(self) -> Optional[datetime]:
        return self._last_order_date

    def update_contact_info(
        self,
        contact_person: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None,
        updated_by: Optional[str] = None
    ) -> None:
        """Update supplier contact information."""
        if contact_person is not None:
            self._contact_person = contact_person
        if email is not None:
            self._email = email
        if phone is not None:
            self._phone = phone
        if address is not None:
            self._address = address
            
        self.update_timestamp(updated_by)

    def update_business_info(
        self,
        company_name: Optional[str] = None,
        tax_id: Optional[str] = None,
        supplier_type: Optional[SupplierType] = None,
        updated_by: Optional[str] = None
    ) -> None:
        """Update supplier business information."""
        if company_name:
            self._company_name = company_name
        if tax_id is not None:
            self._tax_id = tax_id
        if supplier_type:
            self._supplier_type = supplier_type
            
        self.update_timestamp(updated_by)

    def update_payment_terms(
        self,
        payment_terms: PaymentTerms,
        credit_limit: Optional[Decimal] = None,
        updated_by: Optional[str] = None
    ) -> None:
        """Update supplier payment terms and credit limit."""
        self._payment_terms = payment_terms
        if credit_limit is not None:
            if credit_limit < 0:
                raise ValueError("Credit limit cannot be negative")
            self._credit_limit = credit_limit
            
        self.update_timestamp(updated_by)

    def update_tier(
        self,
        supplier_tier: SupplierTier,
        updated_by: Optional[str] = None
    ) -> None:
        """Update supplier tier classification."""
        self._supplier_tier = supplier_tier
        self.update_timestamp(updated_by)

    def deactivate(self, updated_by: Optional[str] = None) -> None:
        """Deactivate the supplier."""
        self._is_active = False
        self.update_timestamp(updated_by)

    def activate(self, updated_by: Optional[str] = None) -> None:
        """Activate the supplier."""
        self._is_active = True
        self.update_timestamp(updated_by)

    def update_performance_metrics(
        self,
        total_orders: Optional[int] = None,
        total_spend: Optional[Decimal] = None,
        average_delivery_days: Optional[int] = None,
        quality_rating: Optional[Decimal] = None,
        last_order_date: Optional[datetime] = None
    ) -> None:
        """Update supplier performance metrics."""
        if total_orders is not None:
            self._total_orders = total_orders
        if total_spend is not None:
            self._total_spend = total_spend
        if average_delivery_days is not None:
            self._average_delivery_days = average_delivery_days
        if quality_rating is not None:
            if not (0 <= quality_rating <= 5):
                raise ValueError("Quality rating must be between 0 and 5")
            self._quality_rating = quality_rating
        if last_order_date is not None:
            self._last_order_date = last_order_date

    def get_display_name(self) -> str:
        """Get the display name for the supplier."""
        return self._company_name

    def can_place_order(self, order_amount: Decimal) -> bool:
        """Check if an order can be placed with this supplier."""
        if not self._is_active:
            return False
        if self._credit_limit > 0 and order_amount > self._credit_limit:
            return False
        return True

    def get_performance_score(self) -> Decimal:
        """Calculate overall performance score (0-100)."""
        if self._total_orders == 0:
            return Decimal('0')
            
        # Weighted scoring: Quality (40%), Delivery (30%), Tier (30%)
        quality_score = (self._quality_rating / 5) * 40
        
        # Delivery score (inverse of delivery days, capped at 30 days)
        delivery_score = max(0, (30 - min(self._average_delivery_days, 30)) / 30) * 30
        
        # Tier score
        tier_scores = {
            SupplierTier.PREFERRED: 30,
            SupplierTier.STANDARD: 20,
            SupplierTier.RESTRICTED: 10
        }
        tier_score = tier_scores.get(self._supplier_tier, 15)
        
        return quality_score + Decimal(str(delivery_score)) + Decimal(str(tier_score))

    def validate(self) -> List[str]:
        """Validate supplier data and return list of errors."""
        errors = []
        
        if not self._supplier_code or not self._supplier_code.strip():
            errors.append("Supplier code is required")
            
        if not self._company_name or not self._company_name.strip():
            errors.append("Company name is required")
            
        if self._email and '@' not in self._email:
            errors.append("Invalid email format")
            
        if self._credit_limit < 0:
            errors.append("Credit limit cannot be negative")
            
        return errors

    def __str__(self) -> str:
        return f"Supplier({self._supplier_code}: {self._company_name})"

    def __repr__(self) -> str:
        return (f"Supplier(id={self.id}, supplier_code='{self._supplier_code}', "
                f"company_name='{self._company_name}', supplier_type={self._supplier_type})")