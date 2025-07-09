"""
Seed script for RBAC data - creates default permissions, categories, and roles.
Run this script after running migrations to populate the database with default RBAC data.
"""

import asyncio
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.core.config import settings
from src.infrastructure.models.auth_models import (
    PermissionCategoryModel,
    PermissionModel,
    RoleModel,
    PermissionDependencyModel,
    UserModel,
    role_permission_association
)
from src.domain.constants.permissions import (
    PermissionCategory,
    Permission,
    RoleTemplate,
    PERMISSION_METADATA,
    PERMISSION_DEPENDENCIES,
    ROLE_TEMPLATE_PERMISSIONS,
    get_permission_category
)
from src.domain.value_objects.user_type import UserType
from src.domain.value_objects.email import Email
from src.core.security import get_password_hash

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RBACSeeder:
    """Seeder for RBAC data."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def seed_all(self):
        """Seed all RBAC data."""
        logger.info("Starting RBAC data seeding...")
        
        try:
            await self.seed_permission_categories()
            await self.seed_permissions()
            await self.seed_permission_dependencies()
            await self.seed_roles()
            await self.seed_default_users()
            
            logger.info("RBAC data seeding completed successfully!")
            
        except Exception as e:
            logger.error(f"Error during seeding: {e}")
            await self.session.rollback()
            raise
    
    async def seed_permission_categories(self):
        """Create permission categories."""
        logger.info("Seeding permission categories...")
        
        category_data = [
            (PermissionCategory.SYSTEM, "System Administration", "System-level administration and configuration", 1),
            (PermissionCategory.USER_MANAGEMENT, "User Management", "User account and profile management", 2),
            (PermissionCategory.ROLE_MANAGEMENT, "Role Management", "Role and permission management", 3),
            (PermissionCategory.CUSTOMER, "Customer Management", "Customer account and relationship management", 4),
            (PermissionCategory.INVENTORY, "Inventory Management", "Inventory tracking and management", 5),
            (PermissionCategory.PRODUCT, "Product Management", "Product, SKU, and category management", 6),
            (PermissionCategory.SALES, "Sales Management", "Sales transaction management", 7),
            (PermissionCategory.RENTAL, "Rental Management", "Rental transaction and lifecycle management", 8),
            (PermissionCategory.PURCHASE, "Purchase Management", "Purchase and supplier management", 9),
            (PermissionCategory.RETURNS, "Returns Management", "Return processing and management", 10),
            (PermissionCategory.INSPECTION, "Inspection Management", "Quality control and inspection", 11),
            (PermissionCategory.FINANCE, "Financial Management", "Financial transactions and reporting", 12),
            (PermissionCategory.REPORTS, "Reports & Analytics", "Reporting and business intelligence", 13),
            (PermissionCategory.SETTINGS, "Settings", "System and application settings", 14),
            (PermissionCategory.AUDIT, "Audit & Compliance", "Audit logs and compliance features", 15),
        ]
        
        for code, name, description, display_order in category_data:
            # Check if category already exists
            from sqlalchemy import select
            query = select(PermissionCategoryModel).filter(PermissionCategoryModel.code == code.value)
            result = await self.session.execute(query)
            existing = result.scalar_one_or_none()
            if not existing:
                category = PermissionCategoryModel(
                    code=code.value,
                    name=name,
                    description=description,
                    display_order=display_order,
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                self.session.add(category)
        
        await self.session.commit()
        logger.info(f"Created {len(category_data)} permission categories")
    
    async def seed_permissions(self):
        """Create permissions."""
        logger.info("Seeding permissions...")
        
        created_count = 0
        
        for permission_enum in Permission:
            # Check if permission already exists
            from sqlalchemy import select
            query = select(PermissionModel).filter(PermissionModel.code == permission_enum.value)
            result = await self.session.execute(query)
            existing = result.scalar_one_or_none()
            
            if not existing:
                # Get metadata
                metadata = PERMISSION_METADATA.get(permission_enum, {})
                category = get_permission_category(permission_enum)
                
                # Get category ID
                category_query = select(PermissionCategoryModel).filter(
                    PermissionCategoryModel.code == category.value
                )
                category_result = await self.session.execute(category_query)
                category_model = category_result.scalar_one_or_none()
                category_id = category_model.id if category_model else None
                
                # Create permission name from enum
                permission_name = permission_enum.value.replace('_', ' ').title()
                
                permission = PermissionModel(
                    code=permission_enum.value,
                    name=permission_name,
                    description=metadata.get('description', f"Permission for {permission_name.lower()}"),
                    category_id=category_id,
                    risk_level=metadata.get('risk_level', 'LOW'),
                    requires_approval=metadata.get('requires_approval', False),
                    permission_metadata=metadata,
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                self.session.add(permission)
                created_count += 1
        
        await self.session.commit()
        logger.info(f"Created {created_count} permissions")
    
    async def seed_permission_dependencies(self):
        """Create permission dependencies."""
        logger.info("Seeding permission dependencies...")
        
        created_count = 0
        
        for permission, dependencies in PERMISSION_DEPENDENCIES.items():
            for dependency in dependencies:
                # Check if dependency already exists
                from sqlalchemy import select
                query = select(PermissionDependencyModel).filter(
                    PermissionDependencyModel.permission_code == permission.value,
                    PermissionDependencyModel.depends_on_code == dependency.value
                )
                result = await self.session.execute(query)
                existing = result.scalar_one_or_none()
                
                if not existing:
                    dep = PermissionDependencyModel(
                        permission_code=permission.value,
                        depends_on_code=dependency.value,
                        created_at=datetime.utcnow()
                    )
                    self.session.add(dep)
                    created_count += 1
        
        await self.session.commit()
        logger.info(f"Created {created_count} permission dependencies")
    
    async def seed_roles(self):
        """Create default roles."""
        logger.info("Seeding roles...")
        
        created_count = 0
        
        for template in RoleTemplate:
            # Check if role already exists
            from sqlalchemy import select
            query = select(RoleModel).filter(RoleModel.name == template.value)
            result = await self.session.execute(query)
            existing = result.scalar_one_or_none()
            
            if not existing:
                # Create role
                role_descriptions = {
                    RoleTemplate.SUPERADMIN: "System superadmin with full access to all features",
                    RoleTemplate.ADMIN: "Administrator with broad access to manage users and system",
                    RoleTemplate.MANAGER: "Manager with access to operational features and reporting", 
                    RoleTemplate.STAFF: "Staff member with access to daily operational features",
                    RoleTemplate.CUSTOMER: "External customer with limited portal access",
                    RoleTemplate.AUDITOR: "Auditor with read-only access to financial and audit data",
                    RoleTemplate.ACCOUNTANT: "Accountant with access to financial management features",
                }
                
                role = RoleModel(
                    name=template.value,
                    description=role_descriptions.get(template, f"Default {template.value} role"),
                    template=template.value,
                    is_system=True,
                    can_be_deleted=False,
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                self.session.add(role)
                await self.session.commit()
                await self.session.refresh(role)
                
                # Assign permissions to role
                await self._assign_role_permissions(role, template)
                created_count += 1
        
        logger.info(f"Created {created_count} roles")
    
    async def _assign_role_permissions(self, role: RoleModel, template: RoleTemplate):
        """Assign permissions to a role based on template."""
        permissions = ROLE_TEMPLATE_PERMISSIONS.get(template, set())
        
        if template == RoleTemplate.SUPERADMIN:
            # Superadmin gets all permissions
            from sqlalchemy import select
            all_perms_query = select(PermissionModel)
            result = await self.session.execute(all_perms_query)
            all_permissions = result.scalars().all()
            permissions_to_assign = all_permissions
        else:
            # Get permission models for the template
            if permissions:
                from sqlalchemy import select
                permission_codes = [perm.value for perm in permissions]
                query = select(PermissionModel).filter(PermissionModel.code.in_(permission_codes))
                result = await self.session.execute(query)
                permissions_to_assign = result.scalars().all()
            else:
                permissions_to_assign = []
        
        # Create role-permission associations
        for permission in permissions_to_assign:
            insert_stmt = role_permission_association.insert().values(
                role_id=role.id,
                permission_id=permission.id
            )
            await self.session.execute(insert_stmt)
        
        await self.session.commit()
        logger.info(f"Assigned {len(permissions_to_assign)} permissions to role {role.name}")
    
    async def seed_default_users(self):
        """Create default system users."""
        logger.info("Seeding default users...")
        
        # Create superadmin user
        from sqlalchemy import select
        superadmin_query = select(UserModel).filter(UserModel.email == "admin@rental.com")
        result = await self.session.execute(superadmin_query)
        existing_admin = result.scalar_one_or_none()
        
        if not existing_admin:
            # Get superadmin role
            role_query = select(RoleModel).filter(RoleModel.name == RoleTemplate.SUPERADMIN.value)
            role_result = await self.session.execute(role_query)
            superadmin_role = role_result.scalar_one_or_none()
            
            admin_user = UserModel(
                email="admin@rental.com",
                name="System Administrator",
                hashed_password=get_password_hash("admin123"),  # Default password - should be changed
                user_type=UserType.SUPERADMIN.value,
                is_superuser=True,
                first_name="System",
                last_name="Administrator",
                username="admin",
                role_id=superadmin_role.id if superadmin_role else None,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.session.add(admin_user)
            
            logger.info("Created default superadmin user (admin@rental.com / admin123)")
        
        await self.session.commit()


async def main():
    """Main function to run the seeder."""
    # Create async engine
    database_url = settings.DATABASE_URL
    engine = create_async_engine(database_url, echo=False)
    
    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        seeder = RBACSeeder(session)
        await seeder.seed_all()


if __name__ == "__main__":
    asyncio.run(main())