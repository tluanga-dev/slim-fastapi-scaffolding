from enum import Enum


class TransactionType(str, Enum):
    """Transaction type enumeration."""

    SALE = "SALE"
    RENTAL = "RENTAL"
    RETURN = "RETURN"
    EXCHANGE = "EXCHANGE"
    REFUND = "REFUND"
    ADJUSTMENT = "ADJUSTMENT"
    PURCHASE = "PURCHASE"


class TransactionStatus(str, Enum):
    """Transaction status enumeration."""

    DRAFT = "DRAFT"
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


class PaymentMethod(str, Enum):
    """Payment method enumeration."""

    CASH = "CASH"
    CREDIT_CARD = "CREDIT_CARD"
    DEBIT_CARD = "DEBIT_CARD"
    BANK_TRANSFER = "BANK_TRANSFER"
    CHECK = "CHECK"
    STORE_CREDIT = "STORE_CREDIT"
    DEPOSIT = "DEPOSIT"
    OTHER = "OTHER"


class PaymentStatus(str, Enum):
    """Payment status enumeration."""

    PENDING = "PENDING"
    PAID = "PAID"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    OVERDUE = "OVERDUE"
    REFUNDED = "REFUNDED"
    CANCELLED = "CANCELLED"


class RentalPeriodUnit(str, Enum):
    """Rental period unit enumeration."""

    HOUR = "HOUR"
    DAY = "DAY"
    WEEK = "WEEK"
    MONTH = "MONTH"
    YEAR = "YEAR"


class LineItemType(str, Enum):
    """Line item type enumeration."""

    PRODUCT = "PRODUCT"
    SERVICE = "SERVICE"
    FEE = "FEE"
    DISCOUNT = "DISCOUNT"
    TAX = "TAX"
    DEPOSIT = "DEPOSIT"
    LATE_FEE = "LATE_FEE"
    DAMAGE_FEE = "DAMAGE_FEE"
    REFUND = "REFUND"
