"""Domain constants module."""

from .permissions import (
    Permission,
    PermissionCategory,
    RoleTemplate,
    PERMISSION_METADATA,
    PERMISSION_DEPENDENCIES,
    ROLE_TEMPLATE_PERMISSIONS,
    get_permission_category,
    get_permission_dependencies,
    get_all_permission_dependencies,
    get_role_template_permissions,
    get_permissions_by_category,
)

__all__ = [
    "Permission",
    "PermissionCategory",
    "RoleTemplate",
    "PERMISSION_METADATA",
    "PERMISSION_DEPENDENCIES",
    "ROLE_TEMPLATE_PERMISSIONS",
    "get_permission_category",
    "get_permission_dependencies",
    "get_all_permission_dependencies",
    "get_role_template_permissions",
    "get_permissions_by_category",
]