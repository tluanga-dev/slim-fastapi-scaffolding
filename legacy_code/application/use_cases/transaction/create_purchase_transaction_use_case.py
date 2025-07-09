"""
DEPRECATED: This use case is deprecated. Use RecordCompletedPurchaseUseCase instead.

This file is kept for backward compatibility only.
"""

from typing import List, Optional, Dict
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID

from ....domain.entities.transaction_header import TransactionHeader
from .record_completed_purchase_use_case import RecordCompletedPurchaseUseCase


class CreatePurchaseTransactionUseCase:
    """
    DEPRECATED: Use RecordCompletedPurchaseUseCase instead.

    This class is kept for backward compatibility and delegates to the new use case.
    """

    def __init__(
        self,
        transaction_repository,
        line_repository,
        item_repository,
        customer_repository,
        inventory_repository=None,
        stock_repository=None,
    ):
        """Initialize use case with repositories."""
        # Create the new use case
        self.new_use_case = RecordCompletedPurchaseUseCase(
            transaction_repository=transaction_repository,
            line_repository=line_repository,
            item_repository=item_repository,
            customer_repository=customer_repository,
            inventory_repository=inventory_repository,
            stock_repository=stock_repository,
        )

    async def execute(
        self,
        supplier_id: UUID,
        location_id: UUID,
        items: List[Dict],
        expected_delivery_date: Optional[date] = None,
        tax_rate: Decimal = Decimal("0.00"),
        notes: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> TransactionHeader:
        """
        DEPRECATED: Execute the use case to create a purchase transaction.

        This method delegates to RecordCompletedPurchaseUseCase for backward compatibility.
        """
        # Convert expected_delivery_date to purchase_date for new use case
        purchase_date = expected_delivery_date or date.today()

        # Delegate to the new use case
        return await self.new_use_case.execute(
            supplier_id=supplier_id,
            location_id=location_id,
            items=items,
            purchase_date=purchase_date,
            tax_rate=tax_rate,
            notes=notes,
            created_by=created_by,
        )
