import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.base import Base
from app.core.config import settings
from app.db.session import get_session

# Test database engine
test_engine = create_async_engine(settings.TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(
    bind=test_engine, 
    class_=AsyncSession,
    expire_on_commit=False
)

async def override_get_session():
    async with TestingSessionLocal() as session:
        yield session

# Override the dependency
app.dependency_overrides[get_session] = override_get_session

@pytest.fixture(scope="session")
def test_client():
    return TestClient(app)

@pytest.fixture(scope="function")
async def test_session():
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestingSessionLocal() as session:
        yield session
        
    # Drop tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(autouse=True)
async def setup_test_db():
    """Set up test database before each test"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)