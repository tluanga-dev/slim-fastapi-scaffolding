from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update, delete
from sqlalchemy.orm import selectinload
from app.modules.customer_addresses.models import CustomerAddressModel
from app.modules.customer_addresses.schemas import CustomerAddressCreate, CustomerAddressUpdate
from app.core.domain.entities.customer_address import CustomerAddress
from app.core.domain.value_objects.address_type import AddressType
from app.core.errors import NotFoundError, ValidationError


class CustomerAddressRepository:
    """Repository for customer address data access operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_address(self, address_data: CustomerAddressCreate) -> CustomerAddress:
        """Create a new customer address."""
        # Check if setting as default
        if address_data.is_default:
            # Unset any existing default addresses for this customer and address type
            await self._unset_default_addresses(address_data.customer_id, address_data.address_type)
        
        # Create domain entity
        address_entity = CustomerAddress(
            customer_id=address_data.customer_id,
            address_type=address_data.address_type,
            street=address_data.street,
            address_line2=address_data.address_line2,
            city=address_data.city,
            state=address_data.state,
            country=address_data.country,
            postal_code=address_data.postal_code,
            is_default=address_data.is_default,
            created_by=address_data.created_by
        )
        
        # Convert to ORM model
        address_model = CustomerAddressModel.from_entity(address_entity)
        
        # Save to database
        self.session.add(address_model)
        await self.session.commit()
        await self.session.refresh(address_model)
        
        return address_model.to_entity()
    
    async def get_address_by_id(self, address_id: UUID) -> Optional[CustomerAddress]:
        """Get customer address by ID."""
        stmt = select(CustomerAddressModel).where(CustomerAddressModel.id == address_id)
        result = await self.session.execute(stmt)
        address_model = result.scalar_one_or_none()
        
        if address_model:
            return address_model.to_entity()
        return None
    
    async def get_addresses_by_customer(
        self,
        customer_id: UUID,
        is_active: Optional[bool] = None,
        address_type: Optional[AddressType] = None
    ) -> List[CustomerAddress]:
        """Get all addresses for a customer."""
        conditions = [CustomerAddressModel.customer_id == customer_id]
        
        if is_active is not None:
            conditions.append(CustomerAddressModel.is_active == is_active)
        
        if address_type is not None:
            conditions.append(CustomerAddressModel.address_type == address_type)
        
        stmt = select(CustomerAddressModel).where(and_(*conditions)).order_by(
            CustomerAddressModel.is_default.desc(),
            CustomerAddressModel.created_at.desc()
        )
        
        result = await self.session.execute(stmt)
        address_models = result.scalars().all()
        
        return [model.to_entity() for model in address_models]
    
    async def get_default_address(
        self,
        customer_id: UUID,
        address_type: Optional[AddressType] = None
    ) -> Optional[CustomerAddress]:
        """Get default address for a customer."""
        conditions = [
            CustomerAddressModel.customer_id == customer_id,
            CustomerAddressModel.is_default == True,
            CustomerAddressModel.is_active == True
        ]
        
        if address_type is not None:
            conditions.append(CustomerAddressModel.address_type == address_type)
        
        stmt = select(CustomerAddressModel).where(and_(*conditions))
        result = await self.session.execute(stmt)
        address_model = result.scalar_one_or_none()
        
        if address_model:
            return address_model.to_entity()
        return None
    
    async def get_addresses_paginated(
        self,
        page: int = 1,
        page_size: int = 50,
        customer_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
        address_type: Optional[AddressType] = None,
        search: Optional[str] = None
    ) -> tuple[List[CustomerAddress], int]:
        """Get paginated list of customer addresses."""
        conditions = []
        
        if customer_id is not None:
            conditions.append(CustomerAddressModel.customer_id == customer_id)
        
        if is_active is not None:
            conditions.append(CustomerAddressModel.is_active == is_active)
        
        if address_type is not None:
            conditions.append(CustomerAddressModel.address_type == address_type)
        
        if search:
            search_term = f"%{search.lower()}%"
            search_conditions = [
                CustomerAddressModel.street.ilike(search_term),
                CustomerAddressModel.city.ilike(search_term),
                CustomerAddressModel.state.ilike(search_term),
                CustomerAddressModel.country.ilike(search_term),
                CustomerAddressModel.postal_code.ilike(search_term)
            ]
            conditions.append(or_(*search_conditions))
        
        base_stmt = select(CustomerAddressModel)
        if conditions:
            base_stmt = base_stmt.where(and_(*conditions))
        
        # Get total count
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar()
        
        # Get paginated results
        offset = (page - 1) * page_size
        stmt = base_stmt.order_by(
            CustomerAddressModel.is_default.desc(),
            CustomerAddressModel.created_at.desc()
        ).offset(offset).limit(page_size)
        
        result = await self.session.execute(stmt)
        address_models = result.scalars().all()
        
        addresses = [model.to_entity() for model in address_models]
        return addresses, total
    
    async def search_addresses(
        self,
        query: str,
        customer_id: Optional[UUID] = None,
        limit: int = 10
    ) -> List[CustomerAddress]:
        """Search addresses by query."""
        search_term = f"%{query.lower()}%"
        
        conditions = [
            CustomerAddressModel.is_active == True,
            or_(
                CustomerAddressModel.street.ilike(search_term),
                CustomerAddressModel.city.ilike(search_term),
                CustomerAddressModel.state.ilike(search_term),
                CustomerAddressModel.country.ilike(search_term)
            )
        ]
        
        if customer_id is not None:
            conditions.append(CustomerAddressModel.customer_id == customer_id)
        
        stmt = select(CustomerAddressModel).where(and_(*conditions)).limit(limit)
        result = await self.session.execute(stmt)
        address_models = result.scalars().all()
        
        return [model.to_entity() for model in address_models]
    
    async def update_address(self, address_id: UUID, update_data: CustomerAddressUpdate) -> Optional[CustomerAddress]:
        """Update customer address."""
        # Get existing address
        address_model = await self._get_address_model_by_id(address_id)
        if not address_model:
            return None
        
        # Convert to entity and update
        address_entity = address_model.to_entity()
        
        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        if update_dict:
            address_entity.update_details(
                street=update_dict.get('street'),
                address_line2=update_dict.get('address_line2'),
                city=update_dict.get('city'),
                state=update_dict.get('state'),
                country=update_dict.get('country'),
                postal_code=update_dict.get('postal_code'),
                updated_by=update_dict.get('updated_by')
            )
            
            if 'address_type' in update_dict:
                address_entity.address_type = update_dict['address_type']
        
        # Update model from entity
        updated_model = CustomerAddressModel.from_entity(address_entity)
        
        # Update in database
        stmt = update(CustomerAddressModel).where(
            CustomerAddressModel.id == address_id
        ).values(**{
            'address_type': updated_model.address_type,
            'street': updated_model.street,
            'address_line2': updated_model.address_line2,
            'city': updated_model.city,
            'state': updated_model.state,
            'country': updated_model.country,
            'postal_code': updated_model.postal_code,
            'updated_at': updated_model.updated_at,
            'updated_by': updated_model.updated_by
        })
        
        await self.session.execute(stmt)
        await self.session.commit()
        
        # Return updated entity
        return await self.get_address_by_id(address_id)
    
    async def update_address_status(self, address_id: UUID, is_active: bool, updated_by: Optional[str] = None) -> Optional[CustomerAddress]:
        """Update address status."""
        address_model = await self._get_address_model_by_id(address_id)
        if not address_model:
            return None
        
        address_entity = address_model.to_entity()
        
        if is_active:
            address_entity.activate()
        else:
            address_entity.deactivate()
        
        if updated_by:
            address_entity.updated_by = updated_by
        
        # Update in database
        stmt = update(CustomerAddressModel).where(
            CustomerAddressModel.id == address_id
        ).values(
            is_active=address_entity.is_active,
            is_default=address_entity.is_default,
            updated_at=address_entity.updated_at,
            updated_by=address_entity.updated_by
        )
        
        await self.session.execute(stmt)
        await self.session.commit()
        
        return await self.get_address_by_id(address_id)
    
    async def set_default_address(self, address_id: UUID, updated_by: Optional[str] = None) -> Optional[CustomerAddress]:
        """Set address as default."""
        address_model = await self._get_address_model_by_id(address_id)
        if not address_model:
            return None
        
        address_entity = address_model.to_entity()
        
        # Unset other default addresses for this customer and address type
        await self._unset_default_addresses(address_entity.customer_id, address_entity.address_type)
        
        # Set this address as default
        address_entity.set_as_default()
        if updated_by:
            address_entity.updated_by = updated_by
        
        # Update in database
        stmt = update(CustomerAddressModel).where(
            CustomerAddressModel.id == address_id
        ).values(
            is_default=True,
            updated_at=address_entity.updated_at,
            updated_by=address_entity.updated_by
        )
        
        await self.session.execute(stmt)
        await self.session.commit()
        
        return await self.get_address_by_id(address_id)
    
    async def delete_address(self, address_id: UUID) -> bool:
        """Delete customer address."""
        stmt = delete(CustomerAddressModel).where(CustomerAddressModel.id == address_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        return result.rowcount > 0
    
    async def validate_addresses_for_customer(self, address_ids: List[UUID], customer_id: UUID) -> List[dict]:
        """Validate multiple addresses belong to customer."""
        stmt = select(CustomerAddressModel).where(
            CustomerAddressModel.id.in_(address_ids)
        )
        result = await self.session.execute(stmt)
        found_addresses = result.scalars().all()
        
        validation_results = []
        for address_id in address_ids:
            found_address = next((addr for addr in found_addresses if addr.id == address_id), None)
            
            if not found_address:
                validation_results.append({
                    'address_id': address_id,
                    'is_valid': False,
                    'is_active': False,
                    'exists': False,
                    'validation_message': 'Address not found'
                })
            elif found_address.customer_id != customer_id:
                validation_results.append({
                    'address_id': address_id,
                    'is_valid': False,
                    'is_active': found_address.is_active,
                    'exists': True,
                    'validation_message': 'Address does not belong to specified customer'
                })
            else:
                validation_results.append({
                    'address_id': address_id,
                    'is_valid': found_address.is_active,
                    'is_active': found_address.is_active,
                    'exists': True,
                    'validation_message': 'Valid address' if found_address.is_active else 'Address is inactive'
                })
        
        return validation_results
    
    async def _get_address_model_by_id(self, address_id: UUID) -> Optional[CustomerAddressModel]:
        """Get address model by ID (internal helper)."""
        stmt = select(CustomerAddressModel).where(CustomerAddressModel.id == address_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _unset_default_addresses(self, customer_id: UUID, address_type: AddressType) -> None:
        """Unset all default addresses for customer and address type."""
        stmt = update(CustomerAddressModel).where(
            and_(
                CustomerAddressModel.customer_id == customer_id,
                CustomerAddressModel.address_type == address_type,
                CustomerAddressModel.is_default == True
            )
        ).values(is_default=False)
        
        await self.session.execute(stmt)