from abc import abstractmethod
from typing import Optional

from src.domain.repositories.base import BaseRepository
from src.domain.entities.user import User
from src.domain.value_objects.email import Email


class UserRepository(BaseRepository[User]):
    @abstractmethod
    async def get_by_email(self, email: Email) -> Optional[User]:
        pass