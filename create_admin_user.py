#!/usr/bin/env python3
"""
Script to create an admin user for the rental management system.
"""

import asyncio
import sys
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_session_context
from app.modules.auth.models import User, Role, Permission, UserStatus


async def create_admin_permissions():
    """Create system permissions for admin role."""
    permissions_data = [
        # User management
        {"name": "users:read", "resource": "users", "action": "read", "description": "View users", "is_system_permission": True},
        {"name": "users:write", "resource": "users", "action": "write", "description": "Create and update users", "is_system_permission": True},
        {"name": "users:delete", "resource": "users", "action": "delete", "description": "Delete users", "is_system_permission": True},
        
        # Role management
        {"name": "roles:read", "resource": "roles", "action": "read", "description": "View roles", "is_system_permission": True},
        {"name": "roles:write", "resource": "roles", "action": "write", "description": "Create and update roles", "is_system_permission": True},
        {"name": "roles:delete", "resource": "roles", "action": "delete", "description": "Delete roles", "is_system_permission": True},
        
        # Customer management
        {"name": "customers:read", "resource": "customers", "action": "read", "description": "View customers", "is_system_permission": True},
        {"name": "customers:write", "resource": "customers", "action": "write", "description": "Create and update customers", "is_system_permission": True},
        {"name": "customers:delete", "resource": "customers", "action": "delete", "description": "Delete customers", "is_system_permission": True},
        
        # Supplier management
        {"name": "suppliers:read", "resource": "suppliers", "action": "read", "description": "View suppliers", "is_system_permission": True},
        {"name": "suppliers:write", "resource": "suppliers", "action": "write", "description": "Create and update suppliers", "is_system_permission": True},
        {"name": "suppliers:delete", "resource": "suppliers", "action": "delete", "description": "Delete suppliers", "is_system_permission": True},
        
        # Inventory management
        {"name": "inventory:read", "resource": "inventory", "action": "read", "description": "View inventory", "is_system_permission": True},
        {"name": "inventory:write", "resource": "inventory", "action": "write", "description": "Create and update inventory", "is_system_permission": True},
        {"name": "inventory:delete", "resource": "inventory", "action": "delete", "description": "Delete inventory", "is_system_permission": True},
        
        # Transaction management
        {"name": "transactions:read", "resource": "transactions", "action": "read", "description": "View transactions", "is_system_permission": True},
        {"name": "transactions:write", "resource": "transactions", "action": "write", "description": "Create and update transactions", "is_system_permission": True},
        {"name": "transactions:delete", "resource": "transactions", "action": "delete", "description": "Delete transactions", "is_system_permission": True},
        
        # Rental management
        {"name": "rentals:read", "resource": "rentals", "action": "read", "description": "View rentals", "is_system_permission": True},
        {"name": "rentals:write", "resource": "rentals", "action": "write", "description": "Create and update rentals", "is_system_permission": True},
        {"name": "rentals:delete", "resource": "rentals", "action": "delete", "description": "Delete rentals", "is_system_permission": True},
        
        # Master data management
        {"name": "master_data:read", "resource": "master_data", "action": "read", "description": "View master data", "is_system_permission": True},
        {"name": "master_data:write", "resource": "master_data", "action": "write", "description": "Create and update master data", "is_system_permission": True},
        {"name": "master_data:delete", "resource": "master_data", "action": "delete", "description": "Delete master data", "is_system_permission": True},
        
        # Analytics and reports
        {"name": "analytics:read", "resource": "analytics", "action": "read", "description": "View analytics", "is_system_permission": True},
        {"name": "reports:read", "resource": "reports", "action": "read", "description": "View reports", "is_system_permission": True},
        {"name": "reports:generate", "resource": "reports", "action": "generate", "description": "Generate reports", "is_system_permission": True},
        
        # System administration
        {"name": "system:read", "resource": "system", "action": "read", "description": "View system settings", "is_system_permission": True},
        {"name": "system:write", "resource": "system", "action": "write", "description": "Update system settings", "is_system_permission": True},
        {"name": "system:admin", "resource": "system", "action": "admin", "description": "Full system administration", "is_system_permission": True},
    ]
    
    created_permissions = []
    
    async with get_session_context() as session:
        for perm_data in permissions_data:
            # Check if permission already exists
            result = await session.execute(
                select(Permission).where(Permission.name == perm_data["name"])
            )
            existing_permission = result.scalar_one_or_none()
            
            if not existing_permission:
                permission = Permission(**perm_data)
                session.add(permission)
                created_permissions.append(permission)
                print(f"Created permission: {perm_data['name']}")
            else:
                created_permissions.append(existing_permission)
                print(f"Permission already exists: {perm_data['name']}")
        
        await session.commit()
    
    return created_permissions


async def create_admin_role(permissions):
    """Create admin role with all permissions."""
    async with get_session_context() as session:
        # Check if admin role already exists
        result = await session.execute(
            select(Role).where(Role.name == "ADMIN")
        )
        admin_role = result.scalar_one_or_none()
        
        if not admin_role:
            admin_role = Role(
                name="ADMIN",
                description="System Administrator with full access to all features",
                is_system_role=True
            )
            session.add(admin_role)
            await session.flush()  # To get the ID
            print("Created admin role")
        else:
            print("Admin role already exists")
        
        # Assign all permissions to admin role
        admin_role.permissions = permissions
        await session.commit()
        print(f"Assigned {len(permissions)} permissions to admin role")
        
        return admin_role


async def create_admin_user(admin_role):
    """Create admin user account."""
    username = "admin"
    password = "admin@123"
    email = "admin@example.com"
    
    async with get_session_context() as session:
        # Check if admin user already exists
        result = await session.execute(
            select(User).where(User.username == username)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"User '{username}' already exists!")
            print(f"User ID: {existing_user.id}")
            print(f"Email: {existing_user.email}")
            print(f"Status: {existing_user.status}")
            print(f"Roles: {[role.name for role in existing_user.roles]}")
            
            # Update password if requested
            print(f"Updating password for existing user...")
            existing_user.set_password(password, updated_by="system")
            
            # Ensure admin role is assigned
            if admin_role not in existing_user.roles:
                existing_user.roles.append(admin_role)
                print("Added admin role to existing user")
            
            await session.commit()
            return existing_user
        
        # Create new admin user
        try:
            admin_user = User(
                username=username,
                email=email,
                password=password,
                first_name="System",
                last_name="Administrator",
                status=UserStatus.ACTIVE
            )
            
            # Assign admin role
            admin_user.roles = [admin_role]
            
            session.add(admin_user)
            await session.commit()
            
            print("✅ Admin user created successfully!")
            print(f"Username: {username}")
            print(f"Password: {password}")
            print(f"Email: {email}")
            print(f"User ID: {admin_user.id}")
            print(f"Roles: {[role.name for role in admin_user.roles]}")
            
            return admin_user
            
        except Exception as e:
            print(f"❌ Error creating admin user: {e}")
            await session.rollback()
            raise


async def verify_admin_user():
    """Verify admin user can login and has proper permissions."""
    async with get_session_context() as session:
        result = await session.execute(
            select(User).where(User.username == "admin")
        )
        admin_user = result.scalar_one_or_none()
        
        if not admin_user:
            print("❌ Admin user not found!")
            return False
        
        # Test password verification
        if not admin_user.verify_password("admin@123"):
            print("❌ Admin password verification failed!")
            return False
        
        print("✅ Admin user verification successful!")
        print(f"Can login: {admin_user.can_login()}")
        print(f"Is active: {admin_user.is_active_user()}")
        print(f"Permissions count: {len(admin_user.get_permissions())}")
        print(f"Has admin role: {admin_user.has_role('ADMIN')}")
        print(f"Has system admin permission: {admin_user.has_permission('system:admin')}")
        
        return True


async def main():
    """Main function to create admin account."""
    print("🚀 Creating admin account for Rental Management System")
    print("=" * 60)
    
    try:
        # Step 1: Create permissions
        print("\n1. Creating system permissions...")
        permissions = await create_admin_permissions()
        
        # Step 2: Create admin role
        print("\n2. Creating admin role...")
        admin_role = await create_admin_role(permissions)
        
        # Step 3: Create admin user
        print("\n3. Creating admin user...")
        admin_user = await create_admin_user(admin_role)
        
        # Step 4: Verify setup
        print("\n4. Verifying admin user...")
        verification_success = await verify_admin_user()
        
        if verification_success:
            print("\n" + "=" * 60)
            print("✅ Admin account setup completed successfully!")
            print("\nLogin credentials:")
            print(f"  Username: admin")
            print(f"  Password: admin@123")
            print(f"  Email: admin@example.com")
            print("\n🔐 Please change the default password after first login!")
            print("=" * 60)
        else:
            print("\n❌ Admin account setup failed verification!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Error during admin account setup: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())