from app.modules.items.repository import ItemRepository

class ItemService:
    def __init__(self, item_repo: ItemRepository):
        self.repo = item_repo

    async def create_item(self, item_data):
        return await self.repo.create_item(item_data)

    async def get_item(self, item_id: int):
        return await self.repo.get_item(item_id)