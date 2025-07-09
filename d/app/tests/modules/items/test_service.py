import pytest
from app.modules.items.service import ItemService
from app.modules.items.repository import ItemRepository
from app.modules.items.models import Item

@pytest.mark.asyncio
async def test_create_item(test_session):
    repo = ItemRepository(test_session)
    service = ItemService(repo)
    item_data = {"name": "Test", "description": "Test Desc"}
    item = await service.create_item(item_data)
    assert item.id is not None
    assert item.name == "Test"

@pytest.mark.asyncio
async def test_get_item(test_session):
    repo = ItemRepository(test_session)
    service = ItemService(repo)
    
    # Create item first
    item = await service.create_item({"name": "Test", "description": "Test"})
    
    # Retrieve item
    retrieved = await service.get_item(item.id)
    assert retrieved.id == item.id
    assert retrieved.name == "Test"

@pytest.mark.asyncio
async def test_get_nonexistent_item(test_session):
    repo = ItemRepository(test_session)
    service = ItemService(repo)
    
    # Try to get non-existent item
    retrieved = await service.get_item(999)
    assert retrieved is None