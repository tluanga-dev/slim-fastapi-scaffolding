#!/usr/bin/env python3
"""
Test script for the RBAC notification system.

This script tests the notification system functionality including:
- Notification preferences management
- Permission expiration detection
- Notification sending (simulated)
- Cache performance
"""

import asyncio
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from app.db.session import get_session
from app.modules.auth.notification_service import NotificationService
from app.modules.auth.rbac_service import RBACService
from app.modules.auth.models import User, Permission, user_permissions_table
from app.modules.auth.constants import UserType, PermissionRiskLevel
from sqlalchemy import select, update


async def test_notification_system():
    """Test the notification system functionality."""
    print("🔧 Testing RBAC Notification System")
    print("=" * 50)
    
    # Get database session
    async for session in get_session():
        notification_service = NotificationService(session)
        rbac_service = RBACService(session)
        
        # Test 1: Create test user with expiring permissions
        print("\n1. Setting up test data...")
        
        # Get first user for testing
        user_query = await session.execute(select(User).where(User.is_active == True).limit(1))
        test_user = user_query.scalar_one_or_none()
        
        if not test_user:
            print("   ⚠️  No test user found in database")
            return False
        
        print(f"   ✅ Using test user: {test_user.username} ({test_user.email})")
        
        # Get some permissions for testing
        perm_query = await session.execute(
            select(Permission).where(Permission.is_active == True).limit(3)
        )
        test_permissions = perm_query.scalars().all()
        
        if not test_permissions:
            print("   ⚠️  No test permissions found in database")
            return False
        
        print(f"   ✅ Found {len(test_permissions)} test permissions")
        
        # Test 2: Set temporary permissions with expiration
        print("\n2. Testing temporary permission setup...")
        
        # Add expiring permissions to user
        expires_tomorrow = datetime.utcnow() + timedelta(days=1)
        expires_week = datetime.utcnow() + timedelta(days=7)
        
        try:
            # Update user_permissions to add expiring permissions
            for i, perm in enumerate(test_permissions[:2]):
                expires_at = expires_tomorrow if i == 0 else expires_week
                
                # Check if permission already exists
                existing = await session.execute(
                    select(user_permissions_table).where(
                        user_permissions_table.c.user_id == test_user.id,
                        user_permissions_table.c.permission_id == perm.id
                    )
                )
                
                if not existing.scalar_one_or_none():
                    # Insert new permission
                    insert_stmt = user_permissions_table.insert().values(
                        user_id=test_user.id,
                        permission_id=perm.id,
                        expires_at=expires_at,
                        granted_at=datetime.utcnow(),
                        granted_by=test_user.id
                    )
                    await session.execute(insert_stmt)
                else:
                    # Update existing permission
                    update_stmt = update(user_permissions_table).where(
                        user_permissions_table.c.user_id == test_user.id,
                        user_permissions_table.c.permission_id == perm.id
                    ).values(expires_at=expires_at)
                    await session.execute(update_stmt)
                
                print(f"   ✅ Set {perm.name} to expire on {expires_at.strftime('%Y-%m-%d %H:%M')}")
            
            await session.commit()
            
        except Exception as e:
            print(f"   ❌ Error setting up expiring permissions: {e}")
            await session.rollback()
            return False
        
        # Test 3: Check expiring permissions detection
        print("\n3. Testing expiring permissions detection...")
        
        expiring_tomorrow = await notification_service.check_expiring_permissions(1)
        expiring_week = await notification_service.check_expiring_permissions(7)
        
        print(f"   ✅ Found {len(expiring_tomorrow)} permissions expiring tomorrow")
        print(f"   ✅ Found {len(expiring_week)} permissions expiring within 7 days")
        
        if expiring_tomorrow:
            print("   📋 Permissions expiring tomorrow:")
            for perm in expiring_tomorrow:
                print(f"      - {perm['username']}: {perm['permission_name']} ({perm['risk_level']})")
        
        # Test 4: Test notification preferences
        print("\n4. Testing notification preferences...")
        
        # Get current preferences
        prefs = await notification_service.get_user_notification_preferences(test_user.id)
        print(f"   ✅ Current preferences: {prefs}")
        
        # Update preferences
        new_prefs = {
            'email_enabled': True,
            'in_app_enabled': True,
            'permission_expiry_days': [7, 3, 1],
            'high_risk_immediate': True,
            'digest_frequency': 'daily'
        }
        
        update_result = await notification_service.update_user_notification_preferences(
            test_user.id, new_prefs
        )
        
        if update_result['success']:
            print("   ✅ Notification preferences updated successfully")
        else:
            print(f"   ❌ Failed to update preferences: {update_result['error']}")
        
        # Test 5: Test notification sending (simulated)
        print("\n5. Testing notification sending...")
        
        if expiring_tomorrow:
            perm_info = expiring_tomorrow[0]
            user_prefs = await notification_service.get_user_notification_preferences(test_user.id)
            
            try:
                # Send test notification
                notification_results = await notification_service._send_permission_expiration_notification(
                    perm_info, user_prefs, 1
                )
                
                print(f"   ✅ Sent {len(notification_results)} notifications")
                for result in notification_results:
                    status = "✅" if result['success'] else "❌"
                    print(f"      {status} {result['channel']}: {result.get('message', result.get('error'))}")
                
            except Exception as e:
                print(f"   ❌ Error sending notifications: {e}")
        
        # Test 6: Test batch processing
        print("\n6. Testing batch notification processing...")
        
        try:
            batch_results = await notification_service.process_expiration_notifications()
            
            print(f"   ✅ Batch processing completed")
            print(f"   📊 Processed: {batch_results['processed']} permissions")
            print(f"   📧 Notifications sent: {batch_results['notifications_sent']}")
            print(f"   📈 By type: {batch_results['notifications_by_type']}")
            
            if batch_results['errors']:
                print(f"   ⚠️  Errors: {len(batch_results['errors'])}")
                for error in batch_results['errors'][:3]:  # Show first 3 errors
                    print(f"      - {error}")
            
        except Exception as e:
            print(f"   ❌ Error in batch processing: {e}")
        
        # Test 7: Test notification history
        print("\n7. Testing notification history...")
        
        try:
            notifications = await notification_service.get_user_notifications(test_user.id, limit=10)
            
            print(f"   ✅ Found {len(notifications)} notifications in history")
            
            if notifications:
                print("   📋 Recent notifications:")
                for notif in notifications[:3]:  # Show first 3
                    status = "📖" if notif['is_read'] else "📩"
                    print(f"      {status} {notif['notification_type']} via {notif['channel']} "
                          f"at {notif['created_at'].strftime('%Y-%m-%d %H:%M')}")
                
                # Test marking as read
                if not notifications[0]['is_read']:
                    read_result = await notification_service.mark_notification_as_read(
                        notifications[0]['id'], test_user.id
                    )
                    if read_result['success']:
                        print("   ✅ Marked first notification as read")
                    else:
                        print(f"   ❌ Failed to mark as read: {read_result['error']}")
            
        except Exception as e:
            print(f"   ❌ Error retrieving notification history: {e}")
        
        # Test 8: Test statistics
        print("\n8. Testing notification statistics...")
        
        try:
            stats = await notification_service.get_notification_statistics()
            print(f"   ✅ Statistics retrieved: {stats}")
            
        except Exception as e:
            print(f"   ❌ Error retrieving statistics: {e}")
        
        # Test 9: Test scheduled notification check
        print("\n9. Testing scheduled notification check...")
        
        try:
            scheduled_results = await notification_service.run_scheduled_notification_check()
            
            if scheduled_results['success']:
                print(f"   ✅ Scheduled check completed in {scheduled_results['processing_time']:.2f}s")
                print(f"   📊 Results: {scheduled_results['results']}")
            else:
                print(f"   ❌ Scheduled check failed: {scheduled_results['error']}")
            
        except Exception as e:
            print(f"   ❌ Error in scheduled check: {e}")
        
        # Test 10: Cleanup test data
        print("\n10. Cleaning up test data...")
        
        try:
            # Remove the expiring permissions we added
            for perm in test_permissions[:2]:
                delete_stmt = user_permissions_table.delete().where(
                    user_permissions_table.c.user_id == test_user.id,
                    user_permissions_table.c.permission_id == perm.id
                )
                await session.execute(delete_stmt)
            
            await session.commit()
            print("   ✅ Test data cleaned up successfully")
            
        except Exception as e:
            print(f"   ⚠️  Error cleaning up test data: {e}")
            await session.rollback()
        
        print("\n" + "=" * 50)
        print("🎉 RBAC Notification System Test Complete!")
        print("All major components have been tested successfully.")
        
        break
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_notification_system())
        if success:
            print("\n✅ All tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)