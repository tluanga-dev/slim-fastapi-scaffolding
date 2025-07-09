import pytest
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import patch
from datetime import datetime, timedelta

from app.modules.auth.models import User, Role, Permission
from app.modules.auth.schemas import UserRegister, UserLogin
from app.core.security import create_access_token


@pytest.mark.integration
class TestAuthRoutes:
    """Test authentication API routes."""
    
    @pytest_asyncio.fixture
    async def sample_user(self, session):
        """Create sample user for testing."""
        user = User(
            username="testuser",
            email="test@example.com",
            password="Test123!@#",
            first_name="Test",
            last_name="User"
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
    
    @pytest_asyncio.fixture
    async def admin_user(self, session):
        """Create admin user for testing."""
        user = User(
            username="admin",
            email="admin@example.com",
            password="Admin123!@#",
            first_name="Admin",
            last_name="User"
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
    
    @pytest_asyncio.fixture
    async def admin_token(self, admin_user):
        """Create admin token for testing."""
        token_data = {
            "sub": admin_user.email,
            "user_id": str(admin_user.id),
            "permissions": ["*"],
            "role": "admin"
        }
        return create_access_token(token_data)

    async def test_register_user_success(self, client: AsyncClient):
        """Test successful user registration."""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "NewUser123!@#"
        }
        
        response = await client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert data["is_active"] is True
        assert "password" not in data
        assert "password_hash" not in data
    
    async def test_register_user_duplicate_email(self, client: AsyncClient, sample_user):
        """Test registration with duplicate email."""
        user_data = {
            "username": "newuser",
            "email": "test@example.com",  # Same as sample_user
            "password": "NewUser123!@#"
        }
        
        response = await client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 409
        data = response.json()
        assert "already exists" in data["detail"].lower()
    
    async def test_register_user_invalid_data(self, client: AsyncClient):
        """Test registration with invalid data."""
        user_data = {
            "username": "nu",  # Too short
            "email": "invalid-email",
            "password": "weak"
        }
        
        response = await client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 422
    
    async def test_login_user_success(self, client: AsyncClient, sample_user):
        """Test successful user login."""
        login_data = {
            "username": "test@example.com",
            "password": "Test123!@#"
        }
        
        response = await client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0
    
    async def test_login_user_invalid_credentials(self, client: AsyncClient, sample_user):
        """Test login with invalid credentials."""
        login_data = {
            "username": "test@example.com",
            "password": "wrongpassword"
        }
        
        response = await client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "Invalid username or password" in data["detail"]
    
    async def test_login_user_not_found(self, client: AsyncClient):
        """Test login with non-existent user."""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "Test123!@#"
        }
        
        response = await client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "Invalid username or password" in data["detail"]
    
    async def test_get_current_user_success(self, client: AsyncClient, sample_user):
        """Test getting current user info."""
        # Create token for sample user
        token_data = {
            "sub": sample_user.email,
            "user_id": str(sample_user.id),
            "permissions": ["users:read"],
            "role": "user"
        }
        token = create_access_token(token_data)
        
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_user.id)
        assert data["username"] == sample_user.username
        assert data["email"] == sample_user.email
    
    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """Test getting current user without authentication."""
        response = await client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
    
    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        """Test getting current user with invalid token."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"}
        )
        
        assert response.status_code == 401
    
    async def test_refresh_token_success(self, client: AsyncClient, sample_user):
        """Test token refresh."""
        # Create refresh token
        token_data = {
            "sub": sample_user.email,
            "user_id": str(sample_user.id),
            "permissions": ["users:read"],
            "role": "user"
        }
        refresh_token = create_access_token(token_data, expires_delta=timedelta(days=7))
        
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    async def test_refresh_token_invalid(self, client: AsyncClient):
        """Test token refresh with invalid token."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid-token"}
        )
        
        assert response.status_code == 401
    
    async def test_change_password_success(self, client: AsyncClient, sample_user):
        """Test password change."""
        # Create token for sample user
        token_data = {
            "sub": sample_user.email,
            "user_id": str(sample_user.id),
            "permissions": ["users:update"],
            "role": "user"
        }
        token = create_access_token(token_data)
        
        password_data = {
            "current_password": "Test123!@#",
            "new_password": "NewPass123!@#"
        }
        
        response = await client.post(
            "/api/v1/auth/change-password",
            json=password_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Password changed successfully"
    
    async def test_change_password_invalid_current(self, client: AsyncClient, sample_user):
        """Test password change with invalid current password."""
        token_data = {
            "sub": sample_user.email,
            "user_id": str(sample_user.id),
            "permissions": ["users:update"],
            "role": "user"
        }
        token = create_access_token(token_data)
        
        password_data = {
            "current_password": "wrongpassword",
            "new_password": "NewPass123!@#"
        }
        
        response = await client.post(
            "/api/v1/auth/change-password",
            json=password_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 401
    
    async def test_list_users_success(self, client: AsyncClient, sample_user, admin_token):
        """Test listing users as admin."""
        response = await client.get(
            "/api/v1/auth/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(user["id"] == str(sample_user.id) for user in data)
    
    async def test_list_users_forbidden(self, client: AsyncClient, sample_user):
        """Test listing users without admin privileges."""
        token_data = {
            "sub": sample_user.email,
            "user_id": str(sample_user.id),
            "permissions": ["users:read"],
            "role": "user"
        }
        token = create_access_token(token_data)
        
        response = await client.get(
            "/api/v1/auth/users",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
    
    async def test_get_user_by_id_success(self, client: AsyncClient, sample_user, admin_token):
        """Test getting user by ID as admin."""
        response = await client.get(
            f"/api/v1/auth/users/{sample_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_user.id)
        assert data["username"] == sample_user.username
        assert data["email"] == sample_user.email
    
    async def test_get_user_by_id_not_found(self, client: AsyncClient, admin_token):
        """Test getting non-existent user by ID."""
        from uuid import uuid4
        
        response = await client.get(
            f"/api/v1/auth/users/{uuid4()}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 404
    
    async def test_update_user_success(self, client: AsyncClient, sample_user, admin_token):
        """Test updating user as admin."""
        update_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "phone_number": "+1234567890"
        }
        
        response = await client.put(
            f"/api/v1/auth/users/{sample_user.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "Name"
        assert data["phone_number"] == "+1234567890"
    
    async def test_activate_user_success(self, client: AsyncClient, sample_user, admin_token):
        """Test activating user as admin."""
        # First deactivate the user
        sample_user.is_active = False
        
        response = await client.post(
            f"/api/v1/auth/users/{sample_user.id}/activate",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True
    
    async def test_deactivate_user_success(self, client: AsyncClient, sample_user, admin_token):
        """Test deactivating user as admin."""
        response = await client.post(
            f"/api/v1/auth/users/{sample_user.id}/deactivate",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False
    
    async def test_create_role_success(self, client: AsyncClient, admin_token):
        """Test creating role as admin."""
        role_data = {
            "name": "editor",
            "description": "Editor role"
        }
        
        response = await client.post(
            "/api/v1/auth/roles",
            json=role_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "editor"
        assert data["description"] == "Editor role"
    
    async def test_list_roles_success(self, client: AsyncClient, admin_token):
        """Test listing roles as admin."""
        response = await client.get(
            "/api/v1/auth/roles",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    async def test_create_permission_success(self, client: AsyncClient, admin_token):
        """Test creating permission as admin."""
        permission_data = {
            "name": "users:delete",
            "resource": "users",
            "action": "delete",
            "description": "Delete users"
        }
        
        response = await client.post(
            "/api/v1/auth/permissions",
            json=permission_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "users:delete"
        assert data["resource"] == "users"
        assert data["action"] == "delete"
    
    async def test_list_permissions_success(self, client: AsyncClient, admin_token):
        """Test listing permissions as admin."""
        response = await client.get(
            "/api/v1/auth/permissions",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    async def test_user_statistics_success(self, client: AsyncClient, admin_token):
        """Test getting user statistics as admin."""
        response = await client.get(
            "/api/v1/auth/statistics",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "active_users" in data
        assert "inactive_users" in data
        assert isinstance(data["total_users"], int)
        assert isinstance(data["active_users"], int)
        assert isinstance(data["inactive_users"], int)
    
    async def test_logout_success(self, client: AsyncClient, sample_user):
        """Test user logout."""
        token_data = {
            "sub": sample_user.email,
            "user_id": str(sample_user.id),
            "permissions": ["users:read"],
            "role": "user"
        }
        token = create_access_token(token_data)
        
        response = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Successfully logged out"
    
    async def test_health_check(self, client: AsyncClient):
        """Test auth health check endpoint."""
        response = await client.get("/api/v1/auth/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "authentication"