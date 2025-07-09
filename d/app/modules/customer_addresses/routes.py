from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.modules.customer_addresses.service import CustomerAddressService
from app.modules.customer_addresses.schemas import (
    CustomerAddressCreate, CustomerAddressUpdate, CustomerAddressStatusUpdate,
    CustomerAddressDefaultUpdate, CustomerAddressResponse, CustomerAddressListResponse,
    CustomerAddressSummary, CustomerAddressValidationResponse, CustomerAddressBulkResponse
)
from app.core.domain.value_objects.address_type import AddressType
from app.core.errors import NotFoundError, ValidationError
from app.shared.dependencies import get_customer_address_service


router = APIRouter(tags=["customer-addresses"])


@router.post("/", response_model=CustomerAddressResponse, status_code=status.HTTP_201_CREATED)
async def create_customer_address(
    address_data: CustomerAddressCreate,
    service: CustomerAddressService = Depends(get_customer_address_service)
):
    """Create a new customer address."""
    try:
        return await service.create_address(address_data)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/", response_model=CustomerAddressListResponse)
async def get_customer_addresses(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    customer_id: Optional[UUID] = Query(None, description="Filter by customer ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    address_type: Optional[AddressType] = Query(None, description="Filter by address type"),
    search: Optional[str] = Query(None, description="Search in address fields"),
    service: CustomerAddressService = Depends(get_customer_address_service)
):
    """Get customer addresses with filtering and pagination."""
    try:
        return await service.get_addresses_paginated(
            page=page,
            page_size=page_size,
            customer_id=customer_id,
            is_active=is_active,
            address_type=address_type,
            search=search
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/customer/{customer_id}", response_model=List[CustomerAddressResponse])
async def get_addresses_by_customer(
    customer_id: UUID,
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    address_type: Optional[AddressType] = Query(None, description="Filter by address type"),
    service: CustomerAddressService = Depends(get_customer_address_service)
):
    """Get all addresses for a specific customer."""
    try:
        return await service.get_addresses_by_customer(
            customer_id=customer_id,
            is_active=is_active,
            address_type=address_type
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/customer/{customer_id}/summary", response_model=List[CustomerAddressSummary])
async def get_customer_addresses_summary(
    customer_id: UUID,
    service: CustomerAddressService = Depends(get_customer_address_service)
):
    """Get summary of all active addresses for a customer."""
    try:
        return await service.get_customer_addresses_summary(customer_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/customer/{customer_id}/default", response_model=Optional[CustomerAddressResponse])
async def get_customer_default_address(
    customer_id: UUID,
    address_type: Optional[AddressType] = Query(None, description="Filter by address type"),
    service: CustomerAddressService = Depends(get_customer_address_service)
):
    """Get default address for a customer."""
    try:
        return await service.get_default_address(customer_id, address_type)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/customer/{customer_id}/statistics")
async def get_customer_address_statistics(
    customer_id: UUID,
    service: CustomerAddressService = Depends(get_customer_address_service)
):
    """Get statistics for customer addresses."""
    try:
        return await service.get_address_statistics(customer_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/search", response_model=List[CustomerAddressSummary])
async def search_customer_addresses(
    q: str = Query(..., min_length=2, description="Search query for address fields"),
    customer_id: Optional[UUID] = Query(None, description="Filter by customer ID"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    service: CustomerAddressService = Depends(get_customer_address_service)
):
    """Search customer addresses by query."""
    try:
        return await service.search_addresses(q, customer_id, limit)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{address_id}", response_model=CustomerAddressResponse)
async def get_customer_address_by_id(
    address_id: UUID,
    service: CustomerAddressService = Depends(get_customer_address_service)
):
    """Get customer address by ID."""
    try:
        return await service.get_address_by_id(address_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{address_id}", response_model=CustomerAddressResponse)
async def update_customer_address(
    address_id: UUID,
    update_data: CustomerAddressUpdate,
    service: CustomerAddressService = Depends(get_customer_address_service)
):
    """Update customer address."""
    try:
        return await service.update_address(address_id, update_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/{address_id}/status", response_model=CustomerAddressResponse)
async def update_customer_address_status(
    address_id: UUID,
    status_data: CustomerAddressStatusUpdate,
    service: CustomerAddressService = Depends(get_customer_address_service)
):
    """Update customer address status (activate/deactivate)."""
    try:
        return await service.update_address_status(address_id, status_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/{address_id}/default", response_model=CustomerAddressResponse)
async def set_customer_address_as_default(
    address_id: UUID,
    default_data: CustomerAddressDefaultUpdate,
    service: CustomerAddressService = Depends(get_customer_address_service)
):
    """Set customer address as default."""
    try:
        return await service.set_default_address(address_id, default_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer_address(
    address_id: UUID,
    service: CustomerAddressService = Depends(get_customer_address_service)
):
    """Delete customer address."""
    try:
        success = await service.delete_address(address_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer address not found")
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/validate", response_model=List[CustomerAddressValidationResponse])
async def validate_customer_addresses(
    address_ids: List[UUID],
    customer_id: UUID = Query(..., description="Customer ID to validate addresses against"),
    service: CustomerAddressService = Depends(get_customer_address_service)
):
    """Validate multiple customer addresses belong to customer."""
    try:
        return await service.validate_addresses_for_customer(address_ids, customer_id)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/bulk/status", response_model=CustomerAddressBulkResponse)
async def bulk_update_customer_addresses_status(
    address_ids: List[UUID],
    is_active: bool = Query(..., description="Active status to set"),
    updated_by: Optional[str] = Query(None, description="User performing the update"),
    service: CustomerAddressService = Depends(get_customer_address_service)
):
    """Bulk update customer addresses status."""
    try:
        return await service.bulk_update_addresses_status(address_ids, is_active, updated_by)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))