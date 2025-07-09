from datetime import date
from decimal import Decimal
from typing import Dict, Optional
from uuid import UUID

from ....domain.entities.rental_return import RentalReturn
from ....domain.repositories.rental_return_repository import RentalReturnRepository
from ....domain.repositories.rental_return_line_repository import RentalReturnLineRepository
from ....domain.repositories.transaction_header_repository import TransactionHeaderRepository
from ....domain.repositories.item_repository import ItemRepository


class CalculateLateFeeUseCase:
    """Use case for calculating late fees for rental returns."""
    
    def __init__(
        self,
        return_repository: RentalReturnRepository,
        line_repository: RentalReturnLineRepository,
        transaction_repository: TransactionHeaderRepository,
        item_repository: ItemRepository
    ):
        """Initialize use case with repositories."""
        self.return_repository = return_repository
        self.line_repository = line_repository
        self.transaction_repository = transaction_repository
        self.item_repository = item_repository
    
    async def execute(
        self,
        return_id: UUID,
        daily_late_fee_rate: Optional[Decimal] = None,
        use_percentage_of_rental_rate: bool = True,
        percentage_rate: Decimal = Decimal("0.10"),  # 10% of daily rental rate
        updated_by: Optional[str] = None
    ) -> Dict:
        """Execute the calculate late fee use case."""
        
        # 1. Get the rental return
        rental_return = await self.return_repository.get_by_id(return_id)
        if not rental_return:
            raise ValueError(f"Rental return {return_id} not found")
        
        # 2. Check if return is actually late
        if not rental_return.is_late():
            return {
                "return_id": str(return_id),
                "is_late": False,
                "days_late": 0,
                "total_late_fee": 0.00,
                "line_fees": []
            }
        
        # 3. Get rental transaction details
        rental_transaction = await self.transaction_repository.get_by_id(rental_return.rental_transaction_id)
        if not rental_transaction:
            raise ValueError("Rental transaction not found")
        
        # 4. Calculate days late
        days_late = rental_return.days_late()
        
        # 5. Get return lines
        return_lines = await self.line_repository.get_by_return_id(return_id)
        if not return_lines:
            raise ValueError("No return lines found")
        
        # 6. Calculate late fees for each line
        line_fees = []
        total_late_fee = Decimal("0.00")
        
        for line in return_lines:
            if line.returned_quantity == 0:
                continue
            
            # Get SKU information to determine rental rate
            from ....domain.repositories.inventory_unit_repository import InventoryUnitRepository
            # For now, we'll use a default rate if not provided
            line_daily_rate = daily_late_fee_rate
            
            if line_daily_rate is None and use_percentage_of_rental_rate:
                # We need to get the SKU to calculate percentage of rental rate
                # This would require additional repository injection
                # For now, use a default rate
                line_daily_rate = Decimal("5.00")  # Default $5/day late fee
            
            if line_daily_rate is None:
                line_daily_rate = Decimal("5.00")  # Fallback default
            
            # Calculate late fee for this line
            line_late_fee = line.returned_quantity * line_daily_rate * days_late
            
            # Update the line with late fee
            line.set_late_fee(line_late_fee, updated_by)
            await self.line_repository.update(line)
            
            total_late_fee += line_late_fee
            
            line_fees.append({
                "line_id": str(line.id),
                "inventory_unit_id": str(line.inventory_unit_id),
                "returned_quantity": line.returned_quantity,
                "daily_rate": float(line_daily_rate),
                "days_late": days_late,
                "late_fee": float(line_late_fee)
            })
        
        # 7. Update rental return with total late fee
        rental_return._total_late_fee = total_late_fee
        await self.return_repository.update(rental_return)
        
        return {
            "return_id": str(return_id),
            "is_late": True,
            "days_late": days_late,
            "expected_return_date": rental_return.expected_return_date.isoformat() if rental_return.expected_return_date else None,
            "actual_return_date": rental_return.return_date.isoformat(),
            "total_late_fee": float(total_late_fee),
            "line_fees": line_fees
        }
    
    async def calculate_projected_late_fee(
        self,
        return_id: UUID,
        projected_return_date: date,
        daily_late_fee_rate: Optional[Decimal] = None
    ) -> Dict:
        """Calculate projected late fee for a future return date."""
        
        # 1. Get the rental return
        rental_return = await self.return_repository.get_by_id(return_id)
        if not rental_return:
            raise ValueError(f"Rental return {return_id} not found")
        
        # 2. Check if projected date would be late
        if not rental_return.expected_return_date or projected_return_date <= rental_return.expected_return_date:
            return {
                "return_id": str(return_id),
                "projected_return_date": projected_return_date.isoformat(),
                "would_be_late": False,
                "projected_days_late": 0,
                "projected_late_fee": 0.00
            }
        
        # 3. Calculate projected days late
        projected_days_late = (projected_return_date - rental_return.expected_return_date).days
        
        # 4. Get return lines
        return_lines = await self.line_repository.get_by_return_id(return_id)
        if not return_lines:
            return {
                "return_id": str(return_id),
                "projected_return_date": projected_return_date.isoformat(),
                "would_be_late": True,
                "projected_days_late": projected_days_late,
                "projected_late_fee": 0.00
            }
        
        # 5. Calculate projected fees
        line_daily_rate = daily_late_fee_rate or Decimal("5.00")
        total_projected_fee = Decimal("0.00")
        
        for line in return_lines:
            if line.returned_quantity > 0:
                line_projected_fee = line.returned_quantity * line_daily_rate * projected_days_late
                total_projected_fee += line_projected_fee
        
        return {
            "return_id": str(return_id),
            "projected_return_date": projected_return_date.isoformat(),
            "expected_return_date": rental_return.expected_return_date.isoformat(),
            "would_be_late": True,
            "projected_days_late": projected_days_late,
            "projected_late_fee": float(total_projected_fee),
            "daily_rate_used": float(line_daily_rate)
        }