"""
DEPRECATED: This use case is no longer needed in the new purchase flow.

In the new flow, purchases are recorded as already completed, so inventory 
is created immediately when recording the purchase. There is no separate 
goods receipt process.

This file is kept for backward compatibility only and will raise an error 
if used.
"""

from typing import List, Dict, Optional
from datetime import datetime
from decimal import Decimal
from uuid import UUID


class ReceiveGoodsUseCase:
    """
    DEPRECATED: Use case for receiving goods from a purchase order.

    This class is no longer needed in the new purchase flow and will raise
    an error if used.
    """

    def __init__(self, *args, **kwargs):
        """Initialize use case with repositories."""
        pass

    async def execute(
        self,
        transaction_id: UUID,
        received_items: List[Dict],
        receipt_date: datetime = None,
        notes: Optional[str] = None,
        received_by: Optional[str] = None,
    ):
        """
        DEPRECATED: Execute the use case to receive goods for a purchase order.

        This method is no longer supported in the new purchase flow.
        """
        raise NotImplementedError(
            "ReceiveGoodsUseCase is deprecated. In the new purchase flow, "
            "inventory is created immediately when recording a completed purchase. "
            "Use RecordCompletedPurchaseUseCase instead."
        )
