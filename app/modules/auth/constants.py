"""Authentication and authorization constants."""

from enum import Enum
from typing import Dict, List, Set


class UserType(str, Enum):
    """User type hierarchy for organizational structure."""
    SUPERADMIN = "SUPERADMIN"
    ADMIN = "ADMIN"
    USER = "USER"
    CUSTOMER = "CUSTOMER"


class PermissionRiskLevel(str, Enum):
    """Permission risk level classification."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class NotificationType(str, Enum):
    """Notification type classification."""
    PERMISSION_EXPIRING = "PERMISSION_EXPIRING"
    PERMISSION_EXPIRED = "PERMISSION_EXPIRED"
    PERMISSION_GRANTED = "PERMISSION_GRANTED"
    PERMISSION_REVOKED = "PERMISSION_REVOKED"
    ADMIN_ALERT = "ADMIN_ALERT"
    ROLE_ASSIGNED = "ROLE_ASSIGNED"
    ROLE_REMOVED = "ROLE_REMOVED"
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
    ACCOUNT_UNLOCKED = "ACCOUNT_UNLOCKED"


class NotificationChannel(str, Enum):
    """Notification channel classification."""
    EMAIL = "EMAIL"
    IN_APP = "IN_APP"
    SMS = "SMS"
    WEBHOOK = "WEBHOOK"
    PUSH = "PUSH"


class RoleTemplate(str, Enum):
    """Pre-defined role templates for standardized access patterns."""
    SUPERADMIN = "SUPERADMIN"
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    STAFF = "STAFF"
    CUSTOMER = "CUSTOMER"
    AUDITOR = "AUDITOR"
    ACCOUNTANT = "ACCOUNTANT"


class PermissionCategory(str, Enum):
    """Permission categories for organizational structure."""
    SYSTEM = "SYSTEM"
    USER_MANAGEMENT = "USER_MANAGEMENT"
    ROLE_MANAGEMENT = "ROLE_MANAGEMENT"
    PROPERTY_MANAGEMENT = "PROPERTY_MANAGEMENT"
    INVENTORY = "INVENTORY"
    SALES = "SALES"
    PURCHASES = "PURCHASES"
    FINANCIAL = "FINANCIAL"
    REPORTING = "REPORTING"
    MAINTENANCE = "MAINTENANCE"
    CUSTOMER_SUPPORT = "CUSTOMER_SUPPORT"
    ANALYTICS = "ANALYTICS"
    AUDIT = "AUDIT"
    BACKUP = "BACKUP"
    INTEGRATION = "INTEGRATION"


class Permission:
    """Permission constants with comprehensive business operations."""
    
    # System permissions
    SYSTEM_CONFIG_READ = "SYSTEM_CONFIG_READ"
    SYSTEM_CONFIG_WRITE = "SYSTEM_CONFIG_WRITE"
    SYSTEM_HEALTH_CHECK = "SYSTEM_HEALTH_CHECK"
    SYSTEM_BACKUP = "SYSTEM_BACKUP"
    SYSTEM_RESTORE = "SYSTEM_RESTORE"
    SYSTEM_MAINTENANCE = "SYSTEM_MAINTENANCE"
    SYSTEM_SHUTDOWN = "SYSTEM_SHUTDOWN"
    
    # User management permissions
    USER_CREATE = "USER_CREATE"
    USER_READ = "USER_READ"
    USER_UPDATE = "USER_UPDATE"
    USER_DELETE = "USER_DELETE"
    USER_LIST = "USER_LIST"
    USER_ACTIVATE = "USER_ACTIVATE"
    USER_DEACTIVATE = "USER_DEACTIVATE"
    USER_LOCK = "USER_LOCK"
    USER_UNLOCK = "USER_UNLOCK"
    USER_RESET_PASSWORD = "USER_RESET_PASSWORD"
    USER_CHANGE_PASSWORD = "USER_CHANGE_PASSWORD"
    USER_IMPERSONATE = "USER_IMPERSONATE"
    USER_VIEW_PROFILE = "USER_VIEW_PROFILE"
    USER_EDIT_PROFILE = "USER_EDIT_PROFILE"
    
    # Role management permissions
    ROLE_CREATE = "ROLE_CREATE"
    ROLE_READ = "ROLE_READ"
    ROLE_UPDATE = "ROLE_UPDATE"
    ROLE_DELETE = "ROLE_DELETE"
    ROLE_LIST = "ROLE_LIST"
    ROLE_ASSIGN = "ROLE_ASSIGN"
    ROLE_REVOKE = "ROLE_REVOKE"
    ROLE_MANAGE_PERMISSIONS = "ROLE_MANAGE_PERMISSIONS"
    
    # Permission management
    PERMISSION_CREATE = "PERMISSION_CREATE"
    PERMISSION_READ = "PERMISSION_READ"
    PERMISSION_UPDATE = "PERMISSION_UPDATE"
    PERMISSION_DELETE = "PERMISSION_DELETE"
    PERMISSION_LIST = "PERMISSION_LIST"
    PERMISSION_ASSIGN = "PERMISSION_ASSIGN"
    PERMISSION_REVOKE = "PERMISSION_REVOKE"
    
    # Property management permissions
    PROPERTY_CREATE = "PROPERTY_CREATE"
    PROPERTY_READ = "PROPERTY_READ"
    PROPERTY_UPDATE = "PROPERTY_UPDATE"
    PROPERTY_DELETE = "PROPERTY_DELETE"
    PROPERTY_LIST = "PROPERTY_LIST"
    PROPERTY_SEARCH = "PROPERTY_SEARCH"
    PROPERTY_IMPORT = "PROPERTY_IMPORT"
    PROPERTY_EXPORT = "PROPERTY_EXPORT"
    PROPERTY_BULK_UPDATE = "PROPERTY_BULK_UPDATE"
    PROPERTY_STATUS_CHANGE = "PROPERTY_STATUS_CHANGE"
    
    # Inventory permissions
    INVENTORY_CREATE = "INVENTORY_CREATE"
    INVENTORY_READ = "INVENTORY_READ"
    INVENTORY_UPDATE = "INVENTORY_UPDATE"
    INVENTORY_DELETE = "INVENTORY_DELETE"
    INVENTORY_LIST = "INVENTORY_LIST"
    INVENTORY_ADJUST = "INVENTORY_ADJUST"
    INVENTORY_TRANSFER = "INVENTORY_TRANSFER"
    INVENTORY_COUNT = "INVENTORY_COUNT"
    INVENTORY_VALUATION = "INVENTORY_VALUATION"
    INVENTORY_REPORT = "INVENTORY_REPORT"
    
    # Sales permissions
    SALE_CREATE = "SALE_CREATE"
    SALE_READ = "SALE_READ"
    SALE_UPDATE = "SALE_UPDATE"
    SALE_DELETE = "SALE_DELETE"
    SALE_LIST = "SALE_LIST"
    SALE_APPROVE = "SALE_APPROVE"
    SALE_CANCEL = "SALE_CANCEL"
    SALE_REFUND = "SALE_REFUND"
    SALE_DISCOUNT = "SALE_DISCOUNT"
    SALE_REPORT = "SALE_REPORT"
    
    # Purchase permissions
    PURCHASE_CREATE = "PURCHASE_CREATE"
    PURCHASE_READ = "PURCHASE_READ"
    PURCHASE_UPDATE = "PURCHASE_UPDATE"
    PURCHASE_DELETE = "PURCHASE_DELETE"
    PURCHASE_LIST = "PURCHASE_LIST"
    PURCHASE_APPROVE = "PURCHASE_APPROVE"
    PURCHASE_CANCEL = "PURCHASE_CANCEL"
    PURCHASE_RECEIVE = "PURCHASE_RECEIVE"
    PURCHASE_RETURN = "PURCHASE_RETURN"
    PURCHASE_REPORT = "PURCHASE_REPORT"
    
    # Financial permissions
    FINANCIAL_VIEW = "FINANCIAL_VIEW"
    FINANCIAL_CREATE = "FINANCIAL_CREATE"
    FINANCIAL_UPDATE = "FINANCIAL_UPDATE"
    FINANCIAL_DELETE = "FINANCIAL_DELETE"
    FINANCIAL_APPROVE = "FINANCIAL_APPROVE"
    FINANCIAL_RECONCILE = "FINANCIAL_RECONCILE"
    FINANCIAL_REPORT = "FINANCIAL_REPORT"
    FINANCIAL_BUDGET = "FINANCIAL_BUDGET"
    FINANCIAL_FORECAST = "FINANCIAL_FORECAST"
    FINANCIAL_AUDIT = "FINANCIAL_AUDIT"
    
    # Reporting permissions
    REPORT_VIEW = "REPORT_VIEW"
    REPORT_CREATE = "REPORT_CREATE"
    REPORT_EDIT = "REPORT_EDIT"
    REPORT_DELETE = "REPORT_DELETE"
    REPORT_EXPORT = "REPORT_EXPORT"
    REPORT_SCHEDULE = "REPORT_SCHEDULE"
    REPORT_SHARE = "REPORT_SHARE"
    REPORT_DASHBOARD = "REPORT_DASHBOARD"
    
    # Maintenance permissions
    MAINTENANCE_CREATE = "MAINTENANCE_CREATE"
    MAINTENANCE_READ = "MAINTENANCE_READ"
    MAINTENANCE_UPDATE = "MAINTENANCE_UPDATE"
    MAINTENANCE_DELETE = "MAINTENANCE_DELETE"
    MAINTENANCE_LIST = "MAINTENANCE_LIST"
    MAINTENANCE_SCHEDULE = "MAINTENANCE_SCHEDULE"
    MAINTENANCE_APPROVE = "MAINTENANCE_APPROVE"
    MAINTENANCE_COMPLETE = "MAINTENANCE_COMPLETE"
    MAINTENANCE_REPORT = "MAINTENANCE_REPORT"
    
    # Customer support permissions
    SUPPORT_VIEW = "SUPPORT_VIEW"
    SUPPORT_CREATE = "SUPPORT_CREATE"
    SUPPORT_UPDATE = "SUPPORT_UPDATE"
    SUPPORT_DELETE = "SUPPORT_DELETE"
    SUPPORT_ASSIGN = "SUPPORT_ASSIGN"
    SUPPORT_ESCALATE = "SUPPORT_ESCALATE"
    SUPPORT_CLOSE = "SUPPORT_CLOSE"
    SUPPORT_REPORT = "SUPPORT_REPORT"
    
    # Analytics permissions
    ANALYTICS_VIEW = "ANALYTICS_VIEW"
    ANALYTICS_CREATE = "ANALYTICS_CREATE"
    ANALYTICS_UPDATE = "ANALYTICS_UPDATE"
    ANALYTICS_DELETE = "ANALYTICS_DELETE"
    ANALYTICS_EXPORT = "ANALYTICS_EXPORT"
    ANALYTICS_SHARE = "ANALYTICS_SHARE"
    ANALYTICS_DASHBOARD = "ANALYTICS_DASHBOARD"
    
    # Audit permissions
    AUDIT_VIEW = "AUDIT_VIEW"
    AUDIT_CREATE = "AUDIT_CREATE"
    AUDIT_UPDATE = "AUDIT_UPDATE"
    AUDIT_DELETE = "AUDIT_DELETE"
    AUDIT_EXPORT = "AUDIT_EXPORT"
    AUDIT_REPORT = "AUDIT_REPORT"
    AUDIT_TRAIL = "AUDIT_TRAIL"
    
    # Backup permissions
    BACKUP_CREATE = "BACKUP_CREATE"
    BACKUP_RESTORE = "BACKUP_RESTORE"
    BACKUP_DELETE = "BACKUP_DELETE"
    BACKUP_LIST = "BACKUP_LIST"
    BACKUP_SCHEDULE = "BACKUP_SCHEDULE"
    BACKUP_DOWNLOAD = "BACKUP_DOWNLOAD"
    
    # Integration permissions
    INTEGRATION_VIEW = "INTEGRATION_VIEW"
    INTEGRATION_CREATE = "INTEGRATION_CREATE"
    INTEGRATION_UPDATE = "INTEGRATION_UPDATE"
    INTEGRATION_DELETE = "INTEGRATION_DELETE"
    INTEGRATION_EXECUTE = "INTEGRATION_EXECUTE"
    INTEGRATION_MONITOR = "INTEGRATION_MONITOR"
    INTEGRATION_LOG = "INTEGRATION_LOG"


# Permission categories mapping
PERMISSION_CATEGORIES = {
    PermissionCategory.SYSTEM: [
        Permission.SYSTEM_CONFIG_READ,
        Permission.SYSTEM_CONFIG_WRITE,
        Permission.SYSTEM_HEALTH_CHECK,
        Permission.SYSTEM_BACKUP,
        Permission.SYSTEM_RESTORE,
        Permission.SYSTEM_MAINTENANCE,
        Permission.SYSTEM_SHUTDOWN,
    ],
    PermissionCategory.USER_MANAGEMENT: [
        Permission.USER_CREATE,
        Permission.USER_READ,
        Permission.USER_UPDATE,
        Permission.USER_DELETE,
        Permission.USER_LIST,
        Permission.USER_ACTIVATE,
        Permission.USER_DEACTIVATE,
        Permission.USER_LOCK,
        Permission.USER_UNLOCK,
        Permission.USER_RESET_PASSWORD,
        Permission.USER_CHANGE_PASSWORD,
        Permission.USER_IMPERSONATE,
        Permission.USER_VIEW_PROFILE,
        Permission.USER_EDIT_PROFILE,
    ],
    PermissionCategory.ROLE_MANAGEMENT: [
        Permission.ROLE_CREATE,
        Permission.ROLE_READ,
        Permission.ROLE_UPDATE,
        Permission.ROLE_DELETE,
        Permission.ROLE_LIST,
        Permission.ROLE_ASSIGN,
        Permission.ROLE_REVOKE,
        Permission.ROLE_MANAGE_PERMISSIONS,
        Permission.PERMISSION_CREATE,
        Permission.PERMISSION_READ,
        Permission.PERMISSION_UPDATE,
        Permission.PERMISSION_DELETE,
        Permission.PERMISSION_LIST,
        Permission.PERMISSION_ASSIGN,
        Permission.PERMISSION_REVOKE,
    ],
    PermissionCategory.PROPERTY_MANAGEMENT: [
        Permission.PROPERTY_CREATE,
        Permission.PROPERTY_READ,
        Permission.PROPERTY_UPDATE,
        Permission.PROPERTY_DELETE,
        Permission.PROPERTY_LIST,
        Permission.PROPERTY_SEARCH,
        Permission.PROPERTY_IMPORT,
        Permission.PROPERTY_EXPORT,
        Permission.PROPERTY_BULK_UPDATE,
        Permission.PROPERTY_STATUS_CHANGE,
    ],
    PermissionCategory.INVENTORY: [
        Permission.INVENTORY_CREATE,
        Permission.INVENTORY_READ,
        Permission.INVENTORY_UPDATE,
        Permission.INVENTORY_DELETE,
        Permission.INVENTORY_LIST,
        Permission.INVENTORY_ADJUST,
        Permission.INVENTORY_TRANSFER,
        Permission.INVENTORY_COUNT,
        Permission.INVENTORY_VALUATION,
        Permission.INVENTORY_REPORT,
    ],
    PermissionCategory.SALES: [
        Permission.SALE_CREATE,
        Permission.SALE_READ,
        Permission.SALE_UPDATE,
        Permission.SALE_DELETE,
        Permission.SALE_LIST,
        Permission.SALE_APPROVE,
        Permission.SALE_CANCEL,
        Permission.SALE_REFUND,
        Permission.SALE_DISCOUNT,
        Permission.SALE_REPORT,
    ],
    PermissionCategory.PURCHASES: [
        Permission.PURCHASE_CREATE,
        Permission.PURCHASE_READ,
        Permission.PURCHASE_UPDATE,
        Permission.PURCHASE_DELETE,
        Permission.PURCHASE_LIST,
        Permission.PURCHASE_APPROVE,
        Permission.PURCHASE_CANCEL,
        Permission.PURCHASE_RECEIVE,
        Permission.PURCHASE_RETURN,
        Permission.PURCHASE_REPORT,
    ],
    PermissionCategory.FINANCIAL: [
        Permission.FINANCIAL_VIEW,
        Permission.FINANCIAL_CREATE,
        Permission.FINANCIAL_UPDATE,
        Permission.FINANCIAL_DELETE,
        Permission.FINANCIAL_APPROVE,
        Permission.FINANCIAL_RECONCILE,
        Permission.FINANCIAL_REPORT,
        Permission.FINANCIAL_BUDGET,
        Permission.FINANCIAL_FORECAST,
        Permission.FINANCIAL_AUDIT,
    ],
    PermissionCategory.REPORTING: [
        Permission.REPORT_VIEW,
        Permission.REPORT_CREATE,
        Permission.REPORT_EDIT,
        Permission.REPORT_DELETE,
        Permission.REPORT_EXPORT,
        Permission.REPORT_SCHEDULE,
        Permission.REPORT_SHARE,
        Permission.REPORT_DASHBOARD,
    ],
    PermissionCategory.MAINTENANCE: [
        Permission.MAINTENANCE_CREATE,
        Permission.MAINTENANCE_READ,
        Permission.MAINTENANCE_UPDATE,
        Permission.MAINTENANCE_DELETE,
        Permission.MAINTENANCE_LIST,
        Permission.MAINTENANCE_SCHEDULE,
        Permission.MAINTENANCE_APPROVE,
        Permission.MAINTENANCE_COMPLETE,
        Permission.MAINTENANCE_REPORT,
    ],
    PermissionCategory.CUSTOMER_SUPPORT: [
        Permission.SUPPORT_VIEW,
        Permission.SUPPORT_CREATE,
        Permission.SUPPORT_UPDATE,
        Permission.SUPPORT_DELETE,
        Permission.SUPPORT_ASSIGN,
        Permission.SUPPORT_ESCALATE,
        Permission.SUPPORT_CLOSE,
        Permission.SUPPORT_REPORT,
    ],
    PermissionCategory.ANALYTICS: [
        Permission.ANALYTICS_VIEW,
        Permission.ANALYTICS_CREATE,
        Permission.ANALYTICS_UPDATE,
        Permission.ANALYTICS_DELETE,
        Permission.ANALYTICS_EXPORT,
        Permission.ANALYTICS_SHARE,
        Permission.ANALYTICS_DASHBOARD,
    ],
    PermissionCategory.AUDIT: [
        Permission.AUDIT_VIEW,
        Permission.AUDIT_CREATE,
        Permission.AUDIT_UPDATE,
        Permission.AUDIT_DELETE,
        Permission.AUDIT_EXPORT,
        Permission.AUDIT_REPORT,
        Permission.AUDIT_TRAIL,
    ],
    PermissionCategory.BACKUP: [
        Permission.BACKUP_CREATE,
        Permission.BACKUP_RESTORE,
        Permission.BACKUP_DELETE,
        Permission.BACKUP_LIST,
        Permission.BACKUP_SCHEDULE,
        Permission.BACKUP_DOWNLOAD,
    ],
    PermissionCategory.INTEGRATION: [
        Permission.INTEGRATION_VIEW,
        Permission.INTEGRATION_CREATE,
        Permission.INTEGRATION_UPDATE,
        Permission.INTEGRATION_DELETE,
        Permission.INTEGRATION_EXECUTE,
        Permission.INTEGRATION_MONITOR,
        Permission.INTEGRATION_LOG,
    ],
}


# Permission risk levels
PERMISSION_RISK_LEVELS = {
    # Critical risk permissions
    Permission.SYSTEM_SHUTDOWN: PermissionRiskLevel.CRITICAL,
    Permission.SYSTEM_BACKUP: PermissionRiskLevel.CRITICAL,
    Permission.SYSTEM_RESTORE: PermissionRiskLevel.CRITICAL,
    Permission.USER_DELETE: PermissionRiskLevel.CRITICAL,
    Permission.USER_IMPERSONATE: PermissionRiskLevel.CRITICAL,
    Permission.ROLE_DELETE: PermissionRiskLevel.CRITICAL,
    Permission.PERMISSION_DELETE: PermissionRiskLevel.CRITICAL,
    
    # High risk permissions
    Permission.SYSTEM_CONFIG_WRITE: PermissionRiskLevel.HIGH,
    Permission.SYSTEM_MAINTENANCE: PermissionRiskLevel.HIGH,
    Permission.USER_CREATE: PermissionRiskLevel.HIGH,
    Permission.USER_RESET_PASSWORD: PermissionRiskLevel.HIGH,
    Permission.ROLE_CREATE: PermissionRiskLevel.HIGH,
    Permission.ROLE_MANAGE_PERMISSIONS: PermissionRiskLevel.HIGH,
    Permission.PERMISSION_CREATE: PermissionRiskLevel.HIGH,
    Permission.FINANCIAL_DELETE: PermissionRiskLevel.HIGH,
    Permission.FINANCIAL_APPROVE: PermissionRiskLevel.HIGH,
    
    # Medium risk permissions
    Permission.USER_UPDATE: PermissionRiskLevel.MEDIUM,
    Permission.USER_LOCK: PermissionRiskLevel.MEDIUM,
    Permission.USER_UNLOCK: PermissionRiskLevel.MEDIUM,
    Permission.ROLE_UPDATE: PermissionRiskLevel.MEDIUM,
    Permission.PERMISSION_UPDATE: PermissionRiskLevel.MEDIUM,
    Permission.PROPERTY_DELETE: PermissionRiskLevel.MEDIUM,
    Permission.INVENTORY_DELETE: PermissionRiskLevel.MEDIUM,
    Permission.SALE_DELETE: PermissionRiskLevel.MEDIUM,
    Permission.PURCHASE_DELETE: PermissionRiskLevel.MEDIUM,
    Permission.FINANCIAL_UPDATE: PermissionRiskLevel.MEDIUM,
    
    # Low risk permissions (default for read operations)
}


# Permission dependencies
PERMISSION_DEPENDENCIES: Dict[str, Set[str]] = {
    Permission.USER_DELETE: {Permission.USER_READ, Permission.USER_UPDATE},
    Permission.USER_UPDATE: {Permission.USER_READ},
    Permission.USER_LOCK: {Permission.USER_READ},
    Permission.USER_UNLOCK: {Permission.USER_READ},
    Permission.USER_RESET_PASSWORD: {Permission.USER_READ},
    Permission.ROLE_DELETE: {Permission.ROLE_READ, Permission.ROLE_UPDATE},
    Permission.ROLE_UPDATE: {Permission.ROLE_READ},
    Permission.ROLE_MANAGE_PERMISSIONS: {Permission.ROLE_READ, Permission.PERMISSION_READ},
    Permission.PERMISSION_DELETE: {Permission.PERMISSION_READ, Permission.PERMISSION_UPDATE},
    Permission.PERMISSION_UPDATE: {Permission.PERMISSION_READ},
    Permission.SALE_CREATE: {Permission.SALE_READ, Permission.INVENTORY_READ},
    Permission.SALE_DELETE: {Permission.SALE_READ, Permission.SALE_UPDATE},
    Permission.SALE_UPDATE: {Permission.SALE_READ},
    Permission.PURCHASE_CREATE: {Permission.PURCHASE_READ, Permission.INVENTORY_READ},
    Permission.PURCHASE_DELETE: {Permission.PURCHASE_READ, Permission.PURCHASE_UPDATE},
    Permission.PURCHASE_UPDATE: {Permission.PURCHASE_READ},
    Permission.INVENTORY_ADJUST: {Permission.INVENTORY_READ, Permission.INVENTORY_UPDATE},
    Permission.INVENTORY_TRANSFER: {Permission.INVENTORY_READ, Permission.INVENTORY_UPDATE},
    Permission.INVENTORY_DELETE: {Permission.INVENTORY_READ, Permission.INVENTORY_UPDATE},
    Permission.PROPERTY_DELETE: {Permission.PROPERTY_READ, Permission.PROPERTY_UPDATE},
    Permission.PROPERTY_UPDATE: {Permission.PROPERTY_READ},
    Permission.FINANCIAL_DELETE: {Permission.FINANCIAL_VIEW, Permission.FINANCIAL_UPDATE},
    Permission.FINANCIAL_UPDATE: {Permission.FINANCIAL_VIEW},
    Permission.FINANCIAL_APPROVE: {Permission.FINANCIAL_VIEW},
}


# Role templates with default permissions
ROLE_TEMPLATES: Dict[RoleTemplate, List[str]] = {
    RoleTemplate.SUPERADMIN: [
        # All permissions - superadmin has unrestricted access
        *[perm for category_perms in PERMISSION_CATEGORIES.values() for perm in category_perms]
    ],
    RoleTemplate.ADMIN: [
        # System management
        Permission.SYSTEM_CONFIG_READ,
        Permission.SYSTEM_HEALTH_CHECK,
        Permission.SYSTEM_BACKUP,
        
        # User management
        Permission.USER_CREATE,
        Permission.USER_READ,
        Permission.USER_UPDATE,
        Permission.USER_DELETE,
        Permission.USER_LIST,
        Permission.USER_ACTIVATE,
        Permission.USER_DEACTIVATE,
        Permission.USER_LOCK,
        Permission.USER_UNLOCK,
        Permission.USER_RESET_PASSWORD,
        
        # Role management
        Permission.ROLE_CREATE,
        Permission.ROLE_READ,
        Permission.ROLE_UPDATE,
        Permission.ROLE_DELETE,
        Permission.ROLE_LIST,
        Permission.ROLE_ASSIGN,
        Permission.ROLE_REVOKE,
        Permission.ROLE_MANAGE_PERMISSIONS,
        
        # Permission management
        Permission.PERMISSION_CREATE,
        Permission.PERMISSION_READ,
        Permission.PERMISSION_UPDATE,
        Permission.PERMISSION_DELETE,
        Permission.PERMISSION_LIST,
        Permission.PERMISSION_ASSIGN,
        Permission.PERMISSION_REVOKE,
        
        # Business operations
        Permission.PROPERTY_CREATE,
        Permission.PROPERTY_READ,
        Permission.PROPERTY_UPDATE,
        Permission.PROPERTY_DELETE,
        Permission.PROPERTY_LIST,
        Permission.INVENTORY_CREATE,
        Permission.INVENTORY_READ,
        Permission.INVENTORY_UPDATE,
        Permission.INVENTORY_DELETE,
        Permission.INVENTORY_LIST,
        Permission.SALE_CREATE,
        Permission.SALE_READ,
        Permission.SALE_UPDATE,
        Permission.SALE_DELETE,
        Permission.SALE_LIST,
        Permission.PURCHASE_CREATE,
        Permission.PURCHASE_READ,
        Permission.PURCHASE_UPDATE,
        Permission.PURCHASE_DELETE,
        Permission.PURCHASE_LIST,
        
        # Financial
        Permission.FINANCIAL_VIEW,
        Permission.FINANCIAL_CREATE,
        Permission.FINANCIAL_UPDATE,
        Permission.FINANCIAL_DELETE,
        Permission.FINANCIAL_APPROVE,
        Permission.FINANCIAL_RECONCILE,
        Permission.FINANCIAL_REPORT,
        
        # Reporting
        Permission.REPORT_VIEW,
        Permission.REPORT_CREATE,
        Permission.REPORT_EDIT,
        Permission.REPORT_DELETE,
        Permission.REPORT_EXPORT,
        Permission.REPORT_SCHEDULE,
        Permission.REPORT_SHARE,
        Permission.REPORT_DASHBOARD,
        
        # Audit
        Permission.AUDIT_VIEW,
        Permission.AUDIT_EXPORT,
        Permission.AUDIT_REPORT,
        Permission.AUDIT_TRAIL,
    ],
    RoleTemplate.MANAGER: [
        # User management (limited)
        Permission.USER_READ,
        Permission.USER_UPDATE,
        Permission.USER_LIST,
        Permission.USER_ACTIVATE,
        Permission.USER_DEACTIVATE,
        Permission.USER_LOCK,
        Permission.USER_UNLOCK,
        
        # Role management (limited)
        Permission.ROLE_READ,
        Permission.ROLE_LIST,
        Permission.ROLE_ASSIGN,
        Permission.ROLE_REVOKE,
        
        # Business operations
        Permission.PROPERTY_CREATE,
        Permission.PROPERTY_READ,
        Permission.PROPERTY_UPDATE,
        Permission.PROPERTY_LIST,
        Permission.INVENTORY_CREATE,
        Permission.INVENTORY_READ,
        Permission.INVENTORY_UPDATE,
        Permission.INVENTORY_LIST,
        Permission.INVENTORY_ADJUST,
        Permission.INVENTORY_TRANSFER,
        Permission.SALE_CREATE,
        Permission.SALE_READ,
        Permission.SALE_UPDATE,
        Permission.SALE_LIST,
        Permission.SALE_APPROVE,
        Permission.PURCHASE_CREATE,
        Permission.PURCHASE_READ,
        Permission.PURCHASE_UPDATE,
        Permission.PURCHASE_LIST,
        Permission.PURCHASE_APPROVE,
        
        # Financial (limited)
        Permission.FINANCIAL_VIEW,
        Permission.FINANCIAL_CREATE,
        Permission.FINANCIAL_UPDATE,
        Permission.FINANCIAL_APPROVE,
        Permission.FINANCIAL_REPORT,
        
        # Reporting
        Permission.REPORT_VIEW,
        Permission.REPORT_CREATE,
        Permission.REPORT_EDIT,
        Permission.REPORT_EXPORT,
        Permission.REPORT_DASHBOARD,
        
        # Maintenance
        Permission.MAINTENANCE_CREATE,
        Permission.MAINTENANCE_READ,
        Permission.MAINTENANCE_UPDATE,
        Permission.MAINTENANCE_LIST,
        Permission.MAINTENANCE_SCHEDULE,
        Permission.MAINTENANCE_APPROVE,
        
        # Customer support
        Permission.SUPPORT_VIEW,
        Permission.SUPPORT_CREATE,
        Permission.SUPPORT_UPDATE,
        Permission.SUPPORT_ASSIGN,
        Permission.SUPPORT_ESCALATE,
        Permission.SUPPORT_CLOSE,
        
        # Analytics
        Permission.ANALYTICS_VIEW,
        Permission.ANALYTICS_CREATE,
        Permission.ANALYTICS_UPDATE,
        Permission.ANALYTICS_EXPORT,
        Permission.ANALYTICS_DASHBOARD,
    ],
    RoleTemplate.STAFF: [
        # User profile
        Permission.USER_VIEW_PROFILE,
        Permission.USER_EDIT_PROFILE,
        Permission.USER_CHANGE_PASSWORD,
        
        # Business operations (limited)
        Permission.PROPERTY_READ,
        Permission.PROPERTY_LIST,
        Permission.PROPERTY_SEARCH,
        Permission.INVENTORY_READ,
        Permission.INVENTORY_LIST,
        Permission.INVENTORY_COUNT,
        Permission.SALE_CREATE,
        Permission.SALE_READ,
        Permission.SALE_UPDATE,
        Permission.SALE_LIST,
        Permission.PURCHASE_CREATE,
        Permission.PURCHASE_READ,
        Permission.PURCHASE_UPDATE,
        Permission.PURCHASE_LIST,
        Permission.PURCHASE_RECEIVE,
        
        # Basic reporting
        Permission.REPORT_VIEW,
        Permission.REPORT_EXPORT,
        Permission.REPORT_DASHBOARD,
        
        # Maintenance
        Permission.MAINTENANCE_READ,
        Permission.MAINTENANCE_UPDATE,
        Permission.MAINTENANCE_LIST,
        Permission.MAINTENANCE_COMPLETE,
        
        # Customer support
        Permission.SUPPORT_VIEW,
        Permission.SUPPORT_CREATE,
        Permission.SUPPORT_UPDATE,
        
        # Basic analytics
        Permission.ANALYTICS_VIEW,
        Permission.ANALYTICS_DASHBOARD,
    ],
    RoleTemplate.CUSTOMER: [
        # User profile
        Permission.USER_VIEW_PROFILE,
        Permission.USER_EDIT_PROFILE,
        Permission.USER_CHANGE_PASSWORD,
        
        # Limited property access
        Permission.PROPERTY_READ,
        Permission.PROPERTY_SEARCH,
        
        # Customer support
        Permission.SUPPORT_VIEW,
        Permission.SUPPORT_CREATE,
        Permission.SUPPORT_UPDATE,
        
        # Basic reporting
        Permission.REPORT_VIEW,
        Permission.REPORT_DASHBOARD,
    ],
    RoleTemplate.AUDITOR: [
        # Read-only access to most resources
        Permission.USER_READ,
        Permission.USER_LIST,
        Permission.ROLE_READ,
        Permission.ROLE_LIST,
        Permission.PERMISSION_READ,
        Permission.PERMISSION_LIST,
        Permission.PROPERTY_READ,
        Permission.PROPERTY_LIST,
        Permission.INVENTORY_READ,
        Permission.INVENTORY_LIST,
        Permission.INVENTORY_REPORT,
        Permission.SALE_READ,
        Permission.SALE_LIST,
        Permission.SALE_REPORT,
        Permission.PURCHASE_READ,
        Permission.PURCHASE_LIST,
        Permission.PURCHASE_REPORT,
        Permission.FINANCIAL_VIEW,
        Permission.FINANCIAL_REPORT,
        Permission.FINANCIAL_AUDIT,
        
        # Full audit access
        Permission.AUDIT_VIEW,
        Permission.AUDIT_CREATE,
        Permission.AUDIT_UPDATE,
        Permission.AUDIT_DELETE,
        Permission.AUDIT_EXPORT,
        Permission.AUDIT_REPORT,
        Permission.AUDIT_TRAIL,
        
        # Reporting
        Permission.REPORT_VIEW,
        Permission.REPORT_CREATE,
        Permission.REPORT_EDIT,
        Permission.REPORT_EXPORT,
        Permission.REPORT_DASHBOARD,
        
        # Analytics
        Permission.ANALYTICS_VIEW,
        Permission.ANALYTICS_CREATE,
        Permission.ANALYTICS_EXPORT,
        Permission.ANALYTICS_DASHBOARD,
    ],
    RoleTemplate.ACCOUNTANT: [
        # User profile
        Permission.USER_VIEW_PROFILE,
        Permission.USER_EDIT_PROFILE,
        Permission.USER_CHANGE_PASSWORD,
        
        # Limited business operations
        Permission.PROPERTY_READ,
        Permission.PROPERTY_LIST,
        Permission.INVENTORY_READ,
        Permission.INVENTORY_LIST,
        Permission.INVENTORY_VALUATION,
        Permission.SALE_READ,
        Permission.SALE_LIST,
        Permission.SALE_REPORT,
        Permission.PURCHASE_READ,
        Permission.PURCHASE_LIST,
        Permission.PURCHASE_REPORT,
        
        # Full financial access
        Permission.FINANCIAL_VIEW,
        Permission.FINANCIAL_CREATE,
        Permission.FINANCIAL_UPDATE,
        Permission.FINANCIAL_DELETE,
        Permission.FINANCIAL_APPROVE,
        Permission.FINANCIAL_RECONCILE,
        Permission.FINANCIAL_REPORT,
        Permission.FINANCIAL_BUDGET,
        Permission.FINANCIAL_FORECAST,
        Permission.FINANCIAL_AUDIT,
        
        # Reporting
        Permission.REPORT_VIEW,
        Permission.REPORT_CREATE,
        Permission.REPORT_EDIT,
        Permission.REPORT_EXPORT,
        Permission.REPORT_DASHBOARD,
        
        # Analytics
        Permission.ANALYTICS_VIEW,
        Permission.ANALYTICS_CREATE,
        Permission.ANALYTICS_EXPORT,
        Permission.ANALYTICS_DASHBOARD,
    ],
}


# User type hierarchy management rules
USER_TYPE_HIERARCHY = {
    UserType.SUPERADMIN: [UserType.ADMIN, UserType.USER, UserType.CUSTOMER],
    UserType.ADMIN: [UserType.USER, UserType.CUSTOMER],
    UserType.USER: [UserType.CUSTOMER],
    UserType.CUSTOMER: [],
}


def get_permission_risk_level(permission: str) -> PermissionRiskLevel:
    """Get the risk level for a permission."""
    return PERMISSION_RISK_LEVELS.get(permission, PermissionRiskLevel.LOW)


def get_permission_dependencies(permission: str) -> Set[str]:
    """Get the dependencies for a permission."""
    return PERMISSION_DEPENDENCIES.get(permission, set())


def get_role_template_permissions(template: RoleTemplate) -> List[str]:
    """Get the default permissions for a role template."""
    return ROLE_TEMPLATES.get(template, [])


def can_user_type_manage(manager_type: UserType, target_type: UserType) -> bool:
    """Check if a user type can manage another user type."""
    if manager_type == UserType.SUPERADMIN:
        return True
    return target_type in USER_TYPE_HIERARCHY.get(manager_type, [])


def get_permissions_by_category(category: PermissionCategory) -> List[str]:
    """Get all permissions for a specific category."""
    return PERMISSION_CATEGORIES.get(category, [])


def get_all_permissions() -> List[str]:
    """Get all available permissions."""
    return [perm for category_perms in PERMISSION_CATEGORIES.values() for perm in category_perms]


def validate_permission_dependencies(permissions: List[str]) -> List[str]:
    """Validate that all permission dependencies are satisfied."""
    missing_deps = []
    permission_set = set(permissions)
    
    for permission in permissions:
        deps = get_permission_dependencies(permission)
        missing = deps - permission_set
        if missing:
            missing_deps.extend(missing)
    
    return list(set(missing_deps))