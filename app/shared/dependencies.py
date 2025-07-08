from fastapi import Depends
from app.db.session import get_session
from app.modules.items.repository import ItemRepository
from app.modules.items.service import ItemService

async def get_item_repository(session=Depends(get_session)):
    return ItemRepository(session)

async def get_item_service(repo=Depends(get_item_repository)):
    return ItemService(repo)