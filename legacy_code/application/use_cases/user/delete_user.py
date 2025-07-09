from uuid import UUID
from typing import Optional

from src.domain.repositories.user_repository import UserRepository


class DeleteUserUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, user_id: UUID, deleted_by: Optional[str] = None) -> bool:
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError(f"User with id {user_id} not found")
        
        user.soft_delete(deleted_by)
        await self.user_repository.update(user)
        return True