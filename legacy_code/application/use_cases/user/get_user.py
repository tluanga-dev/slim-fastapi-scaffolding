from typing import Optional
from uuid import UUID

from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.domain.repositories.user_repository import UserRepository


class GetUserUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute_by_id(self, user_id: UUID) -> Optional[User]:
        return await self.user_repository.get_by_id(user_id)

    async def execute_by_email(self, email: str) -> Optional[User]:
        email_vo = Email(email)
        return await self.user_repository.get_by_email(email_vo)