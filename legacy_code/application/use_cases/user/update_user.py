from typing import Optional
from uuid import UUID

from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.domain.repositories.user_repository import UserRepository


class UpdateUserUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(
        self,
        user_id: UUID,
        email: Optional[str] = None,
        name: Optional[str] = None,
        hashed_password: Optional[str] = None,
        is_superuser: Optional[bool] = None,
        updated_by: Optional[str] = None,
    ) -> User:
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError(f"User with id {user_id} not found")

        if email:
            email_vo = Email(email)
            existing_user = await self.user_repository.get_by_email(email_vo)
            if existing_user and existing_user.id != user_id:
                raise ValueError(f"User with email {email} already exists")
            user.update_email(email_vo, updated_by)

        if name:
            user.update_name(name, updated_by)

        if hashed_password:
            user.update_password(hashed_password, updated_by)

        if is_superuser is not None:
            if is_superuser:
                user.make_superuser(updated_by)
            else:
                user.revoke_superuser(updated_by)

        return await self.user_repository.update(user)