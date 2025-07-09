from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict
from uuid import UUID

from ....domain.entities.rental_return import RentalReturn
from ....domain.repositories.rental_return_repository import RentalReturnRepository
from ....domain.repositories.transaction_header_repository import TransactionHeaderRepository
from ....domain.value_objects.rental_return_type import ReturnStatus


class ReleaseDepositUseCase:
    """Use case for releasing security deposits after rental returns."""
    
    def __init__(
        self,
        return_repository: RentalReturnRepository,
        transaction_repository: TransactionHeaderRepository
    ):
        """Initialize use case with repositories."""
        self.return_repository = return_repository
        self.transaction_repository = transaction_repository
    
    async def execute(
        self,
        return_id: UUID,
        processed_by: str,
        override_amount: Optional[Decimal] = None,
        release_notes: Optional[str] = None
    ) -> Dict:
        """Execute the release deposit use case."""
        
        # 1. Get the rental return
        rental_return = await self.return_repository.get_by_id(return_id)
        if not rental_return:
            raise ValueError(f"Rental return {return_id} not found")
        
        # 2. Validate return is completed
        if rental_return.return_status != ReturnStatus.COMPLETED:
            raise ValueError("Can only release deposit for completed returns")
        
        # 3. Get rental transaction to find original deposit
        rental_transaction = await self.transaction_repository.get_by_id(rental_return.rental_transaction_id)
        if not rental_transaction:
            raise ValueError("Rental transaction not found")
        
        # 4. Calculate deposit release amount
        deposit_calculation = await self._calculate_deposit_release(
            rental_return,
            rental_transaction,
            override_amount
        )
        
        # 5. Validate deposit release
        if deposit_calculation["release_amount"] < 0:
            raise ValueError("Release amount cannot be negative")
        
        if deposit_calculation["release_amount"] > deposit_calculation["original_deposit"]:
            raise ValueError("Release amount cannot exceed original deposit")
        
        # 6. Process deposit release
        release_result = await self._process_deposit_release(
            rental_return,
            rental_transaction,
            deposit_calculation,
            processed_by,
            release_notes
        )
        
        # 7. Update rental return with deposit release information
        rental_return.record_deposit_release(
            release_amount=deposit_calculation["release_amount"],
            withheld_amount=deposit_calculation["withheld_amount"],
            release_date=datetime.utcnow(),
            processed_by=processed_by,
            notes=release_notes
        )
        
        await self.return_repository.update(rental_return)
        
        return release_result
    
    async def _calculate_deposit_release(
        self,
        rental_return: RentalReturn,
        rental_transaction,
        override_amount: Optional[Decimal] = None
    ) -> Dict:
        """Calculate how much deposit should be released."""
        
        # Get original deposit amount
        original_deposit = rental_transaction.deposit_amount or Decimal("0.00")
        
        if override_amount is not None:
            # Manual override
            withheld_amount = original_deposit - override_amount
            return {
                "original_deposit": original_deposit,
                "release_amount": override_amount,
                "withheld_amount": withheld_amount,
                "calculation_method": "manual_override",
                "fee_breakdown": {}
            }
        
        # Calculate total fees to withhold
        late_fee = rental_return.total_late_fee or Decimal("0.00")
        damage_fee = rental_return.total_damage_fee or Decimal("0.00")
        cleaning_fee = rental_return.total_cleaning_fee or Decimal("0.00")
        replacement_fee = rental_return.total_replacement_fee or Decimal("0.00")
        
        total_fees = late_fee + damage_fee + cleaning_fee + replacement_fee
        
        # Calculate release amount
        release_amount = max(Decimal("0.00"), original_deposit - total_fees)
        withheld_amount = original_deposit - release_amount
        
        fee_breakdown = {
            "late_fee": float(late_fee),
            "damage_fee": float(damage_fee),
            "cleaning_fee": float(cleaning_fee),
            "replacement_fee": float(replacement_fee),
            "total_fees": float(total_fees)
        }
        
        return {
            "original_deposit": original_deposit,
            "release_amount": release_amount,
            "withheld_amount": withheld_amount,
            "calculation_method": "automatic",
            "fee_breakdown": fee_breakdown
        }
    
    async def _process_deposit_release(
        self,
        rental_return: RentalReturn,
        rental_transaction,
        deposit_calculation: Dict,
        processed_by: str,
        release_notes: Optional[str]
    ) -> Dict:
        """Process the actual deposit release."""
        
        # In a real system, this would integrate with payment processing
        # For now, we'll just simulate the release
        
        release_amount = deposit_calculation["release_amount"]
        
        # Simulate payment processing
        if release_amount > 0:
            # Would integrate with payment gateway here
            payment_result = {
                "status": "success",
                "transaction_id": f"dep_release_{rental_return.id}_{int(datetime.utcnow().timestamp())}",
                "amount": float(release_amount),
                "currency": "USD",
                "processed_at": datetime.utcnow().isoformat(),
                "method": "refund_to_original_payment"
            }
        else:
            payment_result = {
                "status": "no_refund",
                "reason": "Full deposit withheld for fees",
                "amount": 0.00
            }
        
        # Create release record
        release_record = {
            "return_id": str(rental_return.id),
            "transaction_id": str(rental_transaction.id),
            "customer_id": str(rental_transaction.customer_id),
            "original_deposit": float(deposit_calculation["original_deposit"]),
            "release_amount": float(release_amount),
            "withheld_amount": float(deposit_calculation["withheld_amount"]),
            "calculation_method": deposit_calculation["calculation_method"],
            "fee_breakdown": deposit_calculation["fee_breakdown"],
            "payment_result": payment_result,
            "processed_by": processed_by,
            "processed_at": datetime.utcnow().isoformat(),
            "notes": release_notes
        }
        
        return release_record
    
    async def calculate_deposit_preview(
        self,
        return_id: UUID,
        include_projections: bool = False
    ) -> Dict:
        """Calculate deposit release preview without processing."""
        
        # 1. Get the rental return
        rental_return = await self.return_repository.get_by_id(return_id)
        if not rental_return:
            raise ValueError(f"Rental return {return_id} not found")
        
        # 2. Get rental transaction
        rental_transaction = await self.transaction_repository.get_by_id(rental_return.rental_transaction_id)
        if not rental_transaction:
            raise ValueError("Rental transaction not found")
        
        # 3. Calculate current deposit release
        current_calculation = await self._calculate_deposit_release(
            rental_return,
            rental_transaction,
            None
        )
        
        preview = {
            "return_id": str(return_id),
            "return_status": rental_return.return_status.value,
            "can_release_deposit": rental_return.return_status == ReturnStatus.COMPLETED,
            "deposit_calculation": current_calculation
        }
        
        # 4. Add projections if requested
        if include_projections:
            # Project different scenarios
            scenarios = []
            
            # Scenario 1: No additional fees
            no_fees_calc = await self._calculate_deposit_release(
                rental_return,
                rental_transaction,
                None
            )
            scenarios.append({
                "name": "Current Fees",
                "description": "Based on current assessed fees",
                "calculation": no_fees_calc
            })
            
            # Scenario 2: Additional damage fee
            if rental_return.total_damage_fee == 0:
                # Simulate additional damage fee
                temp_return = rental_return
                temp_return._total_damage_fee = Decimal("100.00")
                damage_calc = await self._calculate_deposit_release(
                    temp_return,
                    rental_transaction,
                    None
                )
                scenarios.append({
                    "name": "With Damage Fee",
                    "description": "If $100 damage fee is assessed",
                    "calculation": damage_calc
                })
            
            preview["scenarios"] = scenarios
        
        return preview
    
    async def get_deposit_release_history(
        self,
        transaction_id: Optional[UUID] = None,
        customer_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get history of deposit releases."""
        
        # This would query a deposit release history table
        # For now, we'll return a simplified version
        
        filters = []
        if transaction_id:
            filters.append(f"transaction_id = {transaction_id}")
        if customer_id:
            filters.append(f"customer_id = {customer_id}")
        if start_date:
            filters.append(f"processed_at >= {start_date}")
        if end_date:
            filters.append(f"processed_at <= {end_date}")
        
        # In a real implementation, this would query the database
        # For now, return empty list
        return []
    
    async def reverse_deposit_release(
        self,
        return_id: UUID,
        reason: str,
        processed_by: str
    ) -> Dict:
        """Reverse a deposit release (for corrections)."""
        
        # 1. Get the rental return
        rental_return = await self.return_repository.get_by_id(return_id)
        if not rental_return:
            raise ValueError(f"Rental return {return_id} not found")
        
        # 2. Validate deposit was released
        if not rental_return.deposit_released:
            raise ValueError("No deposit release to reverse")
        
        # 3. Process reversal
        reversal_record = {
            "return_id": str(return_id),
            "original_release_amount": float(rental_return.deposit_release_amount or 0),
            "reversal_reason": reason,
            "processed_by": processed_by,
            "processed_at": datetime.utcnow().isoformat(),
            "status": "reversed"
        }
        
        # 4. Update rental return to remove deposit release
        rental_return.reverse_deposit_release(processed_by, reason)
        await self.return_repository.update(rental_return)
        
        return reversal_record