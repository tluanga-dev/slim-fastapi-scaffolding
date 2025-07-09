from fastapi import APIRouter, Depends, HTTPException
from app.modules.items import schemas
from app.shared.dependencies import get_item_service

router = APIRouter(tags=["Items"])

@router.post("/", response_model=schemas.ItemResponse)
async def create_item(
    item: schemas.ItemCreate, 
    service=Depends(get_item_service)
):
    return await service.create_item(item.model_dump())

@router.get("/{item_id}", response_model=schemas.ItemResponse)
async def read_item(
    item_id: int, 
    service=Depends(get_item_service)
):
    item = await service.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item