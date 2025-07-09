from enum import Enum


class TransactionType(str, Enum):
    """Transaction type enumeration."""
    SALE = "sale"
    RENTAL = "rental"
    RETURN = "return"
    EXCHANGE = "exchange"
    REFUND = "refund"
    ADJUSTMENT = "adjustment"
    PURCHASE = "purchase"
    TRANSFER = "transfer"


class TransactionStatus(str, Enum):
    """Transaction status enumeration."""
    DRAFT = "draft"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentStatus(str, Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    OVERDUE = "overdue"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class PaymentMethod(str, Enum):
    """Payment method enumeration."""
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    CHECK = "check"
    STORE_CREDIT = "store_credit"
    DIGITAL_WALLET = "digital_wallet"
    CRYPTOCURRENCY = "cryptocurrency"
    INSTALLMENT = "installment"
    DEPOSIT = "deposit"
    OTHER = "other"


class RentalPeriodUnit(str, Enum):
    """Rental period unit enumeration."""
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class LineItemType(str, Enum):
    """Line item type enumeration."""
    PRODUCT = "product"
    SERVICE = "service"
    RENTAL = "rental"
    DEPOSIT = "deposit"
    FEE = "fee"
    DISCOUNT = "discount"
    TAX = "tax"
    SHIPPING = "shipping"
    ADJUSTMENT = "adjustment"
    LATE_FEE = "late_fee"
    DAMAGE_FEE = "damage_fee"
    REFUND = "refund"