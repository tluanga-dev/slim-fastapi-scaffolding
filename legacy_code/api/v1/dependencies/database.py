from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database import get_session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_session():
        yield session