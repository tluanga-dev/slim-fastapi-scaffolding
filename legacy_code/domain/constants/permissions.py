"""
Permission constants for the RBAC system.

This module defines all permissions used throughout the system, organized by category.
Each permission follows the pattern: <MODULE>_<ACTION>
"""

from enum import Enum
from typing import Dict, List, Set


class PermissionCategory(str, Enum):
    """Categories for grouping related permissions."""
    
    SYSTEM = "SYSTEM"
    USER_MANAGEMENT = "USER_MANAGEMENT"
    ROLE_MANAGEMENT = "ROLE_MANAGEMENT"
    CUSTOMER = "CUSTOMER"
    INVENTORY = "INVENTORY"
    PRODUCT = "PRODUCT"
    SALES = "SALES"
    RENTAL = "RENTAL"
    PURCHASE = "PURCHASE"
    RETURNS = "RETURNS"
    INSPECTION = "INSPECTION"
    FINANCE = "FINANCE"
    REPORTS = "REPORTS"
    SETTINGS = "SETTINGS"
    AUDIT = "AUDIT"


class Permission(str, Enum):
    """All system permissions."""
    
    # System Administration
    SYSTEM_FULL_ACCESS = "SYSTEM_FULL_ACCESS"
    SYSTEM_CONFIG_VIEW = "SYSTEM_CONFIG_VIEW"
    SYSTEM_CONFIG_UPDATE = "SYSTEM_CONFIG_UPDATE"
    SYSTEM_MAINTENANCE = "SYSTEM_MAINTENANCE"
    
    # User Management
    USER_VIEW = "USER_VIEW"
    USER_CREATE = "USER_CREATE"
    USER_UPDATE = "USER_UPDATE"
    USER_DELETE = "USER_DELETE"
    USER_ACTIVATE = "USER_ACTIVATE"
    USER_DEACTIVATE = "USER_DEACTIVATE"
    USER_RESET_PASSWORD = "USER_RESET_PASSWORD"
    USER_IMPERSONATE = "USER_IMPERSONATE"
    USER_VIEW_SESSIONS = "USER_VIEW_SESSIONS"
    USER_TERMINATE_SESSIONS = "USER_TERMINATE_SESSIONS"
    
    # Role & Permission Management
    ROLE_VIEW = "ROLE_VIEW"
    ROLE_CREATE = "ROLE_CREATE"
    ROLE_UPDATE = "ROLE_UPDATE"
    ROLE_DELETE = "ROLE_DELETE"
    ROLE_ASSIGN = "ROLE_ASSIGN"
    PERMISSION_VIEW = "PERMISSION_VIEW"
    PERMISSION_ASSIGN = "PERMISSION_ASSIGN"
    PERMISSION_REVOKE = "PERMISSION_REVOKE"
    
    # Customer Management
    CUSTOMER_VIEW = "CUSTOMER_VIEW"
    CUSTOMER_CREATE = "CUSTOMER_CREATE"
    CUSTOMER_UPDATE = "CUSTOMER_UPDATE"
    CUSTOMER_DELETE = "CUSTOMER_DELETE"
    CUSTOMER_VIEW_SENSITIVE = "CUSTOMER_VIEW_SENSITIVE"
    CUSTOMER_BLACKLIST = "CUSTOMER_BLACKLIST"
    CUSTOMER_SET_CREDIT_LIMIT = "CUSTOMER_SET_CREDIT_LIMIT"
    CUSTOMER_VIEW_HISTORY = "CUSTOMER_VIEW_HISTORY"
    
    # Inventory Management
    INVENTORY_VIEW = "INVENTORY_VIEW"
    INVENTORY_CREATE = "INVENTORY_CREATE"
    INVENTORY_UPDATE = "INVENTORY_UPDATE"
    INVENTORY_DELETE = "INVENTORY_DELETE"
    INVENTORY_ADJUST = "INVENTORY_ADJUST"
    INVENTORY_TRANSFER = "INVENTORY_TRANSFER"
    INVENTORY_COUNT = "INVENTORY_COUNT"
    INVENTORY_VIEW_COST = "INVENTORY_VIEW_COST"
    INVENTORY_SET_LOCATION = "INVENTORY_SET_LOCATION"
    INVENTORY_VIEW_SERIAL = "INVENTORY_VIEW_SERIAL"
    
    # Product/SKU Management
    PRODUCT_VIEW = "PRODUCT_VIEW"
    PRODUCT_CREATE = "PRODUCT_CREATE"
    PRODUCT_UPDATE = "PRODUCT_UPDATE"
    PRODUCT_DELETE = "PRODUCT_DELETE"
    SKU_VIEW = "SKU_VIEW"
    SKU_CREATE = "SKU_CREATE"
    SKU_UPDATE = "SKU_UPDATE"
    SKU_DELETE = "SKU_DELETE"
    SKU_SET_PRICING = "SKU_SET_PRICING"
    CATEGORY_VIEW = "CATEGORY_VIEW"
    CATEGORY_CREATE = "CATEGORY_CREATE"
    CATEGORY_UPDATE = "CATEGORY_UPDATE"
    CATEGORY_DELETE = "CATEGORY_DELETE"
    
    # Sales Management
    SALE_VIEW = "SALE_VIEW"
    SALE_CREATE = "SALE_CREATE"
    SALE_UPDATE = "SALE_UPDATE"
    SALE_DELETE = "SALE_DELETE"
    SALE_CANCEL = "SALE_CANCEL"
    SALE_APPLY_DISCOUNT = "SALE_APPLY_DISCOUNT"
    SALE_OVERRIDE_PRICE = "SALE_OVERRIDE_PRICE"
    SALE_VIEW_PROFIT = "SALE_VIEW_PROFIT"
    SALE_PROCESS_PAYMENT = "SALE_PROCESS_PAYMENT"
    SALE_REFUND = "SALE_REFUND"
    
    # Rental Management
    RENTAL_VIEW = "RENTAL_VIEW"
    RENTAL_CREATE = "RENTAL_CREATE"
    RENTAL_UPDATE = "RENTAL_UPDATE"
    RENTAL_DELETE = "RENTAL_DELETE"
    RENTAL_CANCEL = "RENTAL_CANCEL"
    RENTAL_EXTEND = "RENTAL_EXTEND"
    RENTAL_OVERRIDE_RATE = "RENTAL_OVERRIDE_RATE"
    RENTAL_WAIVE_FEES = "RENTAL_WAIVE_FEES"
    RENTAL_PROCESS_DEPOSIT = "RENTAL_PROCESS_DEPOSIT"
    RENTAL_RELEASE_DEPOSIT = "RENTAL_RELEASE_DEPOSIT"
    RENTAL_APPROVE_DAMAGE = "RENTAL_APPROVE_DAMAGE"
    
    # Purchase Management
    PURCHASE_VIEW = "PURCHASE_VIEW"
    PURCHASE_CREATE = "PURCHASE_CREATE"
    PURCHASE_UPDATE = "PURCHASE_UPDATE"
    PURCHASE_DELETE = "PURCHASE_DELETE"
    PURCHASE_CANCEL = "PURCHASE_CANCEL"
    PURCHASE_APPROVE = "PURCHASE_APPROVE"
    PURCHASE_RECEIVE = "PURCHASE_RECEIVE"
    PURCHASE_VIEW_COST = "PURCHASE_VIEW_COST"
    SUPPLIER_VIEW = "SUPPLIER_VIEW"
    SUPPLIER_CREATE = "SUPPLIER_CREATE"
    SUPPLIER_UPDATE = "SUPPLIER_UPDATE"
    SUPPLIER_DELETE = "SUPPLIER_DELETE"
    
    # Returns Management
    RETURN_VIEW = "RETURN_VIEW"
    RETURN_CREATE = "RETURN_CREATE"
    RETURN_UPDATE = "RETURN_UPDATE"
    RETURN_DELETE = "RETURN_DELETE"
    RETURN_PROCESS = "RETURN_PROCESS"
    RETURN_APPROVE = "RETURN_APPROVE"
    RETURN_REJECT = "RETURN_REJECT"
    
    # Inspection Management
    INSPECTION_VIEW = "INSPECTION_VIEW"
    INSPECTION_CREATE = "INSPECTION_CREATE"
    INSPECTION_UPDATE = "INSPECTION_UPDATE"
    INSPECTION_DELETE = "INSPECTION_DELETE"
    INSPECTION_APPROVE = "INSPECTION_APPROVE"
    INSPECTION_UPLOAD_PHOTOS = "INSPECTION_UPLOAD_PHOTOS"
    
    # Financial Management
    FINANCE_VIEW_TRANSACTIONS = "FINANCE_VIEW_TRANSACTIONS"
    FINANCE_VIEW_REPORTS = "FINANCE_VIEW_REPORTS"
    FINANCE_EXPORT_DATA = "FINANCE_EXPORT_DATA"
    FINANCE_VIEW_PROFIT_LOSS = "FINANCE_VIEW_PROFIT_LOSS"
    FINANCE_VIEW_CASH_FLOW = "FINANCE_VIEW_CASH_FLOW"
    FINANCE_MANAGE_TAXES = "FINANCE_MANAGE_TAXES"
    FINANCE_PROCESS_REFUNDS = "FINANCE_PROCESS_REFUNDS"
    
    # Reports
    REPORT_VIEW_BASIC = "REPORT_VIEW_BASIC"
    REPORT_VIEW_ADVANCED = "REPORT_VIEW_ADVANCED"
    REPORT_CREATE = "REPORT_CREATE"
    REPORT_EXPORT = "REPORT_EXPORT"
    REPORT_SCHEDULE = "REPORT_SCHEDULE"
    REPORT_VIEW_ANALYTICS = "REPORT_VIEW_ANALYTICS"
    
    # Settings
    SETTINGS_VIEW = "SETTINGS_VIEW"
    SETTINGS_UPDATE = "SETTINGS_UPDATE"
    SETTINGS_VIEW_SECURITY = "SETTINGS_VIEW_SECURITY"
    SETTINGS_UPDATE_SECURITY = "SETTINGS_UPDATE_SECURITY"
    SETTINGS_VIEW_INTEGRATIONS = "SETTINGS_VIEW_INTEGRATIONS"
    SETTINGS_MANAGE_INTEGRATIONS = "SETTINGS_MANAGE_INTEGRATIONS"
    
    # Audit
    AUDIT_VIEW_LOGS = "AUDIT_VIEW_LOGS"
    AUDIT_EXPORT_LOGS = "AUDIT_EXPORT_LOGS"
    AUDIT_VIEW_SECURITY_EVENTS = "AUDIT_VIEW_SECURITY_EVENTS"
    AUDIT_VIEW_ACCESS_LOGS = "AUDIT_VIEW_ACCESS_LOGS"


# Permission metadata
PERMISSION_METADATA: Dict[Permission, Dict[str, any]] = {
    # System permissions
    Permission.SYSTEM_FULL_ACCESS: {
        "category": PermissionCategory.SYSTEM,
        "description": "Full system access - superadmin only",
        "risk_level": "CRITICAL",
        "requires_approval": True,
    },
    Permission.SYSTEM_CONFIG_VIEW: {
        "category": PermissionCategory.SYSTEM,
        "description": "View system configuration",
        "risk_level": "MEDIUM",
    },
    Permission.SYSTEM_CONFIG_UPDATE: {
        "category": PermissionCategory.SYSTEM,
        "description": "Update system configuration",
        "risk_level": "HIGH",
        "requires_approval": True,
    },
    
    # User management permissions
    Permission.USER_VIEW: {
        "category": PermissionCategory.USER_MANAGEMENT,
        "description": "View user information",
        "risk_level": "LOW",
    },
    Permission.USER_CREATE: {
        "category": PermissionCategory.USER_MANAGEMENT,
        "description": "Create new users",
        "risk_level": "MEDIUM",
    },
    Permission.USER_UPDATE: {
        "category": PermissionCategory.USER_MANAGEMENT,
        "description": "Update user information",
        "risk_level": "MEDIUM",
    },
    Permission.USER_DELETE: {
        "category": PermissionCategory.USER_MANAGEMENT,
        "description": "Delete users",
        "risk_level": "HIGH",
    },
    Permission.USER_IMPERSONATE: {
        "category": PermissionCategory.USER_MANAGEMENT,
        "description": "Impersonate another user",
        "risk_level": "CRITICAL",
        "requires_approval": True,
        "audit_required": True,
    },
    
    # Add metadata for other permissions as needed...
}


# Permission dependencies (some permissions require others)
PERMISSION_DEPENDENCIES: Dict[Permission, Set[Permission]] = {
    Permission.USER_DELETE: {Permission.USER_VIEW, Permission.USER_UPDATE},
    Permission.USER_UPDATE: {Permission.USER_VIEW},
    Permission.ROLE_DELETE: {Permission.ROLE_VIEW, Permission.ROLE_UPDATE},
    Permission.ROLE_UPDATE: {Permission.ROLE_VIEW},
    Permission.SALE_CREATE: {Permission.SALE_VIEW, Permission.INVENTORY_VIEW, Permission.CUSTOMER_VIEW},
    Permission.SALE_UPDATE: {Permission.SALE_VIEW},
    Permission.SALE_DELETE: {Permission.SALE_VIEW, Permission.SALE_UPDATE},
    Permission.RENTAL_CREATE: {Permission.RENTAL_VIEW, Permission.INVENTORY_VIEW, Permission.CUSTOMER_VIEW},
    Permission.RENTAL_UPDATE: {Permission.RENTAL_VIEW},
    Permission.RENTAL_DELETE: {Permission.RENTAL_VIEW, Permission.RENTAL_UPDATE},
    Permission.PURCHASE_CREATE: {Permission.PURCHASE_VIEW, Permission.SUPPLIER_VIEW},
    Permission.PURCHASE_UPDATE: {Permission.PURCHASE_VIEW},
    Permission.PURCHASE_DELETE: {Permission.PURCHASE_VIEW, Permission.PURCHASE_UPDATE},
    Permission.RETURN_PROCESS: {Permission.RETURN_VIEW, Permission.RETURN_UPDATE},
    Permission.INSPECTION_APPROVE: {Permission.INSPECTION_VIEW, Permission.INSPECTION_UPDATE},
    Permission.FINANCE_PROCESS_REFUNDS: {Permission.FINANCE_VIEW_TRANSACTIONS, Permission.SALE_VIEW},
}


# Role templates with predefined permissions
class RoleTemplate(str, Enum):
    """Predefined role templates."""
    
    SUPERADMIN = "SUPERADMIN"
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    STAFF = "STAFF"
    CUSTOMER = "CUSTOMER"
    AUDITOR = "AUDITOR"
    ACCOUNTANT = "ACCOUNTANT"


# Default permissions for role templates
ROLE_TEMPLATE_PERMISSIONS: Dict[RoleTemplate, Set[Permission]] = {
    RoleTemplate.SUPERADMIN: {
        Permission.SYSTEM_FULL_ACCESS,
        # Superadmin has all permissions
    },
    
    RoleTemplate.ADMIN: {
        # User management
        Permission.USER_VIEW,
        Permission.USER_CREATE,
        Permission.USER_UPDATE,
        Permission.USER_DELETE,
        Permission.USER_ACTIVATE,
        Permission.USER_DEACTIVATE,
        Permission.USER_RESET_PASSWORD,
        Permission.USER_VIEW_SESSIONS,
        Permission.USER_TERMINATE_SESSIONS,
        
        # Role management
        Permission.ROLE_VIEW,
        Permission.ROLE_CREATE,
        Permission.ROLE_UPDATE,
        Permission.ROLE_DELETE,
        Permission.ROLE_ASSIGN,
        Permission.PERMISSION_VIEW,
        Permission.PERMISSION_ASSIGN,
        Permission.PERMISSION_REVOKE,
        
        # All other modules with full access
        Permission.CUSTOMER_VIEW,
        Permission.CUSTOMER_CREATE,
        Permission.CUSTOMER_UPDATE,
        Permission.CUSTOMER_DELETE,
        Permission.CUSTOMER_VIEW_SENSITIVE,
        Permission.CUSTOMER_BLACKLIST,
        Permission.CUSTOMER_SET_CREDIT_LIMIT,
        Permission.CUSTOMER_VIEW_HISTORY,
        
        # Continue with other modules...
    },
    
    RoleTemplate.MANAGER: {
        # Limited user management
        Permission.USER_VIEW,
        Permission.USER_UPDATE,
        Permission.USER_ACTIVATE,
        Permission.USER_DEACTIVATE,
        
        # Customer management
        Permission.CUSTOMER_VIEW,
        Permission.CUSTOMER_CREATE,
        Permission.CUSTOMER_UPDATE,
        Permission.CUSTOMER_VIEW_HISTORY,
        
        # Sales management
        Permission.SALE_VIEW,
        Permission.SALE_CREATE,
        Permission.SALE_UPDATE,
        Permission.SALE_CANCEL,
        Permission.SALE_APPLY_DISCOUNT,
        Permission.SALE_PROCESS_PAYMENT,
        
        # Rental management
        Permission.RENTAL_VIEW,
        Permission.RENTAL_CREATE,
        Permission.RENTAL_UPDATE,
        Permission.RENTAL_EXTEND,
        Permission.RENTAL_PROCESS_DEPOSIT,
        
        # Inventory
        Permission.INVENTORY_VIEW,
        Permission.INVENTORY_UPDATE,
        Permission.INVENTORY_ADJUST,
        Permission.INVENTORY_TRANSFER,
        
        # Reports
        Permission.REPORT_VIEW_BASIC,
        Permission.REPORT_VIEW_ADVANCED,
        Permission.REPORT_EXPORT,
    },
    
    RoleTemplate.STAFF: {
        # Basic permissions
        Permission.CUSTOMER_VIEW,
        Permission.CUSTOMER_CREATE,
        Permission.CUSTOMER_UPDATE,
        
        Permission.SALE_VIEW,
        Permission.SALE_CREATE,
        Permission.SALE_PROCESS_PAYMENT,
        
        Permission.RENTAL_VIEW,
        Permission.RENTAL_CREATE,
        Permission.RENTAL_PROCESS_DEPOSIT,
        
        Permission.INVENTORY_VIEW,
        Permission.PRODUCT_VIEW,
        Permission.SKU_VIEW,
        
        Permission.REPORT_VIEW_BASIC,
    },
    
    RoleTemplate.CUSTOMER: {
        # Very limited permissions - customer portal access
        Permission.CUSTOMER_VIEW,  # View own profile
        Permission.RENTAL_VIEW,    # View own rentals
        Permission.SALE_VIEW,      # View own purchases
    },
    
    RoleTemplate.AUDITOR: {
        # Read-only access to audit and financial data
        Permission.AUDIT_VIEW_LOGS,
        Permission.AUDIT_EXPORT_LOGS,
        Permission.AUDIT_VIEW_SECURITY_EVENTS,
        Permission.AUDIT_VIEW_ACCESS_LOGS,
        Permission.FINANCE_VIEW_TRANSACTIONS,
        Permission.FINANCE_VIEW_REPORTS,
        Permission.FINANCE_EXPORT_DATA,
        Permission.REPORT_VIEW_ADVANCED,
        Permission.USER_VIEW,
        Permission.ROLE_VIEW,
        Permission.PERMISSION_VIEW,
    },
    
    RoleTemplate.ACCOUNTANT: {
        # Financial management permissions
        Permission.FINANCE_VIEW_TRANSACTIONS,
        Permission.FINANCE_VIEW_REPORTS,
        Permission.FINANCE_EXPORT_DATA,
        Permission.FINANCE_VIEW_PROFIT_LOSS,
        Permission.FINANCE_VIEW_CASH_FLOW,
        Permission.FINANCE_MANAGE_TAXES,
        Permission.FINANCE_PROCESS_REFUNDS,
        Permission.PURCHASE_VIEW,
        Permission.PURCHASE_VIEW_COST,
        Permission.SALE_VIEW,
        Permission.SALE_VIEW_PROFIT,
        Permission.INVENTORY_VIEW_COST,
        Permission.REPORT_VIEW_ADVANCED,
        Permission.REPORT_CREATE,
        Permission.REPORT_EXPORT,
    },
}


def get_permission_category(permission: Permission) -> PermissionCategory:
    """Get the category for a permission."""
    metadata = PERMISSION_METADATA.get(permission, {})
    return metadata.get("category", PermissionCategory.SYSTEM)


def get_permission_dependencies(permission: Permission) -> Set[Permission]:
    """Get all permissions required for a given permission."""
    return PERMISSION_DEPENDENCIES.get(permission, set())


def get_all_permission_dependencies(permissions: Set[Permission]) -> Set[Permission]:
    """Get all permissions including their dependencies."""
    all_permissions = set(permissions)
    for perm in permissions:
        all_permissions.update(get_permission_dependencies(perm))
    return all_permissions


def get_role_template_permissions(template: RoleTemplate) -> Set[Permission]:
    """Get permissions for a role template."""
    if template == RoleTemplate.SUPERADMIN:
        # Superadmin gets all permissions
        return set(Permission)
    return ROLE_TEMPLATE_PERMISSIONS.get(template, set())


def get_permissions_by_category(category: PermissionCategory) -> List[Permission]:
    """Get all permissions in a category."""
    permissions = []
    for perm in Permission:
        if get_permission_category(perm) == category:
            permissions.append(perm)
    return permissions