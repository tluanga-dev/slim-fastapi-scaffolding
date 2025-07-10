"""
RBAC Notification API Routes

This module provides API endpoints for RBAC notification management including:
- Notification preferences management
- Notification history retrieval  
- Notification status updates
- Notification statistics
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from uuid import UUID

from .notification_service import NotificationService
from .schemas import (
    NotificationPreferenceResponse, NotificationPreferenceUpdate,
    NotificationHistoryResponse, NotificationMarkReadRequest,
    NotificationStatsResponse, NotificationCheckRequest,
    NotificationCheckResponse, NotificationPreferenceRequest
)
from app.shared.dependencies import get_session, get_current_user_data
from app.core.security import TokenData
from app.modules.auth.rbac_service import RBACService
from app.modules.auth.constants import UserType


router = APIRouter(prefix="/notifications", tags=["RBAC Notifications"])


@router.get("/preferences", response_model=NotificationPreferenceResponse)
async def get_notification_preferences(
    current_user: TokenData = Depends(get_current_user_data),
    session = Depends(get_session)
):
    """Get current user's notification preferences."""
    user_id = UUID(current_user["user_id"])
    notification_service = NotificationService(session)
    
    preferences = await notification_service.get_user_notification_preferences(user_id)
    
    return NotificationPreferenceResponse(
        user_id=user_id,
        email_enabled=preferences.get('email_enabled', True),
        in_app_enabled=preferences.get('in_app_enabled', True),
        permission_expiry_days=preferences.get('permission_expiry_days', [7, 3, 1]),
        high_risk_immediate=preferences.get('high_risk_immediate', True),
        digest_frequency=preferences.get('digest_frequency', 'daily'),
        quiet_hours_start=preferences.get('quiet_hours_start'),
        quiet_hours_end=preferences.get('quiet_hours_end')
    )


@router.put("/preferences", response_model=dict)
async def update_notification_preferences(
    request: NotificationPreferenceRequest,
    current_user: TokenData = Depends(get_current_user_data),
    session = Depends(get_session)
):
    """Update current user's notification preferences."""
    user_id = UUID(current_user["user_id"])
    notification_service = NotificationService(session)
    
    # Convert request to preferences dict
    preferences = {
        'email_enabled': request.email_enabled,
        'in_app_enabled': request.in_app_enabled,
        'permission_expiry_days': request.permission_expiry_days,
        'high_risk_immediate': request.high_risk_immediate,
        'digest_frequency': request.digest_frequency,
        'quiet_hours_start': request.quiet_hours_start,
        'quiet_hours_end': request.quiet_hours_end
    }
    
    result = await notification_service.update_user_notification_preferences(user_id, preferences)
    
    if not result['success']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result['error']
        )
    
    return {"message": "Notification preferences updated successfully"}


@router.get("/history", response_model=List[NotificationHistoryResponse])
async def get_notification_history(
    limit: int = 50,
    offset: int = 0,
    current_user: TokenData = Depends(get_current_user_data),
    session = Depends(get_session)
):
    """Get current user's notification history."""
    user_id = UUID(current_user["user_id"])
    notification_service = NotificationService(session)
    
    notifications = await notification_service.get_user_notifications(user_id, limit, offset)
    
    return [
        NotificationHistoryResponse(
            id=UUID(notif['id']),
            notification_type=notif['notification_type'],
            channel=notif['channel'],
            title=notif['title'],
            message=notif['message'],
            content=notif['content'],
            is_read=notif['is_read'],
            created_at=notif['created_at'],
            read_at=notif['read_at']
        )
        for notif in notifications
    ]


@router.patch("/history/{notification_id}/read", response_model=dict)
async def mark_notification_as_read(
    notification_id: UUID,
    current_user: TokenData = Depends(get_current_user_data),
    session = Depends(get_session)
):
    """Mark a notification as read."""
    user_id = UUID(current_user["user_id"])
    notification_service = NotificationService(session)
    
    result = await notification_service.mark_notification_as_read(notification_id, user_id)
    
    if not result['success']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result['error']
        )
    
    return {"message": "Notification marked as read"}


@router.get("/unread-count", response_model=dict)
async def get_unread_notification_count(
    current_user: TokenData = Depends(get_current_user_data),
    session = Depends(get_session)
):
    """Get count of unread notifications for current user."""
    user_id = UUID(current_user["user_id"])
    notification_service = NotificationService(session)
    
    # Get recent unread notifications
    notifications = await notification_service.get_user_notifications(user_id, limit=100)
    unread_count = sum(1 for notif in notifications if not notif['is_read'])
    
    return {
        "unread_count": unread_count,
        "total_count": len(notifications)
    }


@router.post("/check-expiring", response_model=NotificationCheckResponse)
async def check_expiring_permissions(
    request: NotificationCheckRequest,
    current_user: TokenData = Depends(get_current_user_data),
    session = Depends(get_session)
):
    """Check for expiring permissions (admin only)."""
    user_id = UUID(current_user["user_id"])
    rbac_service = RBACService(session)
    
    # Check if user has admin privileges
    user = await rbac_service.repository.get_user_by_id(user_id)
    if not user or user.user_type not in [UserType.ADMIN.value, UserType.SUPERADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    notification_service = NotificationService(session)
    
    # Check expiring permissions
    expiring_permissions = await notification_service.check_expiring_permissions(request.days_ahead)
    
    return NotificationCheckResponse(
        total_expiring=len(expiring_permissions),
        expiring_permissions=expiring_permissions,
        checked_at=datetime.utcnow()
    )


@router.post("/process-batch", response_model=dict)
async def process_notification_batch(
    background_tasks: BackgroundTasks,
    current_user: TokenData = Depends(get_current_user_data),
    session = Depends(get_session)
):
    """Process notification batch (admin only)."""
    user_id = UUID(current_user["user_id"])
    rbac_service = RBACService(session)
    
    # Check if user has admin privileges
    user = await rbac_service.repository.get_user_by_id(user_id)
    if not user or user.user_type not in [UserType.ADMIN.value, UserType.SUPERADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    notification_service = NotificationService(session)
    
    # Process notifications in background
    background_tasks.add_task(notification_service.process_expiration_notifications)
    
    return {"message": "Notification batch processing started"}


@router.get("/stats", response_model=NotificationStatsResponse)
async def get_notification_statistics(
    current_user: TokenData = Depends(get_current_user_data),
    session = Depends(get_session)
):
    """Get notification system statistics (admin only)."""
    user_id = UUID(current_user["user_id"])
    rbac_service = RBACService(session)
    
    # Check if user has admin privileges
    user = await rbac_service.repository.get_user_by_id(user_id)
    if not user or user.user_type not in [UserType.ADMIN.value, UserType.SUPERADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    notification_service = NotificationService(session)
    
    # Get statistics
    stats = await notification_service.get_notification_statistics()
    
    return NotificationStatsResponse(
        total_processed=stats.get('total_processed', 0),
        total_notifications_sent=stats.get('total_notifications_sent', 0),
        notifications_by_channel=stats.get('notifications_by_channel', {}),
        last_run=stats.get('last_run'),
        system_health="healthy"
    )


@router.post("/test-notification", response_model=dict)
async def send_test_notification(
    current_user: TokenData = Depends(get_current_user_data),
    session = Depends(get_session)
):
    """Send a test notification to current user."""
    user_id = UUID(current_user["user_id"])
    notification_service = NotificationService(session)
    
    # Create test notification data
    test_perm_info = {
        'user_id': user_id,
        'permission_id': user_id,  # Using user_id as dummy permission_id
        'username': current_user.get('username', 'testuser'),
        'email': current_user.get('email', 'test@example.com'),
        'first_name': current_user.get('first_name', 'Test'),
        'last_name': current_user.get('last_name', 'User'),
        'permission_code': 'TEST_PERMISSION',
        'permission_name': 'Test Permission',
        'risk_level': 'LOW',
        'expires_at': datetime.utcnow(),
        'days_until_expiry': 1
    }
    
    # Get user preferences
    user_prefs = await notification_service.get_user_notification_preferences(user_id)
    
    # Send test notification
    results = await notification_service._send_permission_expiration_notification(
        test_perm_info, user_prefs, 1
    )
    
    return {
        "message": "Test notification sent",
        "results": results
    }


@router.get("/admin/expiring-summary", response_model=dict)
async def get_expiring_permissions_summary(
    current_user: TokenData = Depends(get_current_user_data),
    session = Depends(get_session)
):
    """Get summary of expiring permissions (admin only)."""
    user_id = UUID(current_user["user_id"])
    rbac_service = RBACService(session)
    
    # Check if user has admin privileges
    user = await rbac_service.repository.get_user_by_id(user_id)
    if not user or user.user_type not in [UserType.ADMIN.value, UserType.SUPERADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    notification_service = NotificationService(session)
    
    # Get expiring permissions for different time periods
    summary = {
        "expires_today": await notification_service.check_expiring_permissions(0),
        "expires_tomorrow": await notification_service.check_expiring_permissions(1),
        "expires_this_week": await notification_service.check_expiring_permissions(7),
        "expires_this_month": await notification_service.check_expiring_permissions(30)
    }
    
    # Calculate risk breakdown
    risk_breakdown = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    for period_permissions in summary.values():
        for perm in period_permissions:
            risk_level = perm.get('risk_level', 'LOW')
            if risk_level in risk_breakdown:
                risk_breakdown[risk_level] += 1
    
    return {
        "summary": {
            "expires_today": len(summary["expires_today"]),
            "expires_tomorrow": len(summary["expires_tomorrow"]),
            "expires_this_week": len(summary["expires_this_week"]),
            "expires_this_month": len(summary["expires_this_month"])
        },
        "risk_breakdown": risk_breakdown,
        "details": summary
    }