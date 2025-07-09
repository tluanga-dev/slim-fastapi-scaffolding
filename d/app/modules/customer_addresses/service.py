from typing import List, Optional
from uuid import UUID
from math import ceil
from app.modules.customer_addresses.repository import CustomerAddressRepository
from app.modules.customer_addresses.schemas import (
    CustomerAddressCreate, CustomerAddressUpdate, CustomerAddressStatusUpdate,
    CustomerAddressDefaultUpdate, CustomerAddressResponse, CustomerAddressListResponse,
    CustomerAddressSummary, CustomerAddressValidationResponse, CustomerAddressBulkResponse
)
from app.core.domain.entities.customer_address import CustomerAddress
from app.core.domain.value_objects.address_type import AddressType
from app.core.errors import NotFoundError, ValidationError


class CustomerAddressService:
    """Service layer for customer address business logic."""
    
    def __init__(self, repository: CustomerAddressRepository):
        self.repository = repository
    
    async def create_address(self, address_data: CustomerAddressCreate) -> CustomerAddressResponse:
        """Create a new customer address."""
        try:
            address_entity = await self.repository.create_address(address_data)
            return CustomerAddressResponse.model_validate(address_entity)
        except ValueError as e:
            raise ValidationError(str(e))
        except Exception as e:
            raise Exception(f"Failed to create customer address: {str(e)}")
    
    async def get_address_by_id(self, address_id: UUID) -> CustomerAddressResponse:
        """Get customer address by ID."""
        address_entity = await self.repository.get_address_by_id(address_id)
        if not address_entity:
            raise NotFoundError(f"Customer address with ID {address_id} not found")
        
        return CustomerAddressResponse.model_validate(address_entity)
    
    async def get_addresses_by_customer(
        self,
        customer_id: UUID,
        is_active: Optional[bool] = None,
        address_type: Optional[AddressType] = None
    ) -> List[CustomerAddressResponse]:
        """Get all addresses for a customer."""
        address_entities = await self.repository.get_addresses_by_customer(
            customer_id, is_active, address_type
        )
        
        return [CustomerAddressResponse.model_validate(entity) for entity in address_entities]
    
    async def get_customer_addresses_summary(self, customer_id: UUID) -> List[CustomerAddressSummary]:
        """Get summary of all active addresses for a customer."""
        address_entities = await self.repository.get_addresses_by_customer(
            customer_id, is_active=True
        )
        
        return [CustomerAddressSummary.model_validate(entity) for entity in address_entities]
    
    async def get_default_address(
        self,
        customer_id: UUID,
        address_type: Optional[AddressType] = None
    ) -> Optional[CustomerAddressResponse]:
        """Get default address for a customer."""
        address_entity = await self.repository.get_default_address(customer_id, address_type)
        
        if address_entity:
            return CustomerAddressResponse.model_validate(address_entity)
        return None
    
    async def get_addresses_paginated(
        self,
        page: int = 1,
        page_size: int = 50,
        customer_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
        address_type: Optional[AddressType] = None,
        search: Optional[str] = None
    ) -> CustomerAddressListResponse:
        """Get paginated list of customer addresses."""
        if page < 1:
            raise ValidationError("Page number must be >= 1")
        if page_size < 1 or page_size > 100:
            raise ValidationError("Page size must be between 1 and 100")
        
        address_entities, total = await self.repository.get_addresses_paginated(
            page, page_size, customer_id, is_active, address_type, search
        )
        
        addresses = [CustomerAddressResponse.model_validate(entity) for entity in address_entities]
        total_pages = ceil(total / page_size) if total > 0 else 0
        
        return CustomerAddressListResponse(
            addresses=addresses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    
    async def search_addresses(
        self,
        query: str,
        customer_id: Optional[UUID] = None,
        limit: int = 10
    ) -> List[CustomerAddressSummary]:
        """Search addresses by query."""
        if len(query.strip()) < 2:
            raise ValidationError("Search query must be at least 2 characters long")
        
        if limit < 1 or limit > 50:
            raise ValidationError("Limit must be between 1 and 50")
        
        address_entities = await self.repository.search_addresses(query, customer_id, limit)
        return [CustomerAddressSummary.model_validate(entity) for entity in address_entities]
    
    async def update_address(self, address_id: UUID, update_data: CustomerAddressUpdate) -> CustomerAddressResponse:
        """Update customer address."""
        try:
            address_entity = await self.repository.update_address(address_id, update_data)
            if not address_entity:
                raise NotFoundError(f"Customer address with ID {address_id} not found")
            
            return CustomerAddressResponse.model_validate(address_entity)
        except ValueError as e:
            raise ValidationError(str(e))
        except NotFoundError:
            raise
        except Exception as e:
            raise Exception(f"Failed to update customer address: {str(e)}")
    
    async def update_address_status(
        self,
        address_id: UUID,
        status_data: CustomerAddressStatusUpdate
    ) -> CustomerAddressResponse:
        """Update customer address status."""
        try:
            address_entity = await self.repository.update_address_status(
                address_id, status_data.is_active, status_data.updated_by
            )
            if not address_entity:
                raise NotFoundError(f"Customer address with ID {address_id} not found")
            
            return CustomerAddressResponse.model_validate(address_entity)
        except ValueError as e:
            raise ValidationError(str(e))
        except NotFoundError:
            raise
        except Exception as e:
            raise Exception(f"Failed to update address status: {str(e)}")
    
    async def set_default_address(
        self,
        address_id: UUID,
        default_data: CustomerAddressDefaultUpdate
    ) -> CustomerAddressResponse:
        """Set address as default."""
        if not default_data.is_default:
            raise ValidationError("Can only set address as default, not unset")
        
        try:
            address_entity = await self.repository.set_default_address(
                address_id, default_data.updated_by
            )
            if not address_entity:
                raise NotFoundError(f"Customer address with ID {address_id} not found")
            
            return CustomerAddressResponse.model_validate(address_entity)
        except ValueError as e:
            raise ValidationError(str(e))
        except NotFoundError:
            raise
        except Exception as e:
            raise Exception(f"Failed to set default address: {str(e)}")
    
    async def delete_address(self, address_id: UUID) -> bool:
        """Delete customer address."""
        success = await self.repository.delete_address(address_id)
        if not success:
            raise NotFoundError(f"Customer address with ID {address_id} not found")
        
        return success
    
    async def validate_addresses_for_customer(
        self,
        address_ids: List[UUID],
        customer_id: UUID
    ) -> List[CustomerAddressValidationResponse]:
        """Validate multiple addresses belong to customer."""
        if not address_ids:
            raise ValidationError("Address IDs list cannot be empty")
        
        if len(address_ids) > 50:
            raise ValidationError("Cannot validate more than 50 addresses at once")
        
        validation_results = await self.repository.validate_addresses_for_customer(
            address_ids, customer_id
        )
        
        return [CustomerAddressValidationResponse(**result) for result in validation_results]
    
    async def get_address_statistics(self, customer_id: UUID) -> dict:
        """Get statistics for customer addresses."""
        all_addresses = await self.repository.get_addresses_by_customer(customer_id)
        
        stats = {
            'total_addresses': len(all_addresses),
            'active_addresses': len([addr for addr in all_addresses if addr.is_active]),
            'inactive_addresses': len([addr for addr in all_addresses if not addr.is_active]),
            'default_addresses': len([addr for addr in all_addresses if addr.is_default]),
            'addresses_by_type': {}
        }
        
        # Count by address type
        for address_type in AddressType:
            type_count = len([addr for addr in all_addresses if addr.address_type == address_type])
            if type_count > 0:
                stats['addresses_by_type'][address_type.value] = {
                    'total': type_count,
                    'active': len([
                        addr for addr in all_addresses 
                        if addr.address_type == address_type and addr.is_active
                    ]),
                    'default': len([
                        addr for addr in all_addresses 
                        if addr.address_type == address_type and addr.is_default
                    ])
                }
        
        return stats
    
    async def bulk_update_addresses_status(
        self,
        address_ids: List[UUID],
        is_active: bool,
        updated_by: Optional[str] = None
    ) -> CustomerAddressBulkResponse:
        """Bulk update addresses status."""
        if not address_ids:
            raise ValidationError("Address IDs list cannot be empty")
        
        if len(address_ids) > 100:
            raise ValidationError("Cannot update more than 100 addresses at once")
        
        processed = 0
        successful = 0
        failed = 0
        errors = []
        
        for address_id in address_ids:
            try:
                processed += 1
                result = await self.repository.update_address_status(address_id, is_active, updated_by)
                if result:
                    successful += 1
                else:
                    failed += 1
                    errors.append(f"Address {address_id} not found")
            except Exception as e:
                failed += 1
                errors.append(f"Address {address_id}: {str(e)}")
        
        return CustomerAddressBulkResponse(
            processed=processed,
            successful=successful,
            failed=failed,
            errors=errors
        )