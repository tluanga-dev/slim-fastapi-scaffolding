import pytest
import pytest_asyncio
from unittest.mock import patch
from datetime import datetime, timedelta
from uuid import uuid4

from app.modules.auth.models import User, Role, Permission, UserStatus, UserRole
from app.core.errors import ValidationError


@pytest.mark.unit
class TestUserModel:
    """Test User model functionality."""
    
    def test_user_creation_valid(self):
        """Test creating a user with valid data."""
        user = User(
            username="testuser",
            email="test@example.com",
            password="Test123!@#",
            first_name="Test",
            last_name="User"
        )
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.status == UserStatus.ACTIVE.value
        assert user.failed_login_attempts == "0"
        assert user.password_hash is not None
        assert user.password_hash != "Test123!@#"  # Should be hashed
    
    def test_user_creation_invalid_username(self):
        """Test user creation with invalid username."""
        with pytest.raises(ValueError, match="Username cannot be empty"):
            User(
                username="",
                email="test@example.com",
                password="Test123!@#",
                first_name="Test",
                last_name="User"
            )
    
    def test_user_creation_invalid_email(self):
        """Test user creation with invalid email."""
        with pytest.raises(ValueError, match="Invalid email format"):
            User(
                username="testuser",
                email="invalid-email",
                password="Test123!@#",
                first_name="Test",
                last_name="User"
            )
    
    def test_user_creation_weak_password(self):
        """Test user creation with weak password."""
        with pytest.raises(ValueError, match="Password must be at least 8 characters long"):
            User(
                username="testuser",
                email="test@example.com",
                password="weak",
                first_name="Test",
                last_name="User"
            )
    
    def test_password_verification(self):
        """Test password verification."""
        user = User(
            username="testuser",
            email="test@example.com",
            password="Test123!@#",
            first_name="Test",
            last_name="User"
        )
        
        assert user.verify_password("Test123!@#") is True
        assert user.verify_password("wrongpassword") is False
        assert user.verify_password("") is False
    
    def test_set_password(self):
        """Test setting new password."""
        user = User(
            username="testuser",
            email="test@example.com",
            password="Test123!@#",
            first_name="Test",
            last_name="User"
        )
        
        old_hash = user.password_hash
        user.set_password("NewPass123!@#", "admin")
        
        assert user.password_hash != old_hash
        assert user.verify_password("NewPass123!@#") is True
        assert user.verify_password("Test123!@#") is False
        assert user.password_reset_token is None
        assert user.password_reset_expires is None
        assert user.failed_login_attempts == "0"
        assert user.updated_by == "admin"
    
    def test_record_login(self):
        """Test recording successful login."""
        user = User(
            username="testuser",
            email="test@example.com",
            password="Test123!@#",
            first_name="Test",
            last_name="User"
        )
        
        user.failed_login_attempts = "3"
        user.record_login()
        
        assert user.last_login is not None
        assert user.failed_login_attempts == "0"
    
    def test_record_failed_login(self):
        """Test recording failed login attempts."""
        user = User(
            username="testuser",
            email="test@example.com",
            password="Test123!@#",
            first_name="Test",
            last_name="User"
        )
        
        # Record multiple failed attempts
        for i in range(3):
            user.record_failed_login()
            assert user.failed_login_attempts == str(i + 1)
            assert user.status == UserStatus.ACTIVE.value
        
        # 5th attempt should lock account
        user.record_failed_login()
        user.record_failed_login()
        assert user.failed_login_attempts == "5"
        assert user.status == UserStatus.LOCKED.value
    
    def test_unlock_account(self):
        """Test unlocking user account."""
        user = User(
            username="testuser",
            email="test@example.com",
            password="Test123!@#",
            first_name="Test",
            last_name="User"
        )
        
        user.status = UserStatus.LOCKED.value
        user.failed_login_attempts = "5"
        user.unlock_account("admin")
        
        assert user.status == UserStatus.ACTIVE.value
        assert user.failed_login_attempts == "0"
        assert user.updated_by == "admin"
    
    def test_activate_deactivate_suspend(self):
        """Test user status changes."""
        user = User(
            username="testuser",
            email="test@example.com",
            password="Test123!@#",
            first_name="Test",
            last_name="User"
        )
        
        # Test deactivate
        user.deactivate("admin")
        assert user.status == UserStatus.INACTIVE.value
        assert user.updated_by == "admin"
        
        # Test activate
        user.activate("admin")
        assert user.status == UserStatus.ACTIVE.value
        
        # Test suspend
        user.suspend("admin")
        assert user.status == UserStatus.SUSPENDED.value
    
    def test_password_reset_token(self):
        """Test password reset token management."""
        user = User(
            username="testuser",
            email="test@example.com",
            password="Test123!@#",
            first_name="Test",
            last_name="User"
        )
        
        token = "reset-token-123"
        expires = datetime.utcnow() + timedelta(hours=1)
        
        user.set_password_reset_token(token, expires)
        assert user.password_reset_token == token
        assert user.password_reset_expires == expires
        
        user.clear_password_reset_token()
        assert user.password_reset_token is None
        assert user.password_reset_expires is None
    
    def test_user_status_checks(self):
        """Test user status check methods."""
        user = User(
            username="testuser",
            email="test@example.com",
            password="Test123!@#",
            first_name="Test",
            last_name="User"
        )
        
        # Active user
        assert user.is_active_user() is True
        assert user.is_locked() is False
        assert user.is_suspended() is False
        assert user.can_login() is True
        
        # Locked user
        user.status = UserStatus.LOCKED.value
        assert user.is_active_user() is False
        assert user.is_locked() is True
        assert user.can_login() is False
        
        # Suspended user
        user.status = UserStatus.SUSPENDED.value
        assert user.is_suspended() is True
        assert user.can_login() is False
    
    def test_user_properties(self):
        """Test user property methods."""
        user = User(
            username="testuser",
            email="test@example.com",
            password="Test123!@#",
            first_name="Test",
            last_name="User"
        )
        
        assert user.full_name == "Test User"
        assert user.display_name == "Test User (testuser)"
        assert user.role_names == []  # No roles assigned yet
    
    def test_user_string_representations(self):
        """Test user string representations."""
        user = User(
            username="testuser",
            email="test@example.com",
            password="Test123!@#",
            first_name="Test",
            last_name="User"
        )
        user.id = uuid4()
        
        assert str(user) == "Test User (testuser)"
        assert "testuser" in repr(user)
        assert "test@example.com" in repr(user)


@pytest.mark.unit
class TestRoleModel:
    """Test Role model functionality."""
    
    def test_role_creation_valid(self):
        """Test creating a role with valid data."""
        role = Role(
            name="admin",
            description="Administrator role",
            is_system_role=True
        )
        
        assert role.name == "admin"
        assert role.description == "Administrator role"
        assert role.is_system_role is True
    
    def test_role_creation_invalid_name(self):
        """Test role creation with invalid name."""
        with pytest.raises(ValueError, match="Role name cannot be empty"):
            Role(name="", description="Test role")
    
    def test_role_creation_long_name(self):
        """Test role creation with too long name."""
        with pytest.raises(ValueError, match="Role name cannot exceed 50 characters"):
            Role(name="a" * 51, description="Test role")
    
    def test_role_can_delete(self):
        """Test role deletion rules."""
        # System role cannot be deleted
        system_role = Role(name="admin", is_system_role=True)
        assert system_role.can_delete() is False
        
        # Regular role can be deleted if no users
        regular_role = Role(name="user", is_system_role=False)
        assert regular_role.can_delete() is True
    
    def test_role_properties(self):
        """Test role property methods."""
        role = Role(name="test")
        
        assert role.user_count == 0
        assert role.permission_count == 0
    
    def test_role_string_representations(self):
        """Test role string representations."""
        role = Role(name="admin", description="Admin role")
        role.id = uuid4()
        
        assert str(role) == "admin"
        assert "admin" in repr(role)


@pytest.mark.unit
class TestPermissionModel:
    """Test Permission model functionality."""
    
    def test_permission_creation_valid(self):
        """Test creating a permission with valid data."""
        permission = Permission(
            name="users:read",
            resource="users",
            action="read",
            description="Read users",
            is_system_permission=True
        )
        
        assert permission.name == "users:read"
        assert permission.resource == "users"
        assert permission.action == "read"
        assert permission.description == "Read users"
        assert permission.is_system_permission is True
    
    def test_permission_creation_invalid_name(self):
        """Test permission creation with invalid name."""
        with pytest.raises(ValueError, match="Permission name cannot be empty"):
            Permission(name="", resource="users", action="read")
    
    def test_permission_creation_invalid_resource(self):
        """Test permission creation with invalid resource."""
        with pytest.raises(ValueError, match="Resource cannot be empty"):
            Permission(name="test", resource="", action="read")
    
    def test_permission_creation_invalid_action(self):
        """Test permission creation with invalid action."""
        with pytest.raises(ValueError, match="Action cannot be empty"):
            Permission(name="test", resource="users", action="")
    
    def test_permission_can_delete(self):
        """Test permission deletion rules."""
        # System permission cannot be deleted
        system_perm = Permission(
            name="users:read",
            resource="users",
            action="read",
            is_system_permission=True
        )
        assert system_perm.can_delete() is False
        
        # Regular permission can be deleted if no roles
        regular_perm = Permission(
            name="custom:read",
            resource="custom",
            action="read",
            is_system_permission=False
        )
        assert regular_perm.can_delete() is True
    
    def test_permission_properties(self):
        """Test permission property methods."""
        permission = Permission(
            name="users:read",
            resource="users", 
            action="read"
        )
        
        assert permission.role_count == 0
    
    def test_permission_string_representations(self):
        """Test permission string representations."""
        permission = Permission(
            name="users:read",
            resource="users",
            action="read"
        )
        permission.id = uuid4()
        
        assert str(permission) == "users:read"
        assert "users:read" in repr(permission)
        assert "users" in repr(permission)
        assert "read" in repr(permission)