from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Union


@dataclass(frozen=True)
class Money:
    """Immutable money value object for precise financial calculations."""
    
    amount: Decimal
    currency: str = "INR"
    
    def __post_init__(self):
        """Validate and normalize money data."""
        # Convert to Decimal if needed
        if isinstance(self.amount, (int, float, str)):
            object.__setattr__(self, 'amount', Decimal(str(self.amount)))
        
        # Ensure amount is rounded to 2 decimal places
        object.__setattr__(
            self, 
            'amount', 
            self.amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        )
        
        # Validate currency code (ISO 4217)
        if not self.currency or len(self.currency) != 3:
            raise ValueError("Currency must be a 3-letter ISO code (e.g., INR, USD)")
        
        # Normalize currency to uppercase
        object.__setattr__(self, 'currency', self.currency.upper())
    
    def __str__(self) -> str:
        """String representation of money."""
        return f"{self.currency} {self.amount:,.2f}"
    
    def __add__(self, other: "Money") -> "Money":
        """Add two money values."""
        if not isinstance(other, Money):
            raise TypeError("Can only add Money to Money")
        if self.currency != other.currency:
            raise ValueError(f"Cannot add different currencies: {self.currency} and {other.currency}")
        return Money(self.amount + other.amount, self.currency)
    
    def __sub__(self, other: "Money") -> "Money":
        """Subtract two money values."""
        if not isinstance(other, Money):
            raise TypeError("Can only subtract Money from Money")
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract different currencies: {self.currency} and {other.currency}")
        return Money(self.amount - other.amount, self.currency)
    
    def __mul__(self, multiplier: Union[int, float, Decimal]) -> "Money":
        """Multiply money by a scalar."""
        if not isinstance(multiplier, (int, float, Decimal)):
            raise TypeError("Can only multiply Money by a number")
        return Money(self.amount * Decimal(str(multiplier)), self.currency)
    
    def __truediv__(self, divisor: Union[int, float, Decimal]) -> "Money":
        """Divide money by a scalar."""
        if not isinstance(divisor, (int, float, Decimal)):
            raise TypeError("Can only divide Money by a number")
        if divisor == 0:
            raise ValueError("Cannot divide by zero")
        return Money(self.amount / Decimal(str(divisor)), self.currency)
    
    def __eq__(self, other: object) -> bool:
        """Check equality of two money values."""
        if not isinstance(other, Money):
            return False
        return self.amount == other.amount and self.currency == other.currency
    
    def __lt__(self, other: "Money") -> bool:
        """Check if this money is less than other."""
        if not isinstance(other, Money):
            raise TypeError("Can only compare Money to Money")
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare different currencies: {self.currency} and {other.currency}")
        return self.amount < other.amount
    
    def __le__(self, other: "Money") -> bool:
        """Check if this money is less than or equal to other."""
        return self < other or self == other
    
    def __gt__(self, other: "Money") -> bool:
        """Check if this money is greater than other."""
        if not isinstance(other, Money):
            raise TypeError("Can only compare Money to Money")
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare different currencies: {self.currency} and {other.currency}")
        return self.amount > other.amount
    
    def __ge__(self, other: "Money") -> bool:
        """Check if this money is greater than or equal to other."""
        return self > other or self == other
    
    def is_zero(self) -> bool:
        """Check if amount is zero."""
        return self.amount == Decimal('0.00')
    
    def is_positive(self) -> bool:
        """Check if amount is positive."""
        return self.amount > Decimal('0.00')
    
    def is_negative(self) -> bool:
        """Check if amount is negative."""
        return self.amount < Decimal('0.00')
    
    def apply_percentage(self, percentage: Union[int, float, Decimal]) -> "Money":
        """Apply a percentage to the money amount."""
        percentage_decimal = Decimal(str(percentage)) / Decimal('100')
        return Money(self.amount * percentage_decimal, self.currency)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "amount": str(self.amount),
            "currency": self.currency
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Money":
        """Create from dictionary."""
        return cls(
            amount=data.get("amount", "0"),
            currency=data.get("currency", "INR")
        )
    
    @classmethod
    def zero(cls, currency: str = "INR") -> "Money":
        """Create a zero money value."""
        return cls(Decimal('0.00'), currency)