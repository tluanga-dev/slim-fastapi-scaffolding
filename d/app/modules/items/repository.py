from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.modules.items.models import Item

class ItemRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_item(self, item_data: dict) -> Item:
        item = Item(**item_data)
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def get_item(self, item_id: int) -> Item | None:
        result = await self.session.execute(select(Item).filter(Item.id == item_id))
        return result.scalars().first()