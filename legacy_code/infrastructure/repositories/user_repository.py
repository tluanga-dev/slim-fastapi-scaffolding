from typing import Optional, Set
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.domain.value_objects.user_type import UserType
from src.domain.repositories.user_repository import UserRepository
from src.infrastructure.models.auth_models import UserModel, UserPermissionModel
from src.infrastructure.repositories.base import SQLAlchemyRepository


class UserRepositoryImpl(SQLAlchemyRepository[User, UserModel], UserRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, UserModel, User)

    def _to_entity(self, model: UserModel) -> User:
        # Don't access relationships unless they're already loaded
        direct_permissions = set()
        
        # Convert role if it's loaded (not a lazy attribute)
        role = None
        if model.role is not None:
            from src.domain.entities.role import Role, Permission
            
            # Convert role permissions
            role_permissions = []
            if hasattr(model.role, 'permissions') and model.role.permissions:
                for perm_model in model.role.permissions:
                    permission = Permission(
                        id=perm_model.id,
                        code=perm_model.code,
                        name=perm_model.name,
                        description=perm_model.description,
                        created_at=perm_model.created_at,
                        updated_at=perm_model.updated_at,
                        is_active=perm_model.is_active,
                        created_by=perm_model.created_by,
                        updated_by=perm_model.updated_by,
                    )
                    role_permissions.append(permission)
            
            role = Role(
                id=model.role.id,
                name=model.role.name,
                description=model.role.description,
                permissions=role_permissions,
                created_at=model.role.created_at,
                updated_at=model.role.updated_at,
                is_active=model.role.is_active,
                created_by=model.role.created_by,
                updated_by=model.role.updated_by,
            )
        
        return User(
            id=model.id,
            email=Email(model.email),
            name=model.name,
            hashed_password=model.hashed_password,
            user_type=UserType(model.user_type) if model.user_type else UserType.USER,
            role=role,
            role_id=model.role_id,
            is_superuser=model.is_superuser,
            first_name=model.first_name,
            last_name=model.last_name,
            username=model.username,
            location_id=model.location_id,
            last_login=model.last_login,
            direct_permissions=direct_permissions,
            created_at=model.created_at,
            updated_at=model.updated_at,
            is_active=model.is_active,
            created_by=model.created_by,
            updated_by=model.updated_by,
        )

    def _to_model(self, entity: User) -> UserModel:
        return UserModel(
            id=entity.id,
            email=entity.email.value,
            name=entity.name,
            hashed_password=entity.hashed_password,
            user_type=entity.user_type.value,
            is_superuser=entity.is_superuser,
            first_name=entity.first_name,
            last_name=entity.last_name,
            username=entity.username,
            location_id=entity.location_id,
            last_login=entity.last_login,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            is_active=entity.is_active,
            created_by=entity.created_by,
            updated_by=entity.updated_by,
        )

    async def get_by_email(self, email: Email) -> Optional[User]:
        from src.infrastructure.models.auth_models import RoleModel
        query = select(UserModel).options(
            selectinload(UserModel.role).selectinload(RoleModel.permissions)
        ).filter(UserModel.email == email.value)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
    
    async def add_direct_permission(self, user_id: str, permission_code: str, granted_by: str, reason: Optional[str] = None) -> None:
        """Add a direct permission to a user."""
        from datetime import datetime
        
        permission = UserPermissionModel(
            user_id=user_id,
            permission_code=permission_code,
            granted_by=granted_by,
            granted_at=datetime.utcnow(),
            reason=reason,
            is_active=True
        )
        self.session.add(permission)
        await self.session.commit()
    
    async def remove_direct_permission(self, user_id: str, permission_code: str) -> None:
        """Remove a direct permission from a user."""
        query = select(UserPermissionModel).filter(
            UserPermissionModel.user_id == user_id,
            UserPermissionModel.permission_code == permission_code,
            UserPermissionModel.is_active == True
        )
        result = await self.session.execute(query)
        permission = result.scalar_one_or_none()
        
        if permission:
            permission.is_active = False
            await self.session.commit()
    
    async def get_user_direct_permissions(self, user_id: str) -> Set[str]:
        """Get all direct permissions for a user."""
        query = select(UserPermissionModel).filter(
            UserPermissionModel.user_id == user_id,
            UserPermissionModel.is_active == True
        )
        result = await self.session.execute(query)
        permissions = result.scalars().all()
        return {perm.permission_code for perm in permissions}