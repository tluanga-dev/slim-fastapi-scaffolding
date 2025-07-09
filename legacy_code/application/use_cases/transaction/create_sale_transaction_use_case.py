"""
DEPRECATED: This use case is deprecated. Use RecordCompletedSaleUseCase instead.

This file is kept for backward compatibility only.
"""

from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from ....domain.entities.transaction_header import TransactionHeader
from .record_completed_sale_use_case import RecordCompletedSaleUseCase


class CreateSaleTransactionUseCase:
    """
    DEPRECATED: Use RecordCompletedSaleUseCase instead.

    This class is kept for backward compatibility and delegates to the new use case.
    """

    def __init__(
        self,
        transaction_repository,
        line_repository,
        item_repository,
        inventory_repository,
        stock_repository,
        customer_repository,
    ):
        """Initialize use case with repositories."""
        # Create the new use case
        self.new_use_case = RecordCompletedSaleUseCase(
            transaction_repository=transaction_repository,
            line_repository=line_repository,
            item_repository=item_repository,
            customer_repository=customer_repository,
            inventory_repository=inventory_repository,
            stock_repository=stock_repository,
        )

    async def execute(
        self,
        customer_id: UUID,
        location_id: UUID,
        items: List[Dict],
        sales_person_id: Optional[UUID] = None,
        discount_amount: Decimal = Decimal("0.00"),
        tax_rate: Decimal = Decimal("0.00"),
        notes: Optional[str] = None,
        auto_reserve: bool = True,
        created_by: Optional[str] = None,
    ) -> TransactionHeader:
        """
        DEPRECATED: Execute the use case to create a sale transaction.

        This method delegates to RecordCompletedSaleUseCase for backward compatibility.
        """
        # Use today's date as sale_date for legacy compatibility
        sale_date = date.today()

        # Delegate to the new use case
        return await self.new_use_case.execute(
            customer_id=customer_id,
            location_id=location_id,
            items=items,
            sale_date=sale_date,
            tax_rate=tax_rate,
            discount_amount=discount_amount,
            notes=notes,
            sales_person_id=sales_person_id,
            created_by=created_by,
        )
