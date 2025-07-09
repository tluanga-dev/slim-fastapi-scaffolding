from typing import List

from src.domain.entities.user import User
from src.domain.repositories.user_repository import UserRepository


class ListUsersUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(
        self, skip: int = 0, limit: int = 100, active_only: bool = True
    ) -> List[User]:
        if active_only:
            return await self.user_repository.get_active(skip=skip, limit=limit)
        return await self.user_repository.get_all(skip=skip, limit=limit)