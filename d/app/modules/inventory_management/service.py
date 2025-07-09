from typing import List, Optional, Tuple
from uuid import UUID
from datetime import datetime
from decimal import Decimal
import math

from .repository import TransactionHeaderRepository, TransactionLineRepository
from .models import TransactionHeaderModel, TransactionLineModel
from .schemas import (
    TransactionHeaderCreate,
    TransactionHeaderUpdate,
    TransactionHeaderResponse,
    TransactionHeaderWithDetails,
    TransactionHeaderListResponse,
    TransactionLineCreate,
    TransactionLineUpdate,
    TransactionLineResponse,
    TransactionLineWithDetails,
    TransactionLineListResponse,
    TransactionHeaderWithLines,
    TransactionCreateWithLines
)
from .enums import TransactionType, TransactionStatus, PaymentStatus, LineItemType
from app.core.errors import NotFoundError, ValidationError


class TransactionHeaderService:
    """Service for TransactionHeader business logic."""
    
    def __init__(self, repository: TransactionHeaderRepository):
        self.repository = repository
    
    async def create_transaction(
        self, 
        transaction_data: TransactionHeaderCreate
    ) -> TransactionHeaderResponse:
        """Create a new transaction header."""
        # Validate business rules
        await self._validate_transaction_creation(transaction_data)
        
        # Auto-generate transaction number if not provided
        if not transaction_data.transaction_number:
            transaction_data.transaction_number = await self._generate_transaction_number(
                transaction_data.transaction_type
            )
        
        # Calculate totals if not provided
        self._calculate_transaction_totals(transaction_data)
        
        transaction = await self.repository.create(transaction_data)
        return TransactionHeaderResponse.model_validate(transaction)
    
    async def get_transaction(self, transaction_id: UUID) -> TransactionHeaderResponse:
        """Get transaction header by ID."""
        transaction = await self.repository.get_by_id(transaction_id)
        if not transaction:
            raise NotFoundError(f"Transaction with ID {transaction_id} not found")
        
        return TransactionHeaderResponse.model_validate(transaction)
    
    async def get_transaction_with_details(
        self, 
        transaction_id: UUID
    ) -> TransactionHeaderWithDetails:
        """Get transaction header with all related details."""
        transaction = await self.repository.get_with_details(transaction_id)
        if not transaction:
            raise NotFoundError(f"Transaction with ID {transaction_id} not found")
        
        return TransactionHeaderWithDetails.model_validate(transaction)
    
    async def get_transaction_by_number(
        self, 
        transaction_number: str
    ) -> TransactionHeaderResponse:
        """Get transaction header by transaction number."""
        transaction = await self.repository.get_by_transaction_number(transaction_number)
        if not transaction:
            raise NotFoundError(f"Transaction with number {transaction_number} not found")
        
        return TransactionHeaderResponse.model_validate(transaction)
    
    async def get_transactions(
        self,
        page: int = 1,
        size: int = 50,
        transaction_type: Optional[TransactionType] = None,
        status: Optional[TransactionStatus] = None,
        payment_status: Optional[PaymentStatus] = None,
        customer_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> TransactionHeaderListResponse:
        """Get paginated list of transaction headers with filtering."""
        # Calculate pagination
        skip = (page - 1) * size
        
        # Get transactions and total count
        transactions = await self.repository.get_all(
            skip=skip,
            limit=size,
            transaction_type=transaction_type,
            status=status,
            payment_status=payment_status,
            customer_id=customer_id,
            location_id=location_id,
            start_date=start_date,
            end_date=end_date
        )
        
        total = await self.repository.count_all(
            transaction_type=transaction_type,
            status=status,
            payment_status=payment_status,
            customer_id=customer_id,
            location_id=location_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Calculate total pages
        pages = math.ceil(total / size) if total > 0 else 0
        
        # Convert to response models
        transaction_responses = [
            TransactionHeaderResponse.model_validate(transaction)
            for transaction in transactions
        ]
        
        return TransactionHeaderListResponse(
            items=transaction_responses,
            total=total,
            page=page,
            size=size,
            pages=pages
        )
    
    async def update_transaction(
        self,
        transaction_id: UUID,
        transaction_data: TransactionHeaderUpdate
    ) -> TransactionHeaderResponse:
        """Update a transaction header."""
        # Validate business rules for update
        await self._validate_transaction_update(transaction_id, transaction_data)
        
        # Recalculate totals if financial fields are being updated
        if any(field in transaction_data.model_dump(exclude_unset=True) 
               for field in ['subtotal', 'discount_amount', 'tax_amount']):
            self._calculate_transaction_totals_update(transaction_data)
        
        transaction = await self.repository.update(transaction_id, transaction_data)
        if not transaction:
            raise NotFoundError(f"Transaction with ID {transaction_id} not found")
        
        return TransactionHeaderResponse.model_validate(transaction)
    
    async def delete_transaction(self, transaction_id: UUID) -> bool:
        """Delete (soft delete) a transaction header."""
        # Validate that transaction can be deleted
        transaction = await self.repository.get_by_id(transaction_id)
        if not transaction:
            raise NotFoundError(f"Transaction with ID {transaction_id} not found")
        
        if transaction.status in [TransactionStatus.COMPLETED, TransactionStatus.CONFIRMED]:
            raise ValidationError("Cannot delete completed or confirmed transactions")
        
        return await self.repository.delete(transaction_id)
    
    async def get_customer_transactions(
        self,
        customer_id: UUID,
        page: int = 1,
        size: int = 50
    ) -> List[TransactionHeaderResponse]:
        """Get all transactions for a specific customer."""
        skip = (page - 1) * size
        transactions = await self.repository.get_by_customer(customer_id, skip, size)
        
        return [
            TransactionHeaderResponse.model_validate(transaction)
            for transaction in transactions
        ]
    
    async def get_pending_payments(self) -> List[TransactionHeaderResponse]:
        """Get all transactions with pending payments."""
        transactions = await self.repository.get_pending_payments()
        
        return [
            TransactionHeaderResponse.model_validate(transaction)
            for transaction in transactions
        ]
    
    async def process_payment(
        self,
        transaction_id: UUID,
        payment_amount: Decimal,
        payment_method: Optional[str] = None,
        payment_reference: Optional[str] = None
    ) -> TransactionHeaderResponse:
        """Process a payment for a transaction."""
        transaction = await self.repository.get_by_id(transaction_id)
        if not transaction:
            raise NotFoundError(f"Transaction with ID {transaction_id} not found")
        
        # Validate payment
        if payment_amount <= 0:
            raise ValidationError("Payment amount must be greater than zero")
        
        remaining_amount = transaction.total_amount - transaction.paid_amount
        if payment_amount > remaining_amount:
            raise ValidationError(f"Payment amount exceeds remaining balance of {remaining_amount}")
        
        # Update transaction
        new_paid_amount = transaction.paid_amount + payment_amount
        update_data = TransactionHeaderUpdate(
            paid_amount=new_paid_amount,
            payment_method=payment_method,
            payment_reference=payment_reference
        )
        
        # Update payment status
        if new_paid_amount >= transaction.total_amount:
            update_data.payment_status = PaymentStatus.PAID
        else:
            update_data.payment_status = PaymentStatus.PARTIAL
        
        return await self.update_transaction(transaction_id, update_data)
    
    async def _validate_transaction_creation(self, transaction_data: TransactionHeaderCreate):
        """Validate business rules for transaction creation."""
        # Check for duplicate transaction number
        if transaction_data.transaction_number:
            existing = await self.repository.get_by_transaction_number(
                transaction_data.transaction_number
            )
            if existing:
                raise ValidationError(
                    f"Transaction number {transaction_data.transaction_number} already exists"
                )
        
        # Validate financial amounts
        if transaction_data.subtotal < 0:
            raise ValidationError("Subtotal cannot be negative")
        
        if transaction_data.discount_amount < 0:
            raise ValidationError("Discount amount cannot be negative")
        
        if transaction_data.tax_amount < 0:
            raise ValidationError("Tax amount cannot be negative")
    
    async def _validate_transaction_update(
        self, 
        transaction_id: UUID, 
        transaction_data: TransactionHeaderUpdate
    ):
        """Validate business rules for transaction update."""
        transaction = await self.repository.get_by_id(transaction_id)
        if not transaction:
            return
        
        # Prevent updating completed transactions
        if (transaction.status == TransactionStatus.COMPLETED and 
            transaction_data.status != TransactionStatus.COMPLETED):
            raise ValidationError("Cannot modify completed transactions")
        
        # Validate transaction number uniqueness if being updated
        if transaction_data.transaction_number:
            existing = await self.repository.get_by_transaction_number(
                transaction_data.transaction_number
            )
            if existing and existing.id != transaction_id:
                raise ValidationError(
                    f"Transaction number {transaction_data.transaction_number} already exists"
                )
    
    def _calculate_transaction_totals(self, transaction_data: TransactionHeaderCreate):
        """Calculate transaction totals."""
        # Calculate total amount
        total_before_tax = transaction_data.subtotal - transaction_data.discount_amount
        transaction_data.total_amount = total_before_tax + transaction_data.tax_amount
    
    def _calculate_transaction_totals_update(self, transaction_data: TransactionHeaderUpdate):
        """Calculate transaction totals for update."""
        if (transaction_data.subtotal is not None or 
            transaction_data.discount_amount is not None or 
            transaction_data.tax_amount is not None):
            
            # Use provided values or default to 0 for calculation
            subtotal = transaction_data.subtotal or Decimal('0.00')
            discount = transaction_data.discount_amount or Decimal('0.00')
            tax = transaction_data.tax_amount or Decimal('0.00')
            
            total_before_tax = subtotal - discount
            transaction_data.total_amount = total_before_tax + tax
    
    async def _generate_transaction_number(self, transaction_type: TransactionType) -> str:
        """Generate a unique transaction number."""
        # Simple implementation - could be enhanced with more sophisticated numbering
        import time
        timestamp = int(time.time())
        type_prefix = {
            TransactionType.SALE: "SAL",
            TransactionType.RENTAL: "RNT",
            TransactionType.RETURN: "RTN",
            TransactionType.REFUND: "REF",
            TransactionType.PURCHASE: "PUR",
            TransactionType.ADJUSTMENT: "ADJ",
            TransactionType.TRANSFER: "TRF"
        }.get(transaction_type, "TXN")
        
        return f"{type_prefix}-{timestamp}"


class TransactionLineService:
    """Service for TransactionLine business logic."""
    
    def __init__(self, repository: TransactionLineRepository):
        self.repository = repository
    
    async def create_line(
        self, 
        line_data: TransactionLineCreate
    ) -> TransactionLineResponse:
        """Create a new transaction line."""
        # Validate business rules
        await self._validate_line_creation(line_data)
        
        # Auto-assign line number if not provided
        if not line_data.line_number:
            line_data.line_number = await self.repository.get_next_line_number(
                line_data.transaction_id
            )
        
        # Calculate line totals
        self._calculate_line_totals(line_data)
        
        line = await self.repository.create(line_data)
        return TransactionLineResponse.model_validate(line)
    
    async def get_line(self, line_id: UUID) -> TransactionLineResponse:
        """Get transaction line by ID."""
        line = await self.repository.get_by_id(line_id)
        if not line:
            raise NotFoundError(f"Transaction line with ID {line_id} not found")
        
        return TransactionLineResponse.model_validate(line)
    
    async def get_line_with_details(
        self, 
        line_id: UUID
    ) -> TransactionLineWithDetails:
        """Get transaction line with all related details."""
        line = await self.repository.get_with_details(line_id)
        if not line:
            raise NotFoundError(f"Transaction line with ID {line_id} not found")
        
        return TransactionLineWithDetails.model_validate(line)
    
    async def get_lines_by_transaction(
        self,
        transaction_id: UUID,
        page: int = 1,
        size: int = 50
    ) -> TransactionLineListResponse:
        """Get all lines for a specific transaction."""
        skip = (page - 1) * size
        
        lines = await self.repository.get_by_transaction_id(
            transaction_id, skip, size
        )
        
        total = await self.repository.count_all(transaction_id=transaction_id)
        pages = math.ceil(total / size) if total > 0 else 0
        
        line_responses = [
            TransactionLineResponse.model_validate(line)
            for line in lines
        ]
        
        return TransactionLineListResponse(
            items=line_responses,
            total=total,
            page=page,
            size=size,
            pages=pages
        )
    
    async def get_lines(
        self,
        page: int = 1,
        size: int = 50,
        transaction_id: Optional[UUID] = None,
        line_type: Optional[LineItemType] = None,
        item_id: Optional[UUID] = None,
        inventory_unit_id: Optional[UUID] = None
    ) -> TransactionLineListResponse:
        """Get paginated list of transaction lines with filtering."""
        skip = (page - 1) * size
        
        lines = await self.repository.get_all(
            skip=skip,
            limit=size,
            transaction_id=transaction_id,
            line_type=line_type,
            item_id=item_id,
            inventory_unit_id=inventory_unit_id
        )
        
        total = await self.repository.count_all(
            transaction_id=transaction_id,
            line_type=line_type,
            item_id=item_id,
            inventory_unit_id=inventory_unit_id
        )
        
        pages = math.ceil(total / size) if total > 0 else 0
        
        line_responses = [
            TransactionLineResponse.model_validate(line)
            for line in lines
        ]
        
        return TransactionLineListResponse(
            items=line_responses,
            total=total,
            page=page,
            size=size,
            pages=pages
        )
    
    async def update_line(
        self,
        line_id: UUID,
        line_data: TransactionLineUpdate
    ) -> TransactionLineResponse:
        """Update a transaction line."""
        # Validate business rules for update
        await self._validate_line_update(line_id, line_data)
        
        # Recalculate totals if financial fields are being updated
        if any(field in line_data.model_dump(exclude_unset=True) 
               for field in ['quantity', 'unit_price', 'discount_percentage', 'discount_amount', 'tax_rate']):
            self._calculate_line_totals_update(line_data)
        
        line = await self.repository.update(line_id, line_data)
        if not line:
            raise NotFoundError(f"Transaction line with ID {line_id} not found")
        
        return TransactionLineResponse.model_validate(line)
    
    async def delete_line(self, line_id: UUID) -> bool:
        """Delete (soft delete) a transaction line."""
        line = await self.repository.get_by_id(line_id)
        if not line:
            raise NotFoundError(f"Transaction line with ID {line_id} not found")
        
        # Additional business logic validation could go here
        
        return await self.repository.delete(line_id)
    
    async def get_rental_lines_due(self, due_date: datetime) -> List[TransactionLineResponse]:
        """Get all rental lines that are due by a specific date."""
        lines = await self.repository.get_rental_lines_due(due_date)
        
        return [
            TransactionLineResponse.model_validate(line)
            for line in lines
        ]
    
    async def return_rental_item(
        self,
        line_id: UUID,
        returned_quantity: Decimal,
        return_date: Optional[datetime] = None
    ) -> TransactionLineResponse:
        """Process return of a rental item."""
        line = await self.repository.get_by_id(line_id)
        if not line:
            raise NotFoundError(f"Transaction line with ID {line_id} not found")
        
        if line.line_type != LineItemType.RENTAL:
            raise ValidationError("Can only return rental items")
        
        if returned_quantity <= 0:
            raise ValidationError("Returned quantity must be greater than zero")
        
        total_returned = line.returned_quantity + returned_quantity
        if total_returned > line.quantity:
            raise ValidationError("Cannot return more than originally rented")
        
        update_data = TransactionLineUpdate(
            returned_quantity=total_returned,
            return_date=(return_date or datetime.now()).date()
        )
        
        return await self.update_line(line_id, update_data)
    
    async def _validate_line_creation(self, line_data: TransactionLineCreate):
        """Validate business rules for line creation."""
        # Validate quantity
        if line_data.quantity <= 0:
            raise ValidationError("Quantity must be greater than zero")
        
        # Validate pricing
        if line_data.unit_price < 0:
            raise ValidationError("Unit price cannot be negative")
        
        if line_data.discount_percentage < 0 or line_data.discount_percentage > 100:
            raise ValidationError("Discount percentage must be between 0 and 100")
        
        if line_data.tax_rate < 0 or line_data.tax_rate > 100:
            raise ValidationError("Tax rate must be between 0 and 100")
        
        # Validate rental dates if applicable
        if line_data.line_type == LineItemType.RENTAL:
            if not line_data.rental_start_date or not line_data.rental_end_date:
                raise ValidationError("Rental items must have start and end dates")
            
            if line_data.rental_end_date <= line_data.rental_start_date:
                raise ValidationError("Rental end date must be after start date")
        
        # Validate returned quantity
        if line_data.returned_quantity > line_data.quantity:
            raise ValidationError("Returned quantity cannot exceed total quantity")
    
    async def _validate_line_update(self, line_id: UUID, line_data: TransactionLineUpdate):
        """Validate business rules for line update."""
        line = await self.repository.get_by_id(line_id)
        if not line:
            return
        
        # Validate updated quantities
        if line_data.quantity is not None and line_data.quantity <= 0:
            raise ValidationError("Quantity must be greater than zero")
        
        if line_data.returned_quantity is not None:
            quantity = line_data.quantity or line.quantity
            if line_data.returned_quantity > quantity:
                raise ValidationError("Returned quantity cannot exceed total quantity")
        
        # Validate rental dates if being updated
        if line_data.rental_start_date is not None or line_data.rental_end_date is not None:
            start_date = line_data.rental_start_date or line.rental_start_date
            end_date = line_data.rental_end_date or line.rental_end_date
            
            if start_date and end_date and end_date <= start_date:
                raise ValidationError("Rental end date must be after start date")
    
    def _calculate_line_totals(self, line_data: TransactionLineCreate):
        """Calculate line totals."""
        # Calculate discount amount if percentage is provided
        if line_data.discount_percentage > 0:
            line_data.discount_amount = (line_data.unit_price * line_data.quantity * 
                                       line_data.discount_percentage / 100)
        
        # Calculate subtotal after discount
        subtotal = (line_data.unit_price * line_data.quantity) - line_data.discount_amount
        
        # Calculate tax amount
        if line_data.tax_rate > 0:
            line_data.tax_amount = subtotal * line_data.tax_rate / 100
        
        # Calculate line total
        line_data.line_total = subtotal + line_data.tax_amount
    
    def _calculate_line_totals_update(self, line_data: TransactionLineUpdate):
        """Calculate line totals for update."""
        # Only recalculate if we have the necessary fields
        if (line_data.quantity is not None and 
            line_data.unit_price is not None):
            
            quantity = line_data.quantity
            unit_price = line_data.unit_price
            discount_percentage = line_data.discount_percentage or Decimal('0.00')
            tax_rate = line_data.tax_rate or Decimal('0.00')
            
            # Calculate discount amount if percentage is provided
            if discount_percentage > 0:
                line_data.discount_amount = (unit_price * quantity * 
                                           discount_percentage / 100)
            
            # Calculate subtotal after discount
            discount_amount = line_data.discount_amount or Decimal('0.00')
            subtotal = (unit_price * quantity) - discount_amount
            
            # Calculate tax amount
            if tax_rate > 0:
                line_data.tax_amount = subtotal * tax_rate / 100
            
            # Calculate line total
            tax_amount = line_data.tax_amount or Decimal('0.00')
            line_data.line_total = subtotal + tax_amount


class CombinedTransactionService:
    """Service for managing transactions with their lines."""
    
    def __init__(
        self, 
        header_repository: TransactionHeaderRepository,
        line_repository: TransactionLineRepository
    ):
        self.header_service = TransactionHeaderService(header_repository)
        self.line_service = TransactionLineService(line_repository)
    
    async def create_transaction_with_lines(
        self,
        transaction_data: TransactionCreateWithLines
    ) -> TransactionHeaderWithLines:
        """Create a complete transaction with its lines."""
        # Create the header first
        header = await self.header_service.create_transaction(transaction_data.header)
        
        # Create the lines
        lines = []
        for line_data in transaction_data.lines:
            line_data.transaction_id = header.id
            line = await self.line_service.create_line(line_data)
            lines.append(line)
        
        # Return combined response
        result = TransactionHeaderWithLines.model_validate(header)
        result.lines = lines
        
        return result
    
    async def get_transaction_with_lines(
        self,
        transaction_id: UUID
    ) -> TransactionHeaderWithLines:
        """Get a transaction with all its lines."""
        # Get the header
        header = await self.header_service.get_transaction(transaction_id)
        
        # Get the lines
        lines_response = await self.line_service.get_lines_by_transaction(transaction_id)
        
        # Combine and return
        result = TransactionHeaderWithLines.model_validate(header)
        result.lines = lines_response.items
        
        return result