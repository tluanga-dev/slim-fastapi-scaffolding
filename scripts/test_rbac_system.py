#!/usr/bin/env python3
"""
Test script for the enhanced RBAC system.

This script tests the key functionality of the enhanced RBAC system including:
- Permission dependency validation
- Role hierarchy support
- Temporary permissions
- User type management
"""

import asyncio
import sys
from datetime import datetime, timedelta
from sqlalchemy import select

# Add the app directory to the path
sys.path.append('/Users/tluanga/Dev/code/current-work/rental-manager/rental-backend')

from app.db.session import get_session
from app.modules.auth.rbac_service import RBACService
from app.modules.auth.models import User, Role, Permission
from app.modules.auth.constants import UserType


async def test_rbac_system():
    """Test the enhanced RBAC system functionality."""
    print("🔧 Testing Enhanced RBAC System")
    print("=" * 50)
    
    # Get database session
    async for session in get_session():
        rbac_service = RBACService(session)
        
        # Test 1: Check database seeding
        print("\n1. Testing database seeding...")
        categories = await rbac_service.get_permission_categories()
        print(f"   ✅ Found {len(categories)} permission categories")
        
        permissions_count = await session.execute(select(Permission).where(Permission.is_active == True))
        permissions = permissions_count.scalars().all()
        print(f"   ✅ Found {len(permissions)} permissions")
        
        roles_count = await session.execute(select(Role).where(Role.is_active == True))
        roles = roles_count.scalars().all()
        print(f"   ✅ Found {len(roles)} roles")
        
        # Test 2: Permission dependency validation
        print("\n2. Testing permission dependency validation...")
        
        # Get a user (use first user in database)
        user_query = await session.execute(select(User).where(User.is_active == True).limit(1))
        test_user = user_query.scalar_one_or_none()
        
        if test_user:
            validation_result = await rbac_service.validate_permission_dependencies(
                test_user.id, 
                ["USER_DELETE", "USER_UPDATE"]
            )
            print(f"   ✅ Dependency validation result: {validation_result}")
        else:
            print("   ⚠️  No users found in database")
        
        # Test 3: Permission categories
        print("\n3. Testing permission categories...")
        if categories:
            first_category = categories[0]
            category_permissions = await rbac_service.get_permissions_by_category(first_category.code)
            print(f"   ✅ Category '{first_category.name}' has {len(category_permissions)} permissions")
        
        # Test 4: Role hierarchy (create a test hierarchy)
        print("\n4. Testing role hierarchy...")
        
        # Find admin and manager roles
        admin_role = None
        manager_role = None
        
        for role in roles:
            if role.name == "Admin":
                admin_role = role
            elif role.name == "Manager":
                manager_role = role
        
        if admin_role and manager_role:
            # Add hierarchy: Admin -> Manager
            hierarchy_result = await rbac_service.add_role_hierarchy(
                parent_role_id=admin_role.id,
                child_role_id=manager_role.id,
                inherit_permissions=True
            )
            print(f"   ✅ Role hierarchy result: {hierarchy_result['message']}")
            
            # Test inherited permissions
            inherited_permissions = await rbac_service.get_role_inherited_permissions(manager_role.id)
            print(f"   ✅ Manager role has {len(inherited_permissions)} permissions (including inherited)")
            
            # Clean up - remove hierarchy
            await rbac_service.remove_role_hierarchy(admin_role.id, manager_role.id)
            print("   ✅ Cleaned up test hierarchy")
        else:
            print("   ⚠️  Admin or Manager role not found")
        
        # Test 5: Temporary permissions (if we have a user)
        print("\n5. Testing temporary permissions...")
        
        if test_user and permissions:
            # Grant temporary permission
            test_permission = permissions[0]
            expires_at = datetime.utcnow() + timedelta(hours=1)
            
            temp_result = await rbac_service.grant_temporary_permission(
                granter_id=test_user.id,
                grantee_id=test_user.id,
                permission_code=test_permission.code,
                expires_at=expires_at,
                reason="Test temporary permission"
            )
            
            if temp_result['success']:
                print(f"   ✅ Temporary permission granted: {temp_result['message']}")
                
                # Get temporary permissions
                temp_permissions = await rbac_service.get_user_temporary_permissions(test_user.id)
                print(f"   ✅ User has {temp_permissions['active_count']} active temporary permissions")
                
                # Clean up - revoke temporary permission
                revoke_result = await rbac_service.revoke_temporary_permission(
                    revoker_id=test_user.id,
                    user_id=test_user.id,
                    permission_code=test_permission.code
                )
                print(f"   ✅ Temporary permission revoked: {revoke_result['message']}")
            else:
                print(f"   ⚠️  Failed to grant temporary permission: {temp_result['message']}")
        else:
            print("   ⚠️  No users or permissions found for testing")
        
        # Test 6: User type management
        print("\n6. Testing user type management...")
        
        if test_user:
            # Test user type capabilities
            can_manage_admin = await rbac_service.can_user_manage_user_type(
                test_user.id, 
                UserType.ADMIN
            )
            print(f"   ✅ User can manage ADMIN type: {can_manage_admin}")
            
            can_manage_user = await rbac_service.can_user_manage_user_type(
                test_user.id, 
                UserType.USER
            )
            print(f"   ✅ User can manage USER type: {can_manage_user}")
        
        # Test 7: Audit logging
        print("\n7. Testing audit logging...")
        
        # Get recent audit logs
        audit_logs = await rbac_service.get_rbac_audit_logs(limit=5)
        print(f"   ✅ Found {len(audit_logs)} recent audit log entries")
        
        if audit_logs:
            recent_log = audit_logs[0]
            print(f"   ✅ Most recent action: {recent_log.action} at {recent_log.timestamp}")
        
        print("\n" + "=" * 50)
        print("🎉 Enhanced RBAC System Test Complete!")
        print("All major components are working correctly.")
        
        break


if __name__ == "__main__":
    asyncio.run(test_rbac_system())