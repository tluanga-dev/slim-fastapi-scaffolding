from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....application.use_cases.item import (
    CreateItemUseCase,
    GetItemUseCase,
    UpdateItemUseCase,
    DeleteItemUseCase,
    ListItemsUseCase
)
from ....infrastructure.repositories.item_repository import ItemRepositoryImpl
from ..schemas.item_schemas import (
    ItemCreate,
    ItemUpdate,
    ItemPricingUpdate,
    ItemRentalSettingsUpdate,
    ItemSaleSettingsUpdate,
    ItemResponse,
    ItemListResponse,
    ItemWithRelationsResponse,
    ItemListWithRelationsResponse,
    ItemSearchRequest
)
from ..dependencies.database import get_db

router = APIRouter(tags=["items"])


async def get_item_repository(db: AsyncSession = Depends(get_db)) -> ItemRepositoryImpl:
    """Get item repository instance."""
    return ItemRepositoryImpl(db)


@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(
    item_data: ItemCreate,
    repository: ItemRepositoryImpl = Depends(get_item_repository),
    current_user_id: Optional[str] = None  # TODO: Get from auth
):
    """Create a new item."""
    use_case = CreateItemUseCase(repository)
    
    try:
        item = await use_case.execute(
            sku=item_data.sku,
            item_name=item_data.item_name,
            category_id=item_data.category_id,
            brand_id=item_data.brand_id,
            description=item_data.description,
            is_serialized=item_data.is_serialized,
            barcode=item_data.barcode,
            model_number=item_data.model_number,
            weight=item_data.weight,
            dimensions=item_data.dimensions,
            is_rentable=item_data.is_rentable,
            is_saleable=item_data.is_saleable,
            min_rental_days=item_data.min_rental_days,
            rental_period=item_data.rental_period,
            max_rental_days=item_data.max_rental_days,
            rental_base_price=item_data.rental_base_price,
            sale_base_price=item_data.sale_base_price,
            created_by=current_user_id
        )
        return ItemResponse.model_validate(item)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: UUID,
    repository: ItemRepositoryImpl = Depends(get_item_repository)
):
    """Get an item by ID."""
    use_case = GetItemUseCase(repository)
    item = await use_case.execute(item_id)
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found"
        )
    
    return ItemResponse.model_validate(item)


@router.get("/by-sku/{sku}", response_model=ItemResponse)
async def get_item_by_sku(
    sku: str,
    repository: ItemRepositoryImpl = Depends(get_item_repository)
):
    """Get an item by SKU."""
    item = await repository.get_by_sku(sku)
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with SKU '{sku}' not found"
        )
    
    return ItemResponse.model_validate(item)


@router.get("/by-barcode/{barcode}", response_model=ItemResponse)
async def get_item_by_barcode(
    barcode: str,
    repository: ItemRepositoryImpl = Depends(get_item_repository)
):
    """Get an item by barcode."""
    item = await repository.get_by_barcode(barcode)
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with barcode '{barcode}' not found"
        )
    
    return ItemResponse.model_validate(item)


@router.get("/", response_model=ItemListWithRelationsResponse)
async def list_items(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    category_id: Optional[UUID] = Query(None, description="Filter by category ID"),
    brand_id: Optional[UUID] = Query(None, description="Filter by brand ID"),
    is_rentable: Optional[bool] = Query(None, description="Filter by rentable status"),
    is_saleable: Optional[bool] = Query(None, description="Filter by saleable status"),
    repository: ItemRepositoryImpl = Depends(get_item_repository)
):
    """List items with pagination and filters."""
    # Get items with relations
    items_with_relations = await repository.get_all_with_relations(
        skip=skip, 
        limit=limit,
        category_id=category_id,
        brand_id=brand_id,
        is_rentable=is_rentable,
        is_saleable=is_saleable
    )
    
    # Convert to response format with relations
    items_response = []
    for item_model in items_with_relations:
        item_data = {
            "id": item_model.id,
            "item_id": item_model.item_id,
            "sku": item_model.sku,
            "item_name": item_model.item_name,
            "category_id": item_model.category_id,
            "brand_id": item_model.brand_id,
            "description": item_model.description,
            "is_serialized": item_model.is_serialized,
            "barcode": item_model.barcode,
            "model_number": item_model.model_number,
            "weight": item_model.weight,
            "dimensions": item_model.dimensions,
            "is_rentable": item_model.is_rentable,
            "is_saleable": item_model.is_saleable,
            "min_rental_days": item_model.min_rental_days,
            "rental_period": item_model.rental_period,
            "max_rental_days": item_model.max_rental_days,
            "rental_base_price": item_model.rental_base_price,
            "sale_base_price": item_model.sale_base_price,
            "created_at": item_model.created_at,
            "updated_at": item_model.updated_at,
            "created_by": item_model.created_by,
            "updated_by": item_model.updated_by,
            "is_active": item_model.is_active,
            "category": item_model.category,
            "brand": item_model.brand
        }
        items_response.append(ItemWithRelationsResponse(**item_data))
    
    # Note: For simplicity, we're not implementing total count
    # In a real app, you'd want to implement a separate count query
    total_count = len(items_response)
    
    return ItemListWithRelationsResponse(
        items=items_response,
        total=total_count,
        skip=skip,
        limit=limit
    )


@router.post("/search", response_model=ItemListResponse)
async def search_items(
    search_request: ItemSearchRequest,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    repository: ItemRepositoryImpl = Depends(get_item_repository)
):
    """Search items by name or SKU."""
    if search_request.search_type == "name":
        items = await repository.search_by_name(search_request.query, skip=skip, limit=limit)
    else:  # search_type == "sku"
        items = await repository.search_by_sku(search_request.query, skip=skip, limit=limit)
    
    total_count = len(items)
    
    return ItemListResponse(
        items=[ItemResponse.model_validate(item) for item in items],
        total=total_count,
        skip=skip,
        limit=limit
    )


@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: UUID,
    item_data: ItemUpdate,
    repository: ItemRepositoryImpl = Depends(get_item_repository),
    current_user_id: Optional[str] = None  # TODO: Get from auth
):
    """Update an existing item's basic information."""
    use_case = UpdateItemUseCase(repository)
    
    try:
        # Start with basic info update
        item = await use_case.execute(
            item_id=item_id,
            item_name=item_data.item_name,
            description=item_data.description,
            barcode=item_data.barcode,
            model_number=item_data.model_number,
            weight=item_data.weight,
            dimensions=item_data.dimensions,
            updated_by=current_user_id
        )
        
        # Update rental settings if is_rentable is provided
        if item_data.is_rentable is not None:
            item = await use_case.execute_rental_settings(
                item_id=item_id,
                is_rentable=item_data.is_rentable,
                updated_by=current_user_id
            )
        
        # Update sale settings if is_saleable is provided
        if item_data.is_saleable is not None:
            item = await use_case.execute_sale_settings(
                item_id=item_id,
                is_saleable=item_data.is_saleable,
                updated_by=current_user_id
            )
        
        return ItemResponse.model_validate(item)
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{item_id}/pricing", response_model=ItemResponse)
async def update_item_pricing(
    item_id: UUID,
    pricing_data: ItemPricingUpdate,
    repository: ItemRepositoryImpl = Depends(get_item_repository),
    current_user_id: Optional[str] = None  # TODO: Get from auth
):
    """Update an item's pricing information."""
    use_case = UpdateItemUseCase(repository)
    
    try:
        item = await use_case.execute_pricing(
            item_id=item_id,
            rental_base_price=pricing_data.rental_base_price,
            sale_base_price=pricing_data.sale_base_price,
            updated_by=current_user_id
        )
        return ItemResponse.model_validate(item)
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{item_id}/rental-settings", response_model=ItemResponse)
async def update_item_rental_settings(
    item_id: UUID,
    rental_data: ItemRentalSettingsUpdate,
    repository: ItemRepositoryImpl = Depends(get_item_repository),
    current_user_id: Optional[str] = None  # TODO: Get from auth
):
    """Update an item's rental settings."""
    use_case = UpdateItemUseCase(repository)
    
    try:
        item = await use_case.execute_rental_settings(
            item_id=item_id,
            is_rentable=rental_data.is_rentable,
            min_rental_days=rental_data.min_rental_days,
            rental_period=rental_data.rental_period,
            max_rental_days=rental_data.max_rental_days,
            updated_by=current_user_id
        )
        return ItemResponse.model_validate(item)
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{item_id}/sale-settings", response_model=ItemResponse)
async def update_item_sale_settings(
    item_id: UUID,
    sale_data: ItemSaleSettingsUpdate,
    repository: ItemRepositoryImpl = Depends(get_item_repository),
    current_user_id: Optional[str] = None  # TODO: Get from auth
):
    """Update an item's sale settings."""
    use_case = UpdateItemUseCase(repository)
    
    try:
        item = await use_case.execute_sale_settings(
            item_id=item_id,
            is_saleable=sale_data.is_saleable,
            updated_by=current_user_id
        )
        return ItemResponse.model_validate(item)
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: UUID,
    repository: ItemRepositoryImpl = Depends(get_item_repository),
    current_user_id: Optional[str] = None  # TODO: Get from auth
):
    """Delete (deactivate) an item."""
    use_case = DeleteItemUseCase(repository)
    
    success = await use_case.execute(item_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found"
        )


@router.get("/check-sku/{sku}", response_model=dict)
async def check_sku_availability(
    sku: str,
    repository: ItemRepositoryImpl = Depends(get_item_repository)
):
    """Check if a SKU is available."""
    existing_item = await repository.get_by_sku(sku)
    return {"available": existing_item is None, "sku": sku}


@router.get("/sku-pattern/{pattern}", response_model=dict)
async def get_skus_by_pattern(
    pattern: str,
    repository: ItemRepositoryImpl = Depends(get_item_repository)
):
    """Get all SKUs matching a pattern prefix."""
    # Search for SKUs starting with the pattern
    items = await repository.search_by_sku(pattern, skip=0, limit=1000)
    skus = [item.sku for item in items if item.sku.startswith(pattern)]
    
    # Find the highest sequential number
    max_number = 0
    for sku in skus:
        parts = sku.split('-')
        if len(parts) >= 5:  # Expected format: XXX-XXX-XXX-XXX-000
            try:
                number = int(parts[-1])
                max_number = max(max_number, number)
            except ValueError:
                continue
    
    next_number = max_number + 1
    next_sku_number = str(next_number).zfill(3)
    
    return {
        "pattern": pattern,
        "existing_skus": skus,
        "next_number": next_sku_number,
        "next_sku": f"{pattern}-{next_sku_number}"
    }


@router.post("/generate-sku", response_model=dict)
async def generate_sku(
    sku_data: dict,
    repository: ItemRepositoryImpl = Depends(get_item_repository)
):
    """Generate a unique SKU based on provided components."""
    category_code = sku_data.get("category_code", "CTG")
    brand_code = sku_data.get("brand_code", "BRD")
    color_code = sku_data.get("color_code", "CLR")
    size_code = sku_data.get("size_code", "STD")
    
    # Create base pattern
    base_pattern = f"{category_code}-{brand_code}-{color_code}-{size_code}"
    
    # Get next available number
    result = await get_skus_by_pattern(base_pattern, repository)
    
    return {
        "sku": result["next_sku"],
        "components": {
            "category_code": category_code,
            "brand_code": brand_code,
            "color_code": color_code,
            "size_code": size_code,
            "sequential_number": result["next_number"]
        }
    }