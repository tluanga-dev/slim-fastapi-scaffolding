from typing import Optional, Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.db.session import get_session
from app.core.security import decode_access_token, TokenData
from app.core.config import settings
from app.core.errors import AuthenticationException, AuthorizationException


# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False
)


# Database dependency
AsyncSessionDep = Annotated[AsyncSession, Depends(get_session)]


# Token dependencies
async def get_current_token(
    token: Optional[str] = Depends(oauth2_scheme)
) -> Optional[str]:
    """
    Get current token from request.
    Returns None if no token present (for optional auth).
    """
    return token


async def get_current_user_data(
    token: str = Depends(oauth2_scheme)
) -> TokenData:
    """
    Get current user data from token.
    Raises exception if token is invalid.
    """
    if not token:
        raise AuthenticationException("Not authenticated")
    
    try:
        token_data = decode_access_token(token)
        return token_data
    except Exception:
        raise AuthenticationException("Invalid authentication credentials")


async def get_current_active_user(
    session: AsyncSessionDep,
    token_data: TokenData = Depends(get_current_user_data)
):
    """
    Get current active user from database.
    """
    from app.modules.auth.models import User
    
    if not token_data.user_id:
        raise AuthenticationException("Invalid user token")
    
    # Fetch user from database
    user = await session.get(User, UUID(token_data.user_id))
    if not user or not user.is_active:
        raise AuthenticationException("User not found or inactive")
    
    return user


async def get_optional_current_user(
    token: Optional[str] = Depends(get_current_token),
    session: AsyncSessionDep = None
) -> Optional[TokenData]:
    """
    Get current user if authenticated, None otherwise.
    Used for endpoints that support both authenticated and anonymous access.
    """
    if not token:
        return None
    
    try:
        token_data = decode_access_token(token)
        return token_data
    except Exception:
        return None


# Permission checker
class PermissionChecker:
    """
    Dependency class for checking permissions.
    
    Usage:
        ```python
        @router.get("/admin", dependencies=[Depends(PermissionChecker("admin:read"))])
        async def admin_endpoint():
            pass
        ```
    """
    
    def __init__(self, required_permissions: str | list[str]):
        self.required_permissions = (
            [required_permissions] if isinstance(required_permissions, str) 
            else required_permissions
        )
    
    async def __call__(
        self,
        current_user: TokenData = Depends(get_current_user_data)
    ) -> TokenData:
        """Check if user has required permissions."""
        user_permissions = set(current_user.permissions)
        required = set(self.required_permissions)
        
        if not required.issubset(user_permissions):
            missing = required - user_permissions
            raise AuthorizationException(
                f"Missing required permissions: {', '.join(missing)}"
            )
        
        return current_user


# Role checker
class RoleChecker:
    """
    Dependency class for checking roles.
    
    Usage:
        ```python
        @router.get("/manager", dependencies=[Depends(RoleChecker(["manager", "admin"]))])
        async def manager_endpoint():
            pass
        ```
    """
    
    def __init__(self, allowed_roles: str | list[str]):
        self.allowed_roles = (
            [allowed_roles] if isinstance(allowed_roles, str) 
            else allowed_roles
        )
    
    async def __call__(
        self,
        current_user: TokenData = Depends(get_current_user_data)
    ) -> TokenData:
        """Check if user has allowed role."""
        if current_user.role not in self.allowed_roles:
            raise AuthorizationException(
                f"Role '{current_user.role}' not allowed. "
                f"Required roles: {', '.join(self.allowed_roles)}"
            )
        
        return current_user


# Common query parameters
class CommonQueryParams(BaseModel):
    """Common query parameters for list endpoints."""
    
    skip: int = Query(0, ge=0, description="Number of records to skip")
    limit: int = Query(
        settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description="Number of records to return"
    )
    sort_by: Optional[str] = Query(None, description="Field to sort by")
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order")
    search: Optional[str] = Query(None, description="Search term")
    is_active: Optional[bool] = Query(None, description="Filter by active status")


class PaginationParams(BaseModel):
    """Pagination parameters."""
    
    page: int = Query(1, ge=1, description="Page number")
    page_size: int = Query(
        settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description="Items per page"
    )
    
    @property
    def skip(self) -> int:
        """Calculate skip value from page number."""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Get limit value."""
        return self.page_size


# Repository dependencies
# These will be implemented as modules are created


async def get_brand_repository(session: AsyncSessionDep):
    """Get brand repository instance."""
    from app.modules.master_data.brands.repository import BrandRepository
    return BrandRepository(session)


async def get_category_repository(session: AsyncSessionDep):
    """Get category repository instance."""
    from app.modules.master_data.categories.repository import CategoryRepository
    return CategoryRepository(session)


# Service dependencies
# These will be implemented as modules are created
async def get_auth_service(
    session: AsyncSessionDep
):
    """Get auth service instance."""
    from app.modules.auth.service import AuthService
    return AuthService(session)


async def get_customer_service(
    session: AsyncSessionDep
):
    """Get customer service instance."""
    from app.modules.customers.service import CustomerService
    return CustomerService(session)


async def get_supplier_service(
    session: AsyncSessionDep
):
    """Get supplier service instance."""
    from app.modules.suppliers.service import SupplierService
    return SupplierService(session)


async def get_inventory_service(
    session: AsyncSessionDep
):
    """Get inventory service instance."""
    from app.modules.inventory.service import InventoryService
    return InventoryService(session)


async def get_transaction_service(
    session: AsyncSessionDep
):
    """Get transaction service instance."""
    from app.modules.transactions.service import TransactionService
    return TransactionService(session)


async def get_location_service(
    session: AsyncSessionDep
):
    """Get location service instance."""
    from app.modules.master_data.locations.service import LocationService
    return LocationService(session)




async def get_brand_service(
    brand_repo = Depends(get_brand_repository)
):
    """Get brand service instance."""
    from app.modules.master_data.brands.service import BrandService
    return BrandService(brand_repo)


async def get_category_service(
    category_repo = Depends(get_category_repository)
):
    """Get category service instance."""
    from app.modules.master_data.categories.service import CategoryService
    return CategoryService(category_repo)


async def get_rental_service(
    session: AsyncSessionDep
):
    """Get rental service instance."""
    from app.modules.rentals.service import RentalService
    return RentalService(session)


async def get_analytics_service(
    session: AsyncSessionDep
):
    """Get analytics service instance."""
    from app.modules.analytics.service import AnalyticsService
    return AnalyticsService(session)


async def get_system_service(
    session: AsyncSessionDep
):
    """Get system service instance."""
    from app.modules.system.service import SystemService
    return SystemService(session)


async def get_auth_repository(session: AsyncSessionDep):
    """Get auth repository instance."""
    from app.modules.auth.repository import AuthRepository
    return AuthRepository(session)


async def get_customer_repository(session: AsyncSessionDep):
    """Get customer repository instance."""
    from app.modules.customers.repository import CustomerRepository
    return CustomerRepository(session)


async def get_supplier_repository(session: AsyncSessionDep):
    """Get supplier repository instance."""
    from app.modules.suppliers.repository import SupplierRepository
    return SupplierRepository(session)


async def get_inventory_repository(session: AsyncSessionDep):
    """Get inventory repository instance."""
    from app.modules.inventory.repository import InventoryRepository
    return InventoryRepository(session)


async def get_transaction_repository(session: AsyncSessionDep):
    """Get transaction repository instance."""
    from app.modules.transactions.repository import TransactionRepository
    return TransactionRepository(session)


async def get_rental_repository(session: AsyncSessionDep):
    """Get rental repository instance."""
    from app.modules.rentals.repository import RentalRepository
    return RentalRepository(session)


async def get_location_repository(session: AsyncSessionDep):
    """Get location repository instance."""
    from app.modules.master_data.locations.repository import LocationRepository
    return LocationRepository(session)


# API Key dependency (for external integrations)
async def get_api_key(
    api_key: str = Query(..., description="API Key for authentication")
) -> str:
    """
    Validate API key from query parameter.
    """
    # TODO: Implement API key validation
    # This would check against stored API keys in database
    if not api_key:
        raise AuthenticationException("API key required")
    
    # Temporary validation
    if api_key != "test-api-key":
        raise AuthenticationException("Invalid API key")
    
    return api_key


# Request ID dependency (for request tracking)
async def get_request_id() -> str:
    """
    Generate unique request ID for tracking.
    """
    import uuid
    return str(uuid.uuid4())


# Export commonly used dependencies
__all__ = [
    "AsyncSessionDep",
    "get_current_token",
    "get_current_user_data",
    "get_current_active_user",
    "get_optional_current_user",
    "PermissionChecker",
    "RoleChecker",
    "CommonQueryParams",
    "PaginationParams",
    "get_api_key",
    "get_request_id",
    "get_auth_service",
    "get_customer_service",
    "get_supplier_service",
    "get_inventory_service",
    "get_transaction_service",
    "get_rental_service",
    "get_analytics_service",
    "get_system_service",
    "get_brand_service",
    "get_category_service",
    "get_location_service",
]