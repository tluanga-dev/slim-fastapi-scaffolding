from typing import Optional, List, Dict
from datetime import datetime, date
from uuid import UUID

from ....domain.entities.transaction_header import TransactionHeader
from ....domain.entities.inventory_unit import InventoryUnit
from ....domain.entities.inspection_report import InspectionReport
from ....domain.value_objects.transaction_type import TransactionType, TransactionStatus
from ....domain.value_objects.item_type import InventoryStatus
from ....domain.value_objects.inspection_type import InspectionType, InspectionResult
from ....domain.repositories.transaction_header_repository import TransactionHeaderRepository
from ....domain.repositories.transaction_line_repository import TransactionLineRepository
from ....domain.repositories.inventory_unit_repository import InventoryUnitRepository
from ....domain.repositories.inspection_report_repository import InspectionReportRepository


class RentalPickupItem:
    """DTO for rental pickup inspection."""
    def __init__(
        self,
        inventory_unit_id: UUID,
        serial_number: str,
        condition_notes: Optional[str] = None,
        photos: Optional[List[str]] = None,
        accessories_included: Optional[List[str]] = None
    ):
        self.inventory_unit_id = inventory_unit_id
        self.serial_number = serial_number
        self.condition_notes = condition_notes
        self.photos = photos or []
        self.accessories_included = accessories_included or []


class ProcessRentalPickupUseCase:
    """Use case for processing rental pickup when customer collects items."""
    
    def __init__(
        self,
        transaction_repo: TransactionHeaderRepository,
        transaction_line_repo: TransactionLineRepository,
        inventory_unit_repo: InventoryUnitRepository,
        inspection_repo: InspectionReportRepository
    ):
        self.transaction_repo = transaction_repo
        self.transaction_line_repo = transaction_line_repo
        self.inventory_unit_repo = inventory_unit_repo
        self.inspection_repo = inspection_repo
    
    async def execute(
        self,
        transaction_id: UUID,
        pickup_items: List[RentalPickupItem],
        pickup_person_name: str,
        pickup_person_id: Optional[str] = None,
        pickup_notes: Optional[str] = None,
        processed_by: Optional[str] = None
    ) -> Dict:
        """Process rental pickup with pre-rental inspection."""
        
        # 1. Get and validate transaction
        transaction = await self.transaction_repo.get_by_id(transaction_id)
        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")
        
        if transaction.transaction_type != TransactionType.RENTAL:
            raise ValueError("This use case only processes rental transactions")
        
        # Validate status
        valid_statuses = [TransactionStatus.CONFIRMED, TransactionStatus.IN_PROGRESS]
        if transaction.status not in valid_statuses:
            raise ValueError(
                f"Cannot process pickup for transaction in {transaction.status.value} status"
            )
        
        # Check if rental period has started
        if transaction.rental_start_date > date.today():
            raise ValueError(
                f"Rental period starts on {transaction.rental_start_date}. "
                f"Cannot pickup before start date."
            )
        
        # 2. Validate all pickup items
        validated_items = []
        for item in pickup_items:
            unit = await self.inventory_unit_repo.get_by_id(item.inventory_unit_id)
            if not unit:
                raise ValueError(f"Inventory unit {item.inventory_unit_id} not found")
            
            # Verify serial number matches
            if unit.serial_number != item.serial_number:
                raise ValueError(
                    f"Serial number mismatch for unit {item.inventory_unit_id}. "
                    f"Expected: {unit.serial_number}, Provided: {item.serial_number}"
                )
            
            # Verify unit is reserved for this transaction
            if unit.current_status not in [InventoryStatus.RESERVED_RENT, InventoryStatus.RENTED]:
                raise ValueError(
                    f"Unit {unit.serial_number} is not reserved for rental. "
                    f"Current status: {unit.current_status.value}"
                )
            
            validated_items.append((item, unit))
        
        # 3. Create pre-rental inspection reports
        inspection_reports = []
        for pickup_item, unit in validated_items:
            inspection = InspectionReport(
                entity_type="InventoryUnit",
                entity_id=unit.id,
                inspection_type=InspectionType.PRE_RENTAL,
                inspection_date=datetime.utcnow(),
                inspector_id=processed_by,
                condition_grade=unit.condition_grade,
                inspection_result=InspectionResult.PASS,
                notes=pickup_item.condition_notes,
                photos=pickup_item.photos,
                metadata={
                    "transaction_id": str(transaction_id),
                    "serial_number": unit.serial_number,
                    "accessories": pickup_item.accessories_included
                },
                created_by=processed_by
            )
            
            # Save inspection report
            inspection = await self.inspection_repo.create(inspection)
            inspection_reports.append(inspection)
            
            # Update inventory unit status
            unit.current_status = InventoryStatus.RENTED
            unit.notes = (unit.notes or "") + (
                f"\n[PICKUP] {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} - "
                f"Picked up by {pickup_person_name}"
            )
            await self.inventory_unit_repo.update(unit.id, unit)
        
        # 4. Update transaction status if needed
        if transaction.status == TransactionStatus.CONFIRMED:
            transaction.update_status(TransactionStatus.IN_PROGRESS, processed_by)
        
        # 5. Add pickup notes to transaction
        pickup_note = (
            f"\n[PICKUP] {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} - "
            f"Items picked up by {pickup_person_name}"
        )
        if pickup_person_id:
            pickup_note += f" (ID: {pickup_person_id})"
        if pickup_notes:
            pickup_note += f"\nNotes: {pickup_notes}"
        
        transaction.notes = (transaction.notes or "") + pickup_note
        
        # 6. Save transaction
        await self.transaction_repo.update(transaction.id, transaction)
        
        return {
            "transaction": transaction,
            "inspection_reports": inspection_reports,
            "pickup_summary": {
                "pickup_date": datetime.utcnow(),
                "pickup_person": pickup_person_name,
                "items_count": len(validated_items),
                "items": [
                    {
                        "unit_id": str(unit.id),
                        "serial_number": unit.serial_number,
                        "condition": unit.condition_grade.value,
                        "inspection_id": str(report.id)
                    }
                    for (_, unit), report in zip(validated_items, inspection_reports)
                ]
            }
        }