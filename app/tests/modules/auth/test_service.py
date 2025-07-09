import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from uuid import uuid4

from app.modules.auth.service import AuthService
from app.modules.auth.models import User, Role, Permission, UserStatus
from app.modules.auth.schemas import UserRegister, UserLogin, TokenResponse, UserResponse
from app.core.errors import AuthenticationError, ValidationError, ConflictError, NotFoundError
from app.core.security import verify_password


@pytest.mark.unit
class TestAuthService:
    """Test AuthService functionality."""
    
    @pytest_asyncio.fixture
    async def auth_service(self, session):
        """Create AuthService instance."""
        return AuthService(session)
    
    @pytest_asyncio.fixture
    async def sample_user(self, session):
        """Create sample user in database."""
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
    async def sample_role(self, session):
        """Create sample role in database."""
        role = Role(
            name="user",
            description="Regular user role"
        )
        session.add(role)
        await session.commit()
        await session.refresh(role)
        return role
    
    @pytest_asyncio.fixture
    async def sample_permission(self, session):
        """Create sample permission in database."""
        permission = Permission(
            name="users:read",
            resource="users",
            action="read",
            description="Read users"
        )
        session.add(permission)
        await session.commit()
        await session.refresh(permission)
        return permission

    async def test_register_user_success(self, auth_service, session):
        """Test successful user registration."""
        user_data = UserRegister(
            username="newuser",
            email="newuser@example.com",
            password="NewUser123!@#"
        )
        
        result = await auth_service.register_user(user_data)
        
        assert isinstance(result, UserResponse)
        assert result.username == "newuser"
        assert result.email == "newuser@example.com"
        assert result.first_name == "newuser"  # Default from username
        assert result.last_name == "newuser"   # Default from username
        assert result.is_active is True
        
        # Verify user was created in database
        from sqlalchemy import select
        db_user = await session.execute(select(User).where(User.email == "newuser@example.com"))
        user = db_user.scalar_one_or_none()
        assert user is not None
        assert user.verify_password("NewUser123!@#") is True
    
    async def test_register_user_duplicate_email(self, auth_service, sample_user):
        """Test user registration with duplicate email."""
        user_data = UserRegister(
            username="newuser",
            email="test@example.com",  # Same as sample_user
            password="NewUser123!@#"
        )
        
        with pytest.raises(ConflictError, match="User with email"):
            await auth_service.register_user(user_data)
    
    async def test_register_user_duplicate_username(self, auth_service, sample_user):
        """Test user registration with duplicate username."""
        user_data = UserRegister(
            username="testuser",  # Same as sample_user
            email="newuser@example.com",
            password="NewUser123!@#"
        )
        
        with pytest.raises(ConflictError, match="User with username"):
            await auth_service.register_user(user_data)
    
    async def test_login_user_success(self, auth_service, sample_user):
        """Test successful user login."""
        login_data = UserLogin(
            username="test@example.com",
            password="Test123!@#"
        )
        
        result = await auth_service.login_user(login_data)
        
        assert isinstance(result, TokenResponse)
        assert result.access_token is not None
        assert result.refresh_token is not None
        assert result.token_type == "bearer"
        assert result.expires_in > 0
        
        # Verify last login was updated
        await auth_service.session.refresh(sample_user)
        assert sample_user.last_login is not None
        assert sample_user.failed_login_attempts == "0"
    
    async def test_login_user_invalid_credentials(self, auth_service, sample_user):
        """Test login with invalid credentials."""
        login_data = UserLogin(
            username="test@example.com",
            password="wrongpassword"
        )
        
        with pytest.raises(AuthenticationError, match="Invalid username or password"):
            await auth_service.login_user(login_data)
        
        # Verify failed login was recorded
        await auth_service.session.refresh(sample_user)
        assert sample_user.failed_login_attempts == "1"
    
    async def test_login_user_not_found(self, auth_service):
        """Test login with non-existent user."""
        login_data = UserLogin(
            username="nonexistent@example.com",
            password="Test123!@#"
        )
        
        with pytest.raises(AuthenticationError, match="Invalid username or password"):
            await auth_service.login_user(login_data)
    
    async def test_login_user_inactive(self, auth_service, sample_user):
        """Test login with inactive user."""
        sample_user.is_active = False
        await auth_service.session.commit()
        
        login_data = UserLogin(
            username="test@example.com",
            password="Test123!@#"
        )
        
        with pytest.raises(AuthenticationError, match="User account is inactive"):
            await auth_service.login_user(login_data)
    
    async def test_login_user_locked(self, auth_service, sample_user):
        """Test login with locked user."""
        sample_user.status = UserStatus.LOCKED.value
        await auth_service.session.commit()
        
        login_data = UserLogin(
            username="test@example.com",
            password="Test123!@#"
        )
        
        with pytest.raises(AuthenticationError, match="User account is locked"):
            await auth_service.login_user(login_data)
    
    async def test_get_user_success(self, auth_service, sample_user):
        """Test getting user by ID."""
        result = await auth_service.get_user(sample_user.id)
        
        assert isinstance(result, UserResponse)
        assert result.id == sample_user.id
        assert result.username == sample_user.username
        assert result.email == sample_user.email
    
    async def test_get_user_not_found(self, auth_service):
        """Test getting non-existent user."""
        result = await auth_service.get_user(uuid4())
        assert result is None
    
    async def test_get_user_by_email_success(self, auth_service, sample_user):
        """Test getting user by email."""
        result = await auth_service.get_user_by_email(sample_user.email)
        
        assert isinstance(result, UserResponse)
        assert result.email == sample_user.email
    
    async def test_get_user_by_email_not_found(self, auth_service):
        """Test getting non-existent user by email."""
        result = await auth_service.get_user_by_email("nonexistent@example.com")
        assert result is None
    
    async def test_get_user_by_username_success(self, auth_service, sample_user):
        """Test getting user by username."""
        result = await auth_service.get_user_by_username(sample_user.username)
        
        assert isinstance(result, UserResponse)
        assert result.username == sample_user.username
    
    async def test_get_user_by_username_not_found(self, auth_service):
        """Test getting non-existent user by username."""
        result = await auth_service.get_user_by_username("nonexistent")
        assert result is None
    
    async def test_update_user_success(self, auth_service, sample_user):
        """Test updating user information."""
        from app.modules.auth.schemas import UserUpdate
        
        update_data = UserUpdate(
            first_name="Updated",
            last_name="Name",
            phone_number="+1234567890"
        )
        
        result = await auth_service.update_user(sample_user.id, update_data)
        
        assert isinstance(result, UserResponse)
        assert result.first_name == "Updated"
        assert result.last_name == "Name"
        assert result.phone_number == "+1234567890"
    
    async def test_update_user_not_found(self, auth_service):
        """Test updating non-existent user."""
        from app.modules.auth.schemas import UserUpdate
        
        update_data = UserUpdate(first_name="Updated")
        
        with pytest.raises(NotFoundError, match="User not found"):
            await auth_service.update_user(uuid4(), update_data)
    
    async def test_change_password_success(self, auth_service, sample_user):
        """Test changing user password."""
        from app.modules.auth.schemas import PasswordChange
        
        password_data = PasswordChange(
            current_password="Test123!@#",
            new_password="NewPass123!@#"
        )
        
        result = await auth_service.change_password(sample_user.id, password_data)
        
        assert result is True
        
        # Verify password was changed
        await auth_service.session.refresh(sample_user)
        assert sample_user.verify_password("NewPass123!@#") is True
        assert sample_user.verify_password("Test123!@#") is False
    
    async def test_change_password_invalid_current(self, auth_service, sample_user):
        """Test changing password with invalid current password."""
        from app.modules.auth.schemas import PasswordChange
        
        password_data = PasswordChange(
            current_password="wrongpassword",
            new_password="NewPass123!@#"
        )
        
        with pytest.raises(AuthenticationError, match="Current password is incorrect"):
            await auth_service.change_password(sample_user.id, password_data)
    
    async def test_activate_user_success(self, auth_service, sample_user):
        """Test activating user."""
        sample_user.is_active = False
        await auth_service.session.commit()
        
        result = await auth_service.activate_user(sample_user.id)
        
        assert isinstance(result, UserResponse)
        assert result.is_active is True
    
    async def test_deactivate_user_success(self, auth_service, sample_user):
        """Test deactivating user."""
        result = await auth_service.deactivate_user(sample_user.id)
        
        assert isinstance(result, UserResponse)
        assert result.is_active is False
    
    async def test_create_role_success(self, auth_service):
        """Test creating a new role."""
        from app.modules.auth.schemas import RoleCreate
        
        role_data = RoleCreate(
            name="editor",
            description="Editor role"
        )
        
        result = await auth_service.create_role(role_data)
        
        assert isinstance(result, dict)  # RoleResponse
        assert result["name"] == "editor"
        assert result["description"] == "Editor role"
    
    async def test_create_role_duplicate_name(self, auth_service, sample_role):
        """Test creating role with duplicate name."""
        from app.modules.auth.schemas import RoleCreate
        
        role_data = RoleCreate(
            name="user",  # Same as sample_role
            description="Duplicate role"
        )
        
        with pytest.raises(ConflictError, match="Role with name"):
            await auth_service.create_role(role_data)
    
    async def test_create_permission_success(self, auth_service):
        """Test creating a new permission."""
        from app.modules.auth.schemas import PermissionCreate
        
        permission_data = PermissionCreate(
            name="users:write",
            resource="users",
            action="write",
            description="Write users"
        )
        
        result = await auth_service.create_permission(permission_data)
        
        assert isinstance(result, dict)  # PermissionResponse
        assert result["name"] == "users:write"
        assert result["resource"] == "users"
        assert result["action"] == "write"
    
    async def test_create_permission_duplicate_name(self, auth_service, sample_permission):
        """Test creating permission with duplicate name."""
        from app.modules.auth.schemas import PermissionCreate
        
        permission_data = PermissionCreate(
            name="users:read",  # Same as sample_permission
            resource="users",
            action="read",
            description="Duplicate permission"
        )
        
        with pytest.raises(ConflictError, match="Permission with name"):
            await auth_service.create_permission(permission_data)
    
    async def test_assign_role_to_user_success(self, auth_service, sample_user, sample_role):
        """Test assigning role to user."""
        result = await auth_service.assign_role_to_user(sample_user.id, sample_role.id)
        
        assert result is True
        
        # Verify role was assigned
        await auth_service.session.refresh(sample_user)
        assert len(sample_user.roles) == 1
        assert sample_user.roles[0].id == sample_role.id
    
    async def test_assign_role_to_user_already_assigned(self, auth_service, sample_user, sample_role):
        """Test assigning role that's already assigned."""
        # First assignment
        await auth_service.assign_role_to_user(sample_user.id, sample_role.id)
        
        # Second assignment should not cause error
        result = await auth_service.assign_role_to_user(sample_user.id, sample_role.id)
        assert result is True
        
        # Verify only one role assignment
        await auth_service.session.refresh(sample_user)
        assert len(sample_user.roles) == 1
    
    async def test_remove_role_from_user_success(self, auth_service, sample_user, sample_role):
        """Test removing role from user."""
        # First assign the role
        await auth_service.assign_role_to_user(sample_user.id, sample_role.id)
        
        # Then remove it
        result = await auth_service.remove_role_from_user(sample_user.id, sample_role.id)
        
        assert result is True
        
        # Verify role was removed
        await auth_service.session.refresh(sample_user)
        assert len(sample_user.roles) == 0
    
    async def test_assign_permission_to_role_success(self, auth_service, sample_role, sample_permission):
        """Test assigning permission to role."""
        result = await auth_service.assign_permission_to_role(sample_role.id, sample_permission.id)
        
        assert result is True
        
        # Verify permission was assigned
        await auth_service.session.refresh(sample_role)
        assert len(sample_role.permissions) == 1
        assert sample_role.permissions[0].id == sample_permission.id
    
    async def test_list_users_success(self, auth_service, sample_user):
        """Test listing users."""
        result = await auth_service.list_users()
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].id == sample_user.id
    
    async def test_list_users_with_pagination(self, auth_service, sample_user):
        """Test listing users with pagination."""
        result = await auth_service.list_users(skip=0, limit=10)
        
        assert isinstance(result, list)
        assert len(result) == 1
    
    async def test_list_roles_success(self, auth_service, sample_role):
        """Test listing roles."""
        result = await auth_service.list_roles()
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["id"] == str(sample_role.id)
    
    async def test_list_permissions_success(self, auth_service, sample_permission):
        """Test listing permissions."""
        result = await auth_service.list_permissions()
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["id"] == str(sample_permission.id)
    
    async def test_get_user_statistics(self, auth_service, sample_user):
        """Test getting user statistics."""
        result = await auth_service.get_user_statistics()
        
        assert isinstance(result, dict)
        assert "total_users" in result
        assert "active_users" in result
        assert "inactive_users" in result
        assert result["total_users"] == 1
        assert result["active_users"] == 1
        assert result["inactive_users"] == 0