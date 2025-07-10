#!/usr/bin/env python3
"""
RBAC Notification Scheduler

This script is designed to be run as a scheduled task (cron job) to check for
expiring permissions and send notifications to users and administrators.

Usage:
    python notification_scheduler.py [--dry-run] [--verbose]

Options:
    --dry-run    : Run without actually sending notifications
    --verbose    : Enable verbose logging
"""

import asyncio
import argparse
import sys
import logging
from datetime import datetime
from pathlib import Path

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from app.db.session import get_session
from app.modules.auth.notification_service import NotificationService
from app.modules.auth.rbac_service import RBACService


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('notification_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def run_notification_check(dry_run: bool = False, verbose: bool = False):
    """
    Run the notification check process.
    
    Args:
        dry_run: If True, don't actually send notifications
        verbose: If True, enable verbose logging
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Starting RBAC notification check process")
    start_time = datetime.utcnow()
    
    try:
        # Get database session
        async for session in get_session():
            notification_service = NotificationService(session)
            
            if dry_run:
                logger.info("DRY RUN MODE: No notifications will be sent")
                
                # Check expiring permissions for different time periods
                for days_ahead in [1, 3, 7, 30]:
                    expiring_permissions = await notification_service.check_expiring_permissions(days_ahead)
                    logger.info(f"Found {len(expiring_permissions)} permissions expiring in {days_ahead} days")
                    
                    if verbose and expiring_permissions:
                        for perm in expiring_permissions[:5]:  # Show first 5 for brevity
                            logger.debug(f"  - User: {perm['username']}, Permission: {perm['permission_name']}, "
                                       f"Risk: {perm['risk_level']}, Expires: {perm['expires_at']}")
                
                # Get notification statistics
                stats = await notification_service.get_notification_statistics()
                logger.info(f"Notification statistics: {stats}")
                
            else:
                # Run actual notification processing
                logger.info("Processing expiration notifications...")
                results = await notification_service.run_scheduled_notification_check()
                
                if results['success']:
                    logger.info(f"Notification check completed successfully")
                    logger.info(f"Processing time: {results['processing_time']:.2f} seconds")
                    logger.info(f"Processed: {results['results']['processed']} permissions")
                    logger.info(f"Notifications sent: {results['results']['notifications_sent']}")
                    logger.info(f"Notifications by type: {results['results']['notifications_by_type']}")
                    
                    # Log any errors
                    if results['results']['errors']:
                        logger.warning(f"Errors encountered: {len(results['results']['errors'])}")
                        for error in results['results']['errors']:
                            logger.error(f"Error: {error}")
                    
                else:
                    logger.error(f"Notification check failed: {results['error']}")
                    logger.error(f"Processing time: {results['processing_time']:.2f} seconds")
                    return False
            
            break  # Exit the async generator
    
    except Exception as e:
        logger.error(f"Unexpected error during notification check: {e}")
        logger.exception("Exception details:")
        return False
    
    finally:
        end_time = datetime.utcnow()
        total_time = (end_time - start_time).total_seconds()
        logger.info(f"Notification check process completed in {total_time:.2f} seconds")
    
    return True


async def run_notification_health_check():
    """
    Run a health check on the notification system.
    """
    logger.info("Running notification system health check")
    
    try:
        async for session in get_session():
            notification_service = NotificationService(session)
            
            # Check basic system health
            stats = await notification_service.get_notification_statistics()
            logger.info(f"System statistics: {stats}")
            
            # Check for any stuck notifications or issues
            current_time = datetime.utcnow()
            
            # Check for permissions expiring today (high priority)
            expiring_today = await notification_service.check_expiring_permissions(0)
            if expiring_today:
                logger.warning(f"⚠️  {len(expiring_today)} permissions expire today!")
                for perm in expiring_today:
                    if perm['risk_level'] in ['HIGH', 'CRITICAL']:
                        logger.critical(f"🚨 CRITICAL: {perm['username']} - {perm['permission_name']} "
                                      f"({perm['risk_level']}) expires today!")
            
            # Check for permissions expiring tomorrow (medium priority)
            expiring_tomorrow = await notification_service.check_expiring_permissions(1)
            if expiring_tomorrow:
                logger.info(f"📅 {len(expiring_tomorrow)} permissions expire tomorrow")
            
            # Check for high-risk permissions expiring soon
            expiring_week = await notification_service.check_expiring_permissions(7)
            high_risk_expiring = [p for p in expiring_week if p['risk_level'] in ['HIGH', 'CRITICAL']]
            if high_risk_expiring:
                logger.warning(f"⚠️  {len(high_risk_expiring)} high-risk permissions expire within 7 days")
            
            logger.info("Health check completed successfully")
            break
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        logger.exception("Exception details:")
        return False
    
    return True


async def cleanup_old_notifications(days_old: int = 90):
    """
    Clean up old notifications to keep database size manageable.
    
    Args:
        days_old: Delete notifications older than this many days
    """
    logger.info(f"Cleaning up notifications older than {days_old} days")
    
    try:
        async for session in get_session():
            from app.modules.auth.models import PermissionNotification
            from sqlalchemy import select, and_
            from datetime import timedelta
            
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Get count of old notifications
            count_query = select(PermissionNotification).where(
                and_(
                    PermissionNotification.created_at < cutoff_date,
                    PermissionNotification.is_read == True  # Only delete read notifications
                )
            )
            
            result = await session.execute(count_query)
            old_notifications = result.scalars().all()
            
            if old_notifications:
                logger.info(f"Found {len(old_notifications)} old notifications to delete")
                
                # Delete old notifications
                for notification in old_notifications:
                    await session.delete(notification)
                
                await session.commit()
                logger.info(f"Deleted {len(old_notifications)} old notifications")
            else:
                logger.info("No old notifications to clean up")
            
            break
            
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        logger.exception("Exception details:")
        return False
    
    return True


def main():
    """Main entry point for the notification scheduler."""
    parser = argparse.ArgumentParser(description='RBAC Notification Scheduler')
    parser.add_argument('--dry-run', action='store_true', help='Run without sending notifications')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--health-check', action='store_true', help='Run health check only')
    parser.add_argument('--cleanup', action='store_true', help='Clean up old notifications')
    parser.add_argument('--cleanup-days', type=int, default=90, help='Days old for cleanup (default: 90)')
    
    args = parser.parse_args()
    
    # Set up logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("RBAC Notification Scheduler started")
    logger.info(f"Arguments: {args}")
    
    success = True
    
    try:
        if args.health_check:
            success = asyncio.run(run_notification_health_check())
        elif args.cleanup:
            success = asyncio.run(cleanup_old_notifications(args.cleanup_days))
        else:
            success = asyncio.run(run_notification_check(args.dry_run, args.verbose))
        
        if success:
            logger.info("Scheduler completed successfully")
            sys.exit(0)
        else:
            logger.error("Scheduler completed with errors")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Scheduler interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Scheduler failed with unexpected error: {e}")
        logger.exception("Exception details:")
        sys.exit(1)


if __name__ == "__main__":
    main()