"""
RBAC Permission Expiration Notification Service

This module provides notification services for RBAC permission expirations including:
- Email notifications for expiring permissions
- In-app notifications for users and admins
- Scheduled tasks to check for expiring permissions
- Notification preferences management
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from .models import (
    User, Permission, user_permissions_table, RBACauditlog,
    NotificationPreference, PermissionNotification
)
from .constants import NotificationType, NotificationChannel
from .rbac_service import RBACService
from app.core.config import settings
try:
    from app.core.cache import cache_manager
except ImportError:
    cache_manager = None
from app.core.errors import ValidationError, NotFoundError


class NotificationService:
    """
    Service for managing RBAC permission expiration notifications.
    
    Features:
    - Email and in-app notifications for expiring permissions
    - Scheduled checks for expiring permissions
    - Notification preferences management
    - Notification history tracking
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize notification service with database session."""
        self.session = session
        self.rbac_service = RBACService(session)
        
        # Default notification settings
        self.default_warning_days = [7, 3, 1]  # Notify 7, 3, and 1 days before expiration
        self.default_batch_size = 100
        
        # Cache keys
        self.cache_prefix = "rbac_notifications:"
        self.user_prefs_cache_key = lambda user_id: f"{self.cache_prefix}user_prefs:{user_id}"
        self.notification_stats_key = f"{self.cache_prefix}stats"
    
    # Permission expiration checking
    async def check_expiring_permissions(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """
        Check for permissions expiring within specified days.
        
        Args:
            days_ahead: Number of days ahead to check for expiring permissions
            
        Returns:
            List of expiring permission info
        """
        cutoff_date = datetime.utcnow() + timedelta(days=days_ahead)
        
        # Query for expiring permissions
        query = select(
            user_permissions_table.c.user_id,
            user_permissions_table.c.permission_id,
            user_permissions_table.c.expires_at,
            User.username,
            User.email,
            User.first_name,
            User.last_name,
            Permission.code,
            Permission.name,
            Permission.risk_level
        ).select_from(
            user_permissions_table
            .join(User, user_permissions_table.c.user_id == User.id)
            .join(Permission, user_permissions_table.c.permission_id == Permission.id)
        ).where(
            and_(
                user_permissions_table.c.expires_at.is_not(None),
                user_permissions_table.c.expires_at <= cutoff_date,
                user_permissions_table.c.expires_at > datetime.utcnow(),
                User.is_active == True,
                Permission.is_active == True
            )
        )
        
        result = await self.session.execute(query)
        expiring_permissions = []
        
        for row in result:
            days_until_expiry = (row.expires_at - datetime.utcnow()).days
            
            expiring_permissions.append({
                'user_id': row.user_id,
                'permission_id': row.permission_id,
                'username': row.username,
                'email': row.email,
                'first_name': row.first_name,
                'last_name': row.last_name,
                'permission_code': row.code,
                'permission_name': row.name,
                'risk_level': row.risk_level,
                'expires_at': row.expires_at,
                'days_until_expiry': days_until_expiry
            })
        
        return expiring_permissions
    
    async def process_expiration_notifications(self) -> Dict[str, Any]:
        """
        Process all pending expiration notifications.
        
        Returns:
            Dict with processing results
        """
        results = {
            'processed': 0,
            'notifications_sent': 0,
            'errors': [],
            'notifications_by_type': {}
        }
        
        # Check for permissions expiring at different intervals
        for days_ahead in self.default_warning_days:
            expiring_permissions = await self.check_expiring_permissions(days_ahead)
            
            for perm_info in expiring_permissions:
                # Check if notification already sent for this combination
                if await self._is_notification_already_sent(
                    perm_info['user_id'],
                    perm_info['permission_id'],
                    days_ahead
                ):
                    continue
                
                # Get user notification preferences
                user_prefs = await self.get_user_notification_preferences(perm_info['user_id'])
                
                # Send notifications based on preferences
                notification_results = await self._send_permission_expiration_notification(
                    perm_info, user_prefs, days_ahead
                )
                
                results['processed'] += 1
                results['notifications_sent'] += len(notification_results)
                
                # Track notification by type
                for notif_result in notification_results:
                    channel = notif_result['channel']
                    if channel not in results['notifications_by_type']:
                        results['notifications_by_type'][channel] = 0
                    results['notifications_by_type'][channel] += 1
                
                # Log any errors
                for notif_result in notification_results:
                    if not notif_result['success']:
                        results['errors'].append({
                            'user_id': perm_info['user_id'],
                            'permission_code': perm_info['permission_code'],
                            'channel': notif_result['channel'],
                            'error': notif_result['error']
                        })
        
        return results
    
    async def _send_permission_expiration_notification(
        self, 
        perm_info: Dict[str, Any], 
        user_prefs: Dict[str, Any], 
        days_ahead: int
    ) -> List[Dict[str, Any]]:
        """
        Send permission expiration notification via configured channels.
        
        Args:
            perm_info: Permission expiration information
            user_prefs: User notification preferences
            days_ahead: Days ahead for this notification
            
        Returns:
            List of notification results
        """
        results = []
        
        # Email notification
        if user_prefs.get('email_enabled', True):
            email_result = await self._send_email_notification(perm_info, days_ahead)
            results.append(email_result)
        
        # In-app notification
        if user_prefs.get('in_app_enabled', True):
            in_app_result = await self._send_in_app_notification(perm_info, days_ahead)
            results.append(in_app_result)
        
        # Admin notification for high-risk permissions
        if perm_info['risk_level'] in ['HIGH', 'CRITICAL']:
            admin_result = await self._send_admin_notification(perm_info, days_ahead)
            results.append(admin_result)
        
        return results
    
    async def _send_email_notification(self, perm_info: Dict[str, Any], days_ahead: int) -> Dict[str, Any]:
        """
        Send email notification for permission expiration.
        
        Args:
            perm_info: Permission expiration information
            days_ahead: Days ahead for this notification
            
        Returns:
            Notification result
        """
        try:
            # Email template based on urgency
            if days_ahead == 1:
                subject = f"⚠️ Permission Expires Tomorrow: {perm_info['permission_name']}"
                urgency = "urgent"
            elif days_ahead <= 3:
                subject = f"⚠️ Permission Expires Soon: {perm_info['permission_name']}"
                urgency = "high"
            else:
                subject = f"📅 Permission Expiring in {days_ahead} days: {perm_info['permission_name']}"
                urgency = "medium"
            
            email_content = self._generate_email_content(perm_info, days_ahead, urgency)
            
            # TODO: Integrate with actual email service
            # For now, we'll simulate email sending
            await self._simulate_email_send(perm_info['email'], subject, email_content)
            
            # Record notification in database
            await self._record_notification(
                user_id=perm_info['user_id'],
                permission_id=perm_info['permission_id'],
                notification_type=NotificationType.PERMISSION_EXPIRING,
                channel=NotificationChannel.EMAIL,
                days_ahead=days_ahead,
                content=email_content
            )
            
            return {
                'success': True,
                'channel': 'email',
                'message': f'Email sent to {perm_info["email"]}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'channel': 'email',
                'error': str(e)
            }
    
    async def _send_in_app_notification(self, perm_info: Dict[str, Any], days_ahead: int) -> Dict[str, Any]:
        """
        Send in-app notification for permission expiration.
        
        Args:
            perm_info: Permission expiration information
            days_ahead: Days ahead for this notification
            
        Returns:
            Notification result
        """
        try:
            # Create in-app notification message
            if days_ahead == 1:
                title = "Permission Expires Tomorrow"
                message = f"Your '{perm_info['permission_name']}' permission expires tomorrow."
                priority = "high"
            elif days_ahead <= 3:
                title = "Permission Expires Soon"
                message = f"Your '{perm_info['permission_name']}' permission expires in {days_ahead} days."
                priority = "medium"
            else:
                title = "Permission Expiring"
                message = f"Your '{perm_info['permission_name']}' permission expires in {days_ahead} days."
                priority = "low"
            
            # Record in-app notification
            await self._record_notification(
                user_id=perm_info['user_id'],
                permission_id=perm_info['permission_id'],
                notification_type=NotificationType.PERMISSION_EXPIRING,
                channel=NotificationChannel.IN_APP,
                days_ahead=days_ahead,
                content=json.dumps({
                    'title': title,
                    'message': message,
                    'priority': priority,
                    'permission_code': perm_info['permission_code'],
                    'expires_at': perm_info['expires_at'].isoformat()
                })
            )
            
            return {
                'success': True,
                'channel': 'in_app',
                'message': f'In-app notification created for user {perm_info["username"]}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'channel': 'in_app',
                'error': str(e)
            }
    
    async def _send_admin_notification(self, perm_info: Dict[str, Any], days_ahead: int) -> Dict[str, Any]:
        """
        Send admin notification for high-risk permission expiration.
        
        Args:
            perm_info: Permission expiration information
            days_ahead: Days ahead for this notification
            
        Returns:
            Notification result
        """
        try:
            # Get admin users
            admin_users = await self._get_admin_users()
            
            if not admin_users:
                return {
                    'success': False,
                    'channel': 'admin',
                    'error': 'No admin users found'
                }
            
            # Create admin notification content
            admin_message = {
                'title': f"High-Risk Permission Expiring",
                'message': f"User {perm_info['username']} has a {perm_info['risk_level']} risk permission '{perm_info['permission_name']}' expiring in {days_ahead} days.",
                'user_details': {
                    'user_id': str(perm_info['user_id']),
                    'username': perm_info['username'],
                    'email': perm_info['email'],
                    'full_name': f"{perm_info['first_name']} {perm_info['last_name']}"
                },
                'permission_details': {
                    'code': perm_info['permission_code'],
                    'name': perm_info['permission_name'],
                    'risk_level': perm_info['risk_level'],
                    'expires_at': perm_info['expires_at'].isoformat()
                },
                'days_until_expiry': days_ahead
            }
            
            # Send to all admin users
            notifications_sent = 0
            for admin_user in admin_users:
                await self._record_notification(
                    user_id=admin_user['id'],
                    permission_id=perm_info['permission_id'],
                    notification_type=NotificationType.ADMIN_ALERT,
                    channel=NotificationChannel.IN_APP,
                    days_ahead=days_ahead,
                    content=json.dumps(admin_message),
                    related_user_id=perm_info['user_id']
                )
                notifications_sent += 1
            
            return {
                'success': True,
                'channel': 'admin',
                'message': f'Admin notifications sent to {notifications_sent} administrators'
            }
            
        except Exception as e:
            return {
                'success': False,
                'channel': 'admin',
                'error': str(e)
            }
    
    # Notification preferences management
    async def get_user_notification_preferences(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get user notification preferences.
        
        Args:
            user_id: User ID
            
        Returns:
            User notification preferences
        """
        # Try cache first
        cache_key = self.user_prefs_cache_key(user_id)
        cached_prefs = None
        if cache_manager:
            cached_prefs = await cache_manager.get(cache_key)
        
        if cached_prefs:
            return json.loads(cached_prefs)
        
        # Query database
        query = select(NotificationPreference).where(
            and_(
                NotificationPreference.user_id == user_id,
                NotificationPreference.is_active == True
            )
        )
        
        result = await self.session.execute(query)
        prefs = result.scalar_one_or_none()
        
        if prefs:
            expiry_days = prefs.permission_expiry_days
            if isinstance(expiry_days, str):
                try:
                    expiry_days = json.loads(expiry_days)
                except:
                    expiry_days = self.default_warning_days
            elif expiry_days is None:
                expiry_days = self.default_warning_days
            
            preferences = {
                'email_enabled': prefs.email_enabled,
                'in_app_enabled': prefs.in_app_enabled,
                'permission_expiry_days': expiry_days,
                'high_risk_immediate': prefs.high_risk_immediate,
                'digest_frequency': prefs.digest_frequency,
                'quiet_hours_start': prefs.quiet_hours_start.isoformat() if prefs.quiet_hours_start else None,
                'quiet_hours_end': prefs.quiet_hours_end.isoformat() if prefs.quiet_hours_end else None
            }
        else:
            # Default preferences
            preferences = {
                'email_enabled': True,
                'in_app_enabled': True,
                'permission_expiry_days': self.default_warning_days,
                'high_risk_immediate': True,
                'digest_frequency': 'daily',
                'quiet_hours_start': None,
                'quiet_hours_end': None
            }
        
        # Cache preferences
        if cache_manager:
            await cache_manager.set(cache_key, json.dumps(preferences), 3600)
        
        return preferences
    
    async def update_user_notification_preferences(self, user_id: UUID, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user notification preferences.
        
        Args:
            user_id: User ID
            preferences: New preferences
            
        Returns:
            Update result
        """
        try:
            # Check if preferences exist
            query = select(NotificationPreference).where(
                NotificationPreference.user_id == user_id
            )
            result = await self.session.execute(query)
            existing_prefs = result.scalar_one_or_none()
            
            if existing_prefs:
                # Update existing preferences
                existing_prefs.email_enabled = preferences.get('email_enabled', existing_prefs.email_enabled)
                existing_prefs.in_app_enabled = preferences.get('in_app_enabled', existing_prefs.in_app_enabled)
                expiry_days = preferences.get('permission_expiry_days', existing_prefs.permission_expiry_days)
                if isinstance(expiry_days, list):
                    expiry_days = json.dumps(expiry_days)
                existing_prefs.permission_expiry_days = expiry_days
                existing_prefs.high_risk_immediate = preferences.get('high_risk_immediate', existing_prefs.high_risk_immediate)
                existing_prefs.digest_frequency = preferences.get('digest_frequency', existing_prefs.digest_frequency)
                existing_prefs.quiet_hours_start = preferences.get('quiet_hours_start', existing_prefs.quiet_hours_start)
                existing_prefs.quiet_hours_end = preferences.get('quiet_hours_end', existing_prefs.quiet_hours_end)
                existing_prefs.updated_at = datetime.utcnow()
            else:
                # Create new preferences
                expiry_days = preferences.get('permission_expiry_days', self.default_warning_days)
                if isinstance(expiry_days, list):
                    expiry_days = json.dumps(expiry_days)
                
                new_prefs = NotificationPreference(
                    user_id=user_id,
                    email_enabled=preferences.get('email_enabled', True),
                    in_app_enabled=preferences.get('in_app_enabled', True),
                    permission_expiry_days=expiry_days,
                    high_risk_immediate=preferences.get('high_risk_immediate', True),
                    digest_frequency=preferences.get('digest_frequency', 'daily'),
                    quiet_hours_start=preferences.get('quiet_hours_start'),
                    quiet_hours_end=preferences.get('quiet_hours_end')
                )
                self.session.add(new_prefs)
            
            await self.session.commit()
            
            # Invalidate cache
            if cache_manager:
                cache_key = self.user_prefs_cache_key(user_id)
                await cache_manager.delete(cache_key)
            
            return {
                'success': True,
                'message': 'Notification preferences updated successfully'
            }
            
        except Exception as e:
            await self.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    # Notification history and management
    async def get_user_notifications(self, user_id: UUID, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get user's notification history.
        
        Args:
            user_id: User ID
            limit: Number of notifications to return
            offset: Offset for pagination
            
        Returns:
            List of user notifications
        """
        query = select(PermissionNotification).where(
            PermissionNotification.user_id == user_id
        ).order_by(
            PermissionNotification.created_at.desc()
        ).limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        notifications = result.scalars().all()
        
        return [
            {
                'id': str(notif.id),
                'notification_type': notif.notification_type,
                'channel': notif.channel,
                'title': notif.title,
                'message': notif.message,
                'content': json.loads(notif.content) if notif.content else None,
                'is_read': notif.is_read,
                'created_at': notif.created_at,
                'read_at': notif.read_at
            }
            for notif in notifications
        ]
    
    async def mark_notification_as_read(self, notification_id: UUID, user_id: UUID) -> Dict[str, Any]:
        """
        Mark a notification as read.
        
        Args:
            notification_id: Notification ID
            user_id: User ID (for security)
            
        Returns:
            Mark read result
        """
        try:
            query = select(PermissionNotification).where(
                and_(
                    PermissionNotification.id == notification_id,
                    PermissionNotification.user_id == user_id
                )
            )
            
            result = await self.session.execute(query)
            notification = result.scalar_one_or_none()
            
            if not notification:
                return {
                    'success': False,
                    'error': 'Notification not found'
                }
            
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            
            await self.session.commit()
            
            return {
                'success': True,
                'message': 'Notification marked as read'
            }
            
        except Exception as e:
            await self.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    # Utility methods
    async def _is_notification_already_sent(self, user_id: UUID, permission_id: UUID, days_ahead: int) -> bool:
        """Check if notification was already sent for this combination."""
        query = select(PermissionNotification).where(
            and_(
                PermissionNotification.user_id == user_id,
                PermissionNotification.permission_id == permission_id,
                PermissionNotification.days_ahead == days_ahead,
                PermissionNotification.created_at >= datetime.utcnow() - timedelta(days=1)
            )
        )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def _record_notification(
        self,
        user_id: UUID,
        permission_id: UUID,
        notification_type: str,
        channel: str,
        days_ahead: int,
        content: str,
        related_user_id: Optional[UUID] = None
    ) -> None:
        """Record notification in database."""
        notification = PermissionNotification(
            user_id=user_id,
            permission_id=permission_id,
            notification_type=notification_type,
            channel=channel,
            days_ahead=days_ahead,
            content=content,
            related_user_id=related_user_id
        )
        
        self.session.add(notification)
        await self.session.commit()
    
    async def _get_admin_users(self) -> List[Dict[str, Any]]:
        """Get all admin users for notifications."""
        query = select(User).where(
            and_(
                User.user_type.in_(['ADMIN', 'SUPERADMIN']),
                User.is_active == True
            )
        )
        
        result = await self.session.execute(query)
        admin_users = result.scalars().all()
        
        return [
            {
                'id': admin.id,
                'username': admin.username,
                'email': admin.email,
                'user_type': admin.user_type
            }
            for admin in admin_users
        ]
    
    def _generate_email_content(self, perm_info: Dict[str, Any], days_ahead: int, urgency: str) -> str:
        """Generate email content for permission expiration."""
        return f"""
        Dear {perm_info['first_name']} {perm_info['last_name']},
        
        This is a {urgency} notification that your permission is expiring soon.
        
        Permission Details:
        - Permission: {perm_info['permission_name']}
        - Code: {perm_info['permission_code']}
        - Risk Level: {perm_info['risk_level']}
        - Expires: {perm_info['expires_at'].strftime('%Y-%m-%d %H:%M:%S')}
        - Days Until Expiry: {days_ahead}
        
        Please contact your administrator if you need to extend this permission.
        
        Best regards,
        System Administrator
        """
    
    async def _simulate_email_send(self, email: str, subject: str, content: str) -> None:
        """Simulate email sending (replace with actual email service)."""
        # TODO: Integrate with actual email service (SendGrid, SES, etc.)
        print(f"EMAIL SIMULATION: Sending to {email}")
        print(f"Subject: {subject}")
        print(f"Content: {content[:100]}...")
        await asyncio.sleep(0.1)  # Simulate email sending delay
    
    # Scheduled task methods
    async def run_scheduled_notification_check(self) -> Dict[str, Any]:
        """
        Run scheduled notification check (typically called by cron job).
        
        Returns:
            Processing results
        """
        start_time = datetime.utcnow()
        
        try:
            # Process expiration notifications
            results = await self.process_expiration_notifications()
            
            # Update statistics
            await self._update_notification_stats(results)
            
            # Log audit entry
            await self._log_notification_batch_audit(results, start_time)
            
            return {
                'success': True,
                'processing_time': (datetime.utcnow() - start_time).total_seconds(),
                'results': results
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'processing_time': (datetime.utcnow() - start_time).total_seconds()
            }
    
    async def _update_notification_stats(self, results: Dict[str, Any]) -> None:
        """Update notification statistics."""
        stats_key = self.notification_stats_key
        
        # Get current stats
        current_stats = None
        if cache_manager:
            current_stats = await cache_manager.get(stats_key)
        if current_stats:
            stats = json.loads(current_stats)
        else:
            stats = {
                'total_processed': 0,
                'total_notifications_sent': 0,
                'notifications_by_channel': {},
                'last_run': None
            }
        
        # Update stats
        stats['total_processed'] += results['processed']
        stats['total_notifications_sent'] += results['notifications_sent']
        stats['last_run'] = datetime.utcnow().isoformat()
        
        # Update channel stats
        for channel, count in results['notifications_by_type'].items():
            if channel not in stats['notifications_by_channel']:
                stats['notifications_by_channel'][channel] = 0
            stats['notifications_by_channel'][channel] += count
        
        # Cache for 24 hours
        if cache_manager:
            await cache_manager.set(stats_key, json.dumps(stats), 86400)
    
    async def _log_notification_batch_audit(self, results: Dict[str, Any], start_time: datetime) -> None:
        """Log notification batch processing audit."""
        audit_log = RBACauditlog(
            action="NOTIFICATION_BATCH_PROCESSED",
            entity_type="NOTIFICATION_SYSTEM",
            changes=json.dumps({
                'processed': results['processed'],
                'notifications_sent': results['notifications_sent'],
                'notifications_by_type': results['notifications_by_type'],
                'errors_count': len(results['errors']),
                'processing_time_seconds': (datetime.utcnow() - start_time).total_seconds()
            }),
            timestamp=datetime.utcnow(),
            success=True
        )
        
        self.session.add(audit_log)
        await self.session.commit()
    
    async def get_notification_statistics(self) -> Dict[str, Any]:
        """Get notification system statistics."""
        stats_key = self.notification_stats_key
        cached_stats = None
        if cache_manager:
            cached_stats = await cache_manager.get(stats_key)
        
        if cached_stats:
            return json.loads(cached_stats)
        
        return {
            'total_processed': 0,
            'total_notifications_sent': 0,
            'notifications_by_channel': {},
            'last_run': None,
            'message': 'No statistics available yet'
        }