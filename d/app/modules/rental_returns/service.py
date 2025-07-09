from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal

from app.modules.rental_returns.repository import RentalReturnRepository
from app.modules.rental_returns.schemas import (
    RentalReturnCreate, RentalReturnUpdate, RentalReturnStatusUpdate, RentalReturnFinancialUpdate,
    RentalReturnLineCreate, RentalReturnLineUpdate, RentalReturnLineProcessing,
    RentalReturnResponse, RentalReturnWithLines, RentalReturnListResponse,
    RentalReturnLineResponse, RentalReturnLineSummary,
    RentalReturnSearchRequest, RentalReturnLineSearchRequest,
    RentalReturnBulkStatusUpdate, RentalReturnLineBulkProcessing,
    RentalReturnMetrics, RentalReturnAnalytics, RentalReturnEstimate
)
from app.core.domain.entities.rental_return import RentalReturn as RentalReturnEntity
from app.core.domain.entities.rental_return_line import RentalReturnLine as RentalReturnLineEntity
from app.core.domain.value_objects.rental_return_type import ReturnStatus, ReturnType, DamageLevel
from app.core.domain.value_objects.item_type import ConditionGrade
from app.core.errors import NotFoundError, ValidationError
from app.modules.rental_returns.models import RentalReturnModel, RentalReturnLineModel


class RentalReturnService:
    """Service layer for rental return business logic."""
    
    def __init__(self, repository: RentalReturnRepository):
        self.repository = repository
    
    def _return_model_to_entity(self, model: RentalReturnModel) -> RentalReturnEntity:
        """Convert SQLAlchemy model to domain entity."""
        return model.to_entity()
    
    def _return_entity_to_dict(self, entity: RentalReturnEntity) -> dict:
        """Convert domain entity to dictionary for database operations."""
        return {
            'id': entity.id,
            'rental_transaction_id': entity.rental_transaction_id,
            'return_date': entity.return_date,
            'return_type': entity.return_type.value,
            'return_status': entity.return_status.value,
            'return_location_id': entity.return_location_id,
            'expected_return_date': entity.expected_return_date,
            'processed_by': entity.processed_by,
            'notes': entity.notes,
            'total_late_fee': float(entity.total_late_fee),
            'total_damage_fee': float(entity.total_damage_fee),
            'total_deposit_release': float(entity.total_deposit_release),
            'total_refund_amount': float(entity.total_refund_amount),
            'created_at': entity.created_at,
            'updated_at': entity.updated_at,
            'created_by': entity.created_by,
            'updated_by': entity.updated_by,
            'is_active': entity.is_active
        }
    
    def _line_model_to_entity(self, model: RentalReturnLineModel) -> RentalReturnLineEntity:
        """Convert SQLAlchemy model to domain entity."""
        return model.to_entity()
    
    def _line_entity_to_dict(self, entity: RentalReturnLineEntity) -> dict:
        """Convert domain entity to dictionary for database operations."""
        return {
            'id': entity.id,
            'return_id': entity.return_id,
            'inventory_unit_id': entity.inventory_unit_id,
            'original_quantity': entity.original_quantity,
            'returned_quantity': entity.returned_quantity,
            'condition_grade': entity.condition_grade.value,
            'damage_level': entity.damage_level.value,
            'late_fee': float(entity.late_fee),
            'damage_fee': float(entity.damage_fee),
            'cleaning_fee': float(entity.cleaning_fee),
            'replacement_fee': float(entity.replacement_fee),
            'is_processed': entity.is_processed,
            'processed_at': entity.processed_at,
            'processed_by': entity.processed_by,
            'notes': entity.notes,
            'created_at': entity.created_at,
            'updated_at': entity.updated_at,
            'created_by': entity.created_by,
            'updated_by': entity.updated_by,
            'is_active': entity.is_active
        }
    
    # Rental Return Operations
    async def create_rental_return(self, return_data: RentalReturnCreate, created_by: Optional[str] = None) -> RentalReturnWithLines:
        """Create a new rental return with lines."""
        # Create domain entity to validate business rules
        try:
            entity = RentalReturnEntity(
                rental_transaction_id=return_data.rental_transaction_id,
                return_date=return_data.return_date,
                return_type=return_data.return_type,
                return_location_id=return_data.return_location_id,
                expected_return_date=return_data.expected_return_date,
                notes=return_data.notes,
                created_by=created_by
            )
        except ValueError as e:
            raise ValidationError(str(e))
        
        # Convert to dict for database creation
        create_data = self._return_entity_to_dict(entity)
        
        # Create in database
        return_model = await self.repository.create_rental_return(create_data)
        
        # Create return lines
        line_models = []
        for line_data in return_data.lines:
            try:
                line_entity = RentalReturnLineEntity(
                    return_id=return_model.id,
                    inventory_unit_id=line_data.inventory_unit_id,
                    original_quantity=line_data.original_quantity,
                    returned_quantity=line_data.returned_quantity,
                    condition_grade=line_data.condition_grade,
                    damage_level=line_data.damage_level,
                    late_fee=line_data.late_fee or Decimal('0.00'),
                    damage_fee=line_data.damage_fee or Decimal('0.00'),
                    cleaning_fee=line_data.cleaning_fee or Decimal('0.00'),
                    replacement_fee=line_data.replacement_fee or Decimal('0.00'),
                    notes=line_data.notes,
                    created_by=created_by
                )
            except ValueError as e:
                raise ValidationError(f"Invalid return line: {str(e)}")
            
            line_create_data = self._line_entity_to_dict(line_entity)
            line_model = await self.repository.create_rental_return_line(line_create_data)
            line_models.append(line_model)
        
        # Update totals
        await self._update_return_totals(return_model.id)
        
        # Get the updated return with lines
        updated_return = await self.repository.get_rental_return_by_id(return_model.id)
        
        return RentalReturnWithLines(
            **RentalReturnResponse.model_validate(updated_return).model_dump(),
            lines=[RentalReturnLineResponse.model_validate(line) for line in updated_return.lines]
        )
    
    async def get_rental_return_by_id(self, return_id: UUID, include_lines: bool = False) -> RentalReturnResponse | RentalReturnWithLines:
        """Get rental return by ID."""
        rental_return = await self.repository.get_rental_return_by_id(return_id)
        if not rental_return:
            raise NotFoundError(f"Rental return with ID {return_id} not found")
        
        if include_lines:
            return RentalReturnWithLines(
                **RentalReturnResponse.model_validate(rental_return).model_dump(),
                lines=[RentalReturnLineResponse.model_validate(line) for line in rental_return.lines]
            )
        else:
            return RentalReturnResponse.model_validate(rental_return)
    
    async def get_rental_returns_by_transaction(self, transaction_id: UUID) -> List[RentalReturnListResponse]:
        """Get all rental returns for a transaction."""
        returns = await self.repository.get_rental_returns_by_transaction(transaction_id)
        return [RentalReturnListResponse.model_validate(ret) for ret in returns]
    
    async def search_rental_returns(self, search_request: RentalReturnSearchRequest) -> List[RentalReturnListResponse]:
        """Search rental returns with filtering."""
        returns = await self.repository.get_rental_returns(
            skip=search_request.offset,
            limit=search_request.limit,
            rental_transaction_id=search_request.rental_transaction_id,
            return_location_id=search_request.return_location_id,
            return_status=search_request.return_status,
            return_type=search_request.return_type,
            return_date_from=search_request.return_date_from,
            return_date_to=search_request.return_date_to,
            processed_by=search_request.processed_by,
            is_active=search_request.is_active
        )
        
        return [RentalReturnListResponse.model_validate(ret) for ret in returns]
    
    async def update_rental_return(self, return_id: UUID, update_data: RentalReturnUpdate, updated_by: Optional[str] = None) -> RentalReturnResponse:
        """Update rental return information."""
        rental_return = await self.repository.get_rental_return_by_id(return_id)
        if not rental_return:
            raise NotFoundError(f"Rental return with ID {return_id} not found")
        
        # Convert to domain entity for validation
        entity = self._return_model_to_entity(rental_return)
        
        # Update entity using domain methods
        try:
            if update_data.return_date is not None:
                entity.return_date = update_data.return_date
                entity.update_timestamp(updated_by)
            
            if update_data.return_type is not None:
                entity.return_type = update_data.return_type
                entity.update_timestamp(updated_by)
            
            if update_data.return_location_id is not None:
                entity.update_return_location(update_data.return_location_id, updated_by)
            
            if update_data.expected_return_date is not None:
                entity.update_expected_return_date(update_data.expected_return_date, updated_by)
            
            if update_data.notes is not None:
                entity.update_notes(update_data.notes, updated_by)
                
        except ValueError as e:
            raise ValidationError(str(e))
        
        # Prepare update data for database
        update_dict = {}
        if update_data.return_date is not None:
            update_dict['return_date'] = entity.return_date
        if update_data.return_type is not None:
            update_dict['return_type'] = entity.return_type.value
        if update_data.return_location_id is not None:
            update_dict['return_location_id'] = entity.return_location_id
        if update_data.expected_return_date is not None:
            update_dict['expected_return_date'] = entity.expected_return_date
        if update_data.notes is not None:
            update_dict['notes'] = entity.notes
        
        update_dict['updated_at'] = entity.updated_at
        if updated_by:
            update_dict['updated_by'] = entity.updated_by
        
        # Update in database
        updated_return = await self.repository.update_rental_return(return_id, update_dict)
        
        return RentalReturnResponse.model_validate(updated_return)
    
    async def update_rental_return_status(self, return_id: UUID, status_data: RentalReturnStatusUpdate, updated_by: Optional[str] = None) -> RentalReturnResponse:
        """Update rental return status."""
        rental_return = await self.repository.get_rental_return_by_id(return_id)
        if not rental_return:
            raise NotFoundError(f"Rental return with ID {return_id} not found")
        
        entity = self._return_model_to_entity(rental_return)
        
        try:
            entity.update_return_status(status_data.return_status, updated_by)
        except ValueError as e:
            raise ValidationError(str(e))
        
        update_dict = {
            'return_status': entity.return_status.value,
            'processed_by': entity.processed_by,
            'updated_at': entity.updated_at,
            'updated_by': entity.updated_by
        }
        
        updated_return = await self.repository.update_rental_return(return_id, update_dict)
        return RentalReturnResponse.model_validate(updated_return)
    
    async def update_rental_return_financials(self, return_id: UUID, financial_data: RentalReturnFinancialUpdate, updated_by: Optional[str] = None) -> RentalReturnResponse:
        """Update rental return financial information."""
        rental_return = await self.repository.get_rental_return_by_id(return_id)
        if not rental_return:
            raise NotFoundError(f"Rental return with ID {return_id} not found")
        
        entity = self._return_model_to_entity(rental_return)
        
        try:
            if financial_data.total_deposit_release is not None:
                entity.update_deposit_release(financial_data.total_deposit_release, updated_by)
            
            if financial_data.total_refund_amount is not None:
                entity.update_refund_amount(financial_data.total_refund_amount, updated_by)
        except ValueError as e:
            raise ValidationError(str(e))
        
        update_dict = {
            'total_deposit_release': float(entity.total_deposit_release),
            'total_refund_amount': float(entity.total_refund_amount),
            'updated_at': entity.updated_at,
            'updated_by': entity.updated_by
        }
        
        updated_return = await self.repository.update_rental_return(return_id, update_dict)
        return RentalReturnResponse.model_validate(updated_return)
    
    # Rental Return Line Operations
    async def get_rental_return_line_by_id(self, line_id: UUID) -> RentalReturnLineResponse:
        """Get rental return line by ID."""
        return_line = await self.repository.get_rental_return_line_by_id(line_id)
        if not return_line:
            raise NotFoundError(f"Rental return line with ID {line_id} not found")
        
        return RentalReturnLineResponse.model_validate(return_line)
    
    async def get_rental_return_lines_by_return(self, return_id: UUID) -> List[RentalReturnLineResponse]:
        """Get all lines for a rental return."""
        lines = await self.repository.get_rental_return_lines_by_return(return_id)
        return [RentalReturnLineResponse.model_validate(line) for line in lines]
    
    async def search_rental_return_lines(self, search_request: RentalReturnLineSearchRequest) -> List[RentalReturnLineResponse]:
        """Search rental return lines with filtering."""
        lines = await self.repository.get_rental_return_lines(
            skip=search_request.offset,
            limit=search_request.limit,
            return_id=search_request.return_id,
            inventory_unit_id=search_request.inventory_unit_id,
            condition_grade=search_request.condition_grade,
            damage_level=search_request.damage_level,
            is_processed=search_request.is_processed,
            processed_by=search_request.processed_by,
            is_active=search_request.is_active
        )
        
        return [RentalReturnLineResponse.model_validate(line) for line in lines]
    
    async def update_rental_return_line(self, line_id: UUID, update_data: RentalReturnLineUpdate, updated_by: Optional[str] = None) -> RentalReturnLineResponse:
        """Update rental return line."""
        return_line = await self.repository.get_rental_return_line_by_id(line_id)
        if not return_line:
            raise NotFoundError(f"Rental return line with ID {line_id} not found")
        
        entity = self._line_model_to_entity(return_line)
        
        try:
            if update_data.returned_quantity is not None:
                entity.update_returned_quantity(update_data.returned_quantity, updated_by)
            
            if update_data.condition_grade is not None:
                entity.update_condition(update_data.condition_grade, updated_by)
            
            if update_data.damage_level is not None:
                entity.update_damage_level(update_data.damage_level, updated_by)
            
            if any([
                update_data.late_fee is not None,
                update_data.damage_fee is not None,
                update_data.cleaning_fee is not None,
                update_data.replacement_fee is not None
            ]):
                entity.update_fees(
                    late_fee=update_data.late_fee,
                    damage_fee=update_data.damage_fee,
                    cleaning_fee=update_data.cleaning_fee,
                    replacement_fee=update_data.replacement_fee,
                    updated_by=updated_by
                )
            
            if update_data.notes is not None:
                entity.update_notes(update_data.notes, updated_by)
                
        except ValueError as e:
            raise ValidationError(str(e))
        
        # Prepare update data for database
        update_dict = {}
        if update_data.returned_quantity is not None:
            update_dict['returned_quantity'] = entity.returned_quantity
        if update_data.condition_grade is not None:
            update_dict['condition_grade'] = entity.condition_grade.value
        if update_data.damage_level is not None:
            update_dict['damage_level'] = entity.damage_level.value
        if update_data.late_fee is not None:
            update_dict['late_fee'] = float(entity.late_fee)
        if update_data.damage_fee is not None:
            update_dict['damage_fee'] = float(entity.damage_fee)
        if update_data.cleaning_fee is not None:
            update_dict['cleaning_fee'] = float(entity.cleaning_fee)
        if update_data.replacement_fee is not None:
            update_dict['replacement_fee'] = float(entity.replacement_fee)
        if update_data.notes is not None:
            update_dict['notes'] = entity.notes
        
        update_dict['updated_at'] = entity.updated_at
        if updated_by:
            update_dict['updated_by'] = entity.updated_by
        
        # Update in database
        updated_line = await self.repository.update_rental_return_line(line_id, update_dict)
        
        # Update return totals
        await self._update_return_totals(updated_line.return_id)
        
        return RentalReturnLineResponse.model_validate(updated_line)
    
    async def process_rental_return_line(self, line_id: UUID, processing_data: RentalReturnLineProcessing) -> RentalReturnLineResponse:
        """Process a rental return line."""
        return_line = await self.repository.get_rental_return_line_by_id(line_id)
        if not return_line:
            raise NotFoundError(f"Rental return line with ID {line_id} not found")
        
        entity = self._line_model_to_entity(return_line)
        
        try:
            entity.mark_as_processed(processing_data.processed_by)
        except ValueError as e:
            raise ValidationError(str(e))
        
        update_dict = {
            'is_processed': entity.is_processed,
            'processed_at': entity.processed_at,
            'processed_by': entity.processed_by,
            'updated_at': entity.updated_at,
            'updated_by': entity.updated_by
        }
        
        updated_line = await self.repository.update_rental_return_line(line_id, update_dict)
        return RentalReturnLineResponse.model_validate(updated_line)
    
    # Specialized Operations
    async def get_returns_by_status(self, status: ReturnStatus) -> List[RentalReturnListResponse]:
        """Get returns by status."""
        returns = await self.repository.get_returns_by_status(status)
        return [RentalReturnListResponse.model_validate(ret) for ret in returns]
    
    async def get_overdue_returns(self) -> List[RentalReturnListResponse]:
        """Get overdue returns."""
        returns = await self.repository.get_overdue_returns()
        return [RentalReturnListResponse.model_validate(ret) for ret in returns]
    
    async def get_lines_needing_processing(self) -> List[RentalReturnLineResponse]:
        """Get return lines that need processing."""
        lines = await self.repository.get_lines_needing_processing()
        return [RentalReturnLineResponse.model_validate(line) for line in lines]
    
    async def get_damaged_returns(self) -> List[RentalReturnLineResponse]:
        """Get return lines with damage."""
        lines = await self.repository.get_damaged_returns()
        return [RentalReturnLineResponse.model_validate(line) for line in lines]
    
    # Bulk Operations
    async def bulk_update_return_status(self, bulk_update: RentalReturnBulkStatusUpdate, updated_by: Optional[str] = None) -> int:
        """Bulk update status for multiple returns."""
        # Validate that all returns exist
        for return_id in bulk_update.return_ids:
            rental_return = await self.repository.get_rental_return_by_id(return_id)
            if not rental_return:
                raise NotFoundError(f"Rental return with ID {return_id} not found")
        
        # Perform bulk update
        updated_count = await self.repository.bulk_update_return_status(
            bulk_update.return_ids,
            bulk_update.new_status,
            updated_by
        )
        
        return updated_count
    
    async def bulk_process_return_lines(self, bulk_processing: RentalReturnLineBulkProcessing) -> int:
        """Bulk process return lines."""
        # Validate that all lines exist
        for line_id in bulk_processing.line_ids:
            return_line = await self.repository.get_rental_return_line_by_id(line_id)
            if not return_line:
                raise NotFoundError(f"Rental return line with ID {line_id} not found")
        
        # Perform bulk processing
        updated_count = await self.repository.bulk_process_return_lines(
            bulk_processing.line_ids,
            bulk_processing.processed_by
        )
        
        return updated_count
    
    async def delete_rental_return(self, return_id: UUID, deleted_by: Optional[str] = None) -> bool:
        """Soft delete rental return."""
        rental_return = await self.repository.get_rental_return_by_id(return_id)
        if not rental_return:
            raise NotFoundError(f"Rental return with ID {return_id} not found")
        
        # Perform soft delete
        deleted_return = await self.repository.soft_delete_rental_return(return_id, deleted_by)
        return deleted_return is not None
    
    # Analytics and Reporting
    async def get_return_analytics(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> RentalReturnAnalytics:
        """Get comprehensive return analytics."""
        # Get basic metrics
        metrics_data = await self.repository.get_return_metrics(start_date, end_date)
        
        # Get status breakdown
        status_summary = await self.repository.get_return_summary_by_status()
        total_returns = sum(status_summary.values())
        
        status_breakdown = [
            {
                "status": status,
                "count": count,
                "percentage": (count / total_returns * 100) if total_returns > 0 else 0
            }
            for status, count in status_summary.items()
        ]
        
        # Get damage breakdown
        damage_summary = await self.repository.get_damage_summary()
        
        damage_breakdown = [
            {
                "damage_level": damage_level,
                "count": data["count"],
                "total_damage_fees": Decimal(str(data["total_fees"]))
            }
            for damage_level, data in damage_summary.items()
        ]
        
        metrics = RentalReturnMetrics(
            total_returns=metrics_data["total_returns"],
            completed_returns=metrics_data["completed_returns"],
            cancelled_returns=status_summary.get(ReturnStatus.CANCELLED.value, 0),
            returns_with_damage=sum(
                data["count"] for level, data in damage_summary.items() 
                if level != DamageLevel.NONE.value
            ),
            returns_with_late_fees=0,  # This would need additional query
            average_return_time_days=0.0,  # This would need additional calculation
            total_fees_collected=Decimal(str(metrics_data["total_fees"])),
            total_refunds_issued=Decimal(str(metrics_data["total_refunds"]))
        )
        
        return RentalReturnAnalytics(
            metrics=metrics,
            status_breakdown=status_breakdown,
            damage_breakdown=damage_breakdown,
            period_start=start_date or date.today(),
            period_end=end_date or date.today()
        )
    
    async def estimate_return_costs(self, return_data: RentalReturnCreate) -> RentalReturnEstimate:
        """Estimate costs for a potential return."""
        total_late_fees = Decimal('0.00')
        total_damage_fees = Decimal('0.00')
        days_late = 0
        
        # Calculate days late if expected return date is provided
        if return_data.expected_return_date and return_data.return_date > return_data.expected_return_date:
            days_late = (return_data.return_date - return_data.expected_return_date).days
        
        # Sum up fees from lines
        for line in return_data.lines:
            if line.late_fee:
                total_late_fees += line.late_fee
            if line.damage_fee:
                total_damage_fees += line.damage_fee
            if line.cleaning_fee:
                total_damage_fees += line.cleaning_fee
            if line.replacement_fee:
                total_damage_fees += line.replacement_fee
        
        total_fees = total_late_fees + total_damage_fees
        
        # These would typically be calculated based on business logic
        estimated_deposit_release = Decimal('0.00')
        estimated_refund = Decimal('0.00')
        
        return RentalReturnEstimate(
            estimated_late_fees=total_late_fees,
            estimated_damage_fees=total_damage_fees,
            estimated_total_fees=total_fees,
            estimated_deposit_release=estimated_deposit_release,
            estimated_refund_amount=estimated_refund,
            days_late=days_late
        )
    
    # Helper Methods
    async def _update_return_totals(self, return_id: UUID):
        """Update calculated totals for a return based on its lines."""
        lines = await self.repository.get_rental_return_lines_by_return(return_id)
        
        total_late_fee = sum(Decimal(str(line.late_fee)) for line in lines)
        total_damage_fee = sum(
            Decimal(str(line.damage_fee)) + 
            Decimal(str(line.cleaning_fee)) + 
            Decimal(str(line.replacement_fee))
            for line in lines
        )
        
        await self.repository.update_rental_return(return_id, {
            'total_late_fee': float(total_late_fee),
            'total_damage_fee': float(total_damage_fee)
        })