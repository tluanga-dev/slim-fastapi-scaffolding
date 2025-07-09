from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, DateTime, Boolean, String
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
import sqlalchemy as sa
from ..database import Base


# Create a UUID type that works with both PostgreSQL and SQLite
class UUID(sa.TypeDecorator):
    """Platform-independent UUID type.
    Uses PostgreSQL's UUID type when available,
    otherwise uses CHAR(36), storing as stringified hex values.
    """
    impl = sa.CHAR(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgresUUID(as_uuid=True))
        else:
            return dialect.type_descriptor(sa.CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid4.__class__):
                from uuid import UUID as python_UUID
                return python_UUID(value)
            else:
                return value


class BaseModel(Base):
    __abstract__ = True
    
    id = Column(UUID(), primary_key=True, default=uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)