from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies.database import get_db
from src.domain.repositories.user_repository import UserRepository
from src.infrastructure.repositories.user_repository import UserRepositoryImpl


async def get_user_repository(
    db: AsyncSession = Depends(get_db),
) -> UserRepository:
    return UserRepositoryImpl(db)