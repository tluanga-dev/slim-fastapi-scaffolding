from sqlalchemy import Column, String, Boolean

from src.infrastructure.database import Base
from src.infrastructure.models.base import BaseModel


class UserModel(BaseModel):
    __tablename__ = "users"

    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)