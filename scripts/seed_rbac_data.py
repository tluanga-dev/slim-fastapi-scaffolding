#!/usr/bin/env python3
"""
Enhanced RBAC Data Seeding Script

This script populates the database with:
- Permission categories
- 185+ comprehensive permissions
- Role templates
- Permission dependencies
- Default users and roles

Usage:
    python scripts/seed_rbac_data.py
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.db.session import get_session
from app.modules.auth.models import (
    User, Role, Permission, PermissionCategory, PermissionDependency,
    user_roles_table, role_permissions_table
)
from app.modules.auth.constants import (
    PermissionCategory as PermissionCategoryEnum,
    Permission as PermissionEnum,
    PermissionRiskLevel,
    RoleTemplate,
    UserType,
    PERMISSION_CATEGORIES,
    PERMISSION_RISK_LEVELS,
    PERMISSION_DEPENDENCIES,
    ROLE_TEMPLATES,
    get_permission_risk_level
)


class RBACSeeder:
    """Enhanced RBAC data seeding class."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.permission_map: Dict[str, str] = {}  # permission_code -> permission_id
        self.category_map: Dict[str, str] = {}    # category_code -> category_id
        self.role_map: Dict[str, str] = {}        # role_name -> role_id
        
    async def seed_all(self):
        """Seed all RBAC data."""
        print("Starting enhanced RBAC data seeding...")
        
        # Clear existing data (optional - comment out for production)
        # await self.clear_existing_data()  # Skip clearing for now
        
        # Seed in order of dependencies
        await self.seed_permission_categories()
        await self.seed_permissions()
        await self.seed_permission_dependencies()
        await self.seed_roles()
        await self.seed_role_permissions()
        # await self.seed_default_users()  # Skip user creation - users already exist
        
        await self.session.commit()
        print("Enhanced RBAC data seeding completed successfully!")
    
    async def clear_existing_data(self):
        """Clear existing RBAC data for fresh start."""
        print("Clearing existing RBAC data...")
        
        # Delete in reverse order of dependencies
        await self.session.execute(delete(PermissionDependency))
        await self.session.execute(delete(role_permissions_table))
        await self.session.execute(delete(user_roles_table))
        await self.session.execute(delete(Permission))
        await self.session.execute(delete(PermissionCategory))
        await self.session.execute(delete(Role))
        
        # Delete users except those with specific usernames to preserve
        result = await self.session.execute(
            select(User).where(User.username.notin_(["admin", "system"]))
        )
        users_to_delete = result.scalars().all()
        for user in users_to_delete:
            await self.session.delete(user)
        
        await self.session.commit()
        print("Existing RBAC data cleared.")
    
    async def seed_permission_categories(self):
        """Seed permission categories."""
        print("Seeding permission categories...")
        
        categories_data = [
            {
                "code": PermissionCategoryEnum.SYSTEM.value,
                "name": "System Management",
                "description": "Core system administration and configuration",
                "display_order": 1,
                "icon": "cog",
                "color": "#dc3545"
            },
            {
                "code": PermissionCategoryEnum.USER_MANAGEMENT.value,
                "name": "User Management",
                "description": "User accounts, profiles, and authentication",
                "display_order": 2,
                "icon": "users",
                "color": "#007bff"
            },
            {
                "code": PermissionCategoryEnum.ROLE_MANAGEMENT.value,
                "name": "Role Management",
                "description": "Roles, permissions, and access control",
                "display_order": 3,
                "icon": "shield",
                "color": "#6f42c1"
            },
            {
                "code": PermissionCategoryEnum.PROPERTY_MANAGEMENT.value,
                "name": "Property Management",
                "description": "Property listings, details, and status",
                "display_order": 4,
                "icon": "building",
                "color": "#28a745"
            },
            {
                "code": PermissionCategoryEnum.INVENTORY.value,
                "name": "Inventory Management",
                "description": "Stock control, tracking, and valuation",
                "display_order": 5,
                "icon": "boxes",
                "color": "#17a2b8"
            },
            {
                "code": PermissionCategoryEnum.SALES.value,
                "name": "Sales Management",
                "description": "Sales transactions, orders, and processing",
                "display_order": 6,
                "icon": "shopping-cart",
                "color": "#ffc107"
            },
            {
                "code": PermissionCategoryEnum.PURCHASES.value,
                "name": "Purchase Management",
                "description": "Procurement, purchase orders, and receiving",
                "display_order": 7,
                "icon": "shopping-bag",
                "color": "#fd7e14"
            },
            {
                "code": PermissionCategoryEnum.FINANCIAL.value,
                "name": "Financial Management",
                "description": "Financial transactions, budgets, and accounting",
                "display_order": 8,
                "icon": "dollar-sign",
                "color": "#20c997"
            },
            {
                "code": PermissionCategoryEnum.REPORTING.value,
                "name": "Reporting & Analytics",
                "description": "Reports, dashboards, and data analysis",
                "display_order": 9,
                "icon": "chart-bar",
                "color": "#6c757d"
            },
            {
                "code": PermissionCategoryEnum.MAINTENANCE.value,
                "name": "Maintenance Management",
                "description": "Equipment maintenance and service scheduling",
                "display_order": 10,
                "icon": "tools",
                "color": "#e83e8c"
            },
            {
                "code": PermissionCategoryEnum.CUSTOMER_SUPPORT.value,
                "name": "Customer Support",
                "description": "Customer service, tickets, and communication",
                "display_order": 11,
                "icon": "headset",
                "color": "#6610f2"
            },
            {
                "code": PermissionCategoryEnum.ANALYTICS.value,
                "name": "Analytics & Insights",
                "description": "Business intelligence and data insights",
                "display_order": 12,
                "icon": "chart-line",
                "color": "#fd7e14"
            },
            {
                "code": PermissionCategoryEnum.AUDIT.value,
                "name": "Audit & Compliance",
                "description": "Audit trails, compliance, and security",
                "display_order": 13,
                "icon": "search",
                "color": "#495057"
            },
            {
                "code": PermissionCategoryEnum.BACKUP.value,
                "name": "Backup & Recovery",
                "description": "Data backup, restore, and disaster recovery",
                "display_order": 14,
                "icon": "database",
                "color": "#343a40"
            },
            {
                "code": PermissionCategoryEnum.INTEGRATION.value,
                "name": "Integration Management",
                "description": "API integrations, webhooks, and external systems",
                "display_order": 15,
                "icon": "plug",
                "color": "#007bff"
            }
        ]
        
        for category_data in categories_data:
            category = PermissionCategory(
                id=str(uuid.uuid4()),
                code=category_data["code"],
                name=category_data["name"],
                description=category_data["description"],
                display_order=category_data["display_order"],
                icon=category_data["icon"],
                color=category_data["color"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                is_active=True
            )
            self.session.add(category)
            self.category_map[category_data["code"]] = category.id
        
        await self.session.flush()
        print(f"Seeded {len(categories_data)} permission categories.")
    
    async def seed_permissions(self):
        """Seed comprehensive permissions."""
        print("Seeding permissions...")
        
        permissions_data = []
        
        # Generate permissions for each category
        for category, permission_codes in PERMISSION_CATEGORIES.items():
            category_id = self.category_map[category.value]
            
            for permission_code in permission_codes:
                # Parse permission code to get resource and action
                parts = permission_code.split('_')
                if len(parts) >= 2:
                    resource = parts[0]
                    action = '_'.join(parts[1:])
                else:
                    resource = permission_code
                    action = "ACCESS"
                
                # Generate human-readable name and description
                name = permission_code.replace('_', ' ').title()
                description = self._generate_permission_description(permission_code, resource, action)
                
                # Get risk level
                risk_level = get_permission_risk_level(permission_code)
                requires_approval = risk_level in [PermissionRiskLevel.HIGH, PermissionRiskLevel.CRITICAL]
                
                permissions_data.append({
                    "id": str(uuid.uuid4()),
                    "code": permission_code,
                    "name": name,
                    "description": description,
                    "resource": resource.lower(),
                    "action": action.lower(),
                    "category_id": category_id,
                    "risk_level": risk_level.value,
                    "requires_approval": requires_approval,
                    "is_system_permission": True,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "is_active": True
                })
        
        # Create Permission objects
        for perm_data in permissions_data:
            permission = Permission(
                id=perm_data["id"],
                code=perm_data["code"],
                name=perm_data["name"],
                description=perm_data["description"],
                resource=perm_data["resource"],
                action=perm_data["action"],
                category_id=perm_data["category_id"],
                risk_level=perm_data["risk_level"],
                requires_approval=perm_data["requires_approval"],
                is_system_permission=perm_data["is_system_permission"],
                created_at=perm_data["created_at"],
                updated_at=perm_data["updated_at"],
                is_active=perm_data["is_active"]
            )
            self.session.add(permission)
            self.permission_map[perm_data["code"]] = perm_data["id"]
        
        await self.session.flush()
        print(f"Seeded {len(permissions_data)} permissions.")
    
    def _generate_permission_description(self, code: str, resource: str, action: str) -> str:
        """Generate human-readable description for permission."""
        descriptions = {
            "CREATE": f"Create new {resource} entries",
            "READ": f"View {resource} information",
            "UPDATE": f"Modify {resource} information",
            "DELETE": f"Delete {resource} entries",
            "LIST": f"List all {resource} entries",
            "SEARCH": f"Search {resource} entries",
            "EXPORT": f"Export {resource} data",
            "IMPORT": f"Import {resource} data",
            "APPROVE": f"Approve {resource} operations",
            "CANCEL": f"Cancel {resource} operations",
            "ASSIGN": f"Assign {resource} to users",
            "REVOKE": f"Revoke {resource} from users",
            "MANAGE": f"Manage {resource} settings",
            "MONITOR": f"Monitor {resource} activity",
            "AUDIT": f"Audit {resource} operations",
            "BACKUP": f"Backup {resource} data",
            "RESTORE": f"Restore {resource} data",
            "CONFIG": f"Configure {resource} settings",
            "HEALTH_CHECK": f"Check {resource} health status",
            "MAINTENANCE": f"Perform {resource} maintenance",
            "SHUTDOWN": f"Shutdown {resource} system"
        }
        
        action_upper = action.upper()
        if action_upper in descriptions:
            return descriptions[action_upper]
        
        return f"Perform {action} operations on {resource}"
    
    async def seed_permission_dependencies(self):
        """Seed permission dependencies."""
        print("Seeding permission dependencies...")
        
        dependencies_count = 0
        for permission_code, depends_on_codes in PERMISSION_DEPENDENCIES.items():
            if permission_code in self.permission_map:
                permission_id = self.permission_map[permission_code]
                
                for depends_on_code in depends_on_codes:
                    if depends_on_code in self.permission_map:
                        depends_on_id = self.permission_map[depends_on_code]
                        
                        dependency = PermissionDependency(
                            id=str(uuid.uuid4()),
                            permission_id=permission_id,
                            depends_on_id=depends_on_id,
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow(),
                            is_active=True
                        )
                        self.session.add(dependency)
                        dependencies_count += 1
        
        await self.session.flush()
        print(f"Seeded {dependencies_count} permission dependencies.")
    
    async def seed_roles(self):
        """Seed role templates."""
        print("Seeding roles...")
        
        roles_data = [
            {
                "name": "Superadmin",
                "description": "Full system access with all permissions",
                "template": RoleTemplate.SUPERADMIN.value,
                "is_system_role": True,
                "can_be_deleted": False
            },
            {
                "name": "Admin",
                "description": "Administrative access with management permissions",
                "template": RoleTemplate.ADMIN.value,
                "is_system_role": True,
                "can_be_deleted": False
            },
            {
                "name": "Manager",
                "description": "Management access with operational permissions",
                "template": RoleTemplate.MANAGER.value,
                "is_system_role": False,
                "can_be_deleted": True
            },
            {
                "name": "Staff",
                "description": "Staff access with limited operational permissions",
                "template": RoleTemplate.STAFF.value,
                "is_system_role": False,
                "can_be_deleted": True
            },
            {
                "name": "Customer",
                "description": "Customer access with basic permissions",
                "template": RoleTemplate.CUSTOMER.value,
                "is_system_role": False,
                "can_be_deleted": True
            },
            {
                "name": "Auditor",
                "description": "Read-only access for audit and compliance",
                "template": RoleTemplate.AUDITOR.value,
                "is_system_role": False,
                "can_be_deleted": True
            },
            {
                "name": "Accountant",
                "description": "Financial access with accounting permissions",
                "template": RoleTemplate.ACCOUNTANT.value,
                "is_system_role": False,
                "can_be_deleted": True
            }
        ]
        
        for role_data in roles_data:
            role = Role(
                id=str(uuid.uuid4()),
                name=role_data["name"],
                description=role_data["description"],
                template=role_data["template"],
                is_system_role=role_data["is_system_role"],
                can_be_deleted=role_data["can_be_deleted"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                is_active=True
            )
            self.session.add(role)
            self.role_map[role_data["name"]] = role.id
        
        await self.session.flush()
        print(f"Seeded {len(roles_data)} roles.")
    
    async def seed_role_permissions(self):
        """Seed role permissions based on templates."""
        print("Seeding role permissions...")
        
        total_assignments = 0
        
        for role_name, role_id in self.role_map.items():
            # Get template from role name
            template = None
            for t in RoleTemplate:
                if t.value.upper() == role_name.upper():
                    template = t
                    break
            
            if template and template in ROLE_TEMPLATES:
                permission_codes = ROLE_TEMPLATES[template]
                
                for permission_code in permission_codes:
                    if permission_code in self.permission_map:
                        permission_id = self.permission_map[permission_code]
                        
                        # Insert into role_permissions table
                        insert_stmt = role_permissions_table.insert().values(
                            role_id=role_id,
                            permission_id=permission_id
                        )
                        await self.session.execute(insert_stmt)
                        total_assignments += 1
        
        await self.session.flush()
        print(f"Seeded {total_assignments} role-permission assignments.")
    
    async def seed_default_users(self):
        """Seed default users."""
        print("Seeding default users...")
        
        # Create superadmin user
        superadmin_user = User(
            id=str(uuid.uuid4()),
            username="superadmin",
            email="superadmin@example.com",
            password="SuperAdmin123!",  # This will be hashed in the model
            first_name="Super",
            last_name="Admin",
            user_type=UserType.SUPERADMIN.value,
            is_superuser=True,
            email_verified=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_active=True
        )
        self.session.add(superadmin_user)
        
        # Assign superadmin role
        if "Superadmin" in self.role_map:
            superadmin_role_id = self.role_map["Superadmin"]
            insert_stmt = user_roles_table.insert().values(
                user_id=superadmin_user.id,
                role_id=superadmin_role_id
            )
            await self.session.execute(insert_stmt)
        
        # Create admin user
        admin_user = User(
            id=str(uuid.uuid4()),
            username="admin",
            email="admin@example.com",
            password="Admin123!",  # This will be hashed in the model
            first_name="Admin",
            last_name="User",
            user_type=UserType.ADMIN.value,
            is_superuser=False,
            email_verified=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_active=True
        )
        self.session.add(admin_user)
        
        # Assign admin role
        if "Admin" in self.role_map:
            admin_role_id = self.role_map["Admin"]
            insert_stmt = user_roles_table.insert().values(
                user_id=admin_user.id,
                role_id=admin_role_id
            )
            await self.session.execute(insert_stmt)
        
        await self.session.flush()
        print("Seeded default users (superadmin, admin).")


async def main():
    """Main seeding function."""
    async for session in get_session():
        seeder = RBACSeeder(session)
        await seeder.seed_all()
        break


if __name__ == "__main__":
    asyncio.run(main())