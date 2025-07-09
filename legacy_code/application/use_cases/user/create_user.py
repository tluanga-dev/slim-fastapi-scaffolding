from typing import Optional
from uuid import UUID

from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.domain.repositories.user_repository import UserRepository


class CreateUserUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(
        self,
        email: str,
        name: str,
        hashed_password: str,
        is_superuser: bool = False,
        created_by: Optional[str] = None,
    ) -> User:
        email_vo = Email(email)
        
        existing_user = await self.user_repository.get_by_email(email_vo)
        if existing_user:
            raise ValueError(f"User with email {email} already exists")
        
        user = User(
            email=email_vo,
            name=name,
            hashed_password=hashed_password,
            is_superuser=is_superuser,
            created_by=created_by,
        )
        
        return await self.user_repository.create(user)