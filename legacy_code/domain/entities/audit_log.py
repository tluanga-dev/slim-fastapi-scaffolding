"""Audit log entity for RBAC changes."""

from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from src.domain.entities.base import BaseEntity


class RBACauditLog(BaseEntity):
    """Audit log for RBAC-related changes."""
    
    def __init__(
        self,
        user_id: UUID,
        action: str,
        entity_type: str,
        entity_id: Optional[UUID] = None,
        entity_name: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        reason: Optional[str] = None,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        is_active: bool = True,
        created_by: Optional[str] = None,
        updated_by: Optional[str] = None,
    ):
        super().__init__(id, created_at, updated_at, is_active, created_by, updated_by)
        self.user_id = user_id
        self.action = action
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.entity_name = entity_name
        self.changes = changes or {}
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.reason = reason
    
    def add_change(self, field: str, old_value: Any, new_value: Any):
        """Add a field change to the audit log."""
        self.changes[field] = {
            'old': old_value,
            'new': new_value
        }
    
    def get_summary(self) -> str:
        """Get a human-readable summary of the audit log."""
        if self.action == "CREATE":
            return f"Created {self.entity_type.lower()} '{self.entity_name}'"
        elif self.action == "UPDATE":
            changed_fields = list(self.changes.keys())
            if changed_fields:
                return f"Updated {self.entity_type.lower()} '{self.entity_name}' - changed: {', '.join(changed_fields)}"
            return f"Updated {self.entity_type.lower()} '{self.entity_name}'"
        elif self.action == "DELETE":
            return f"Deleted {self.entity_type.lower()} '{self.entity_name}'"
        elif self.action == "PERMISSION_GRANT":
            permission = self.changes.get('permission', {}).get('new')
            return f"Granted permission '{permission}' to {self.entity_type.lower()} '{self.entity_name}'"
        elif self.action == "PERMISSION_REVOKE":
            permission = self.changes.get('permission', {}).get('old')
            return f"Revoked permission '{permission}' from {self.entity_type.lower()} '{self.entity_name}'"
        elif self.action == "ROLE_ASSIGN":
            role = self.changes.get('role', {}).get('new')
            return f"Assigned role '{role}' to user '{self.entity_name}'"
        elif self.action == "ROLE_UNASSIGN":
            role = self.changes.get('role', {}).get('old')
            return f"Removed role '{role}' from user '{self.entity_name}'"
        elif self.action == "LOGIN":
            return f"User '{self.entity_name}' logged in"
        elif self.action == "LOGOUT":
            return f"User '{self.entity_name}' logged out"
        elif self.action == "LOGIN_FAILED":
            return f"Failed login attempt for '{self.entity_name}'"
        elif self.action == "IMPERSONATE":
            target = self.changes.get('target_user', {}).get('new')
            return f"User '{self.entity_name}' impersonated user '{target}'"
        else:
            return f"{self.action} on {self.entity_type.lower()} '{self.entity_name}'"
    
    def is_security_event(self) -> bool:
        """Check if this audit log represents a security-relevant event."""
        security_actions = {
            "LOGIN_FAILED",
            "PERMISSION_GRANT", 
            "PERMISSION_REVOKE",
            "ROLE_ASSIGN",
            "ROLE_UNASSIGN",
            "IMPERSONATE",
            "CREATE",  # Creating users or roles
            "DELETE",  # Deleting users or roles
        }
        return self.action in security_actions
    
    def is_high_risk(self) -> bool:
        """Check if this audit log represents a high-risk action."""
        high_risk_actions = {
            "PERMISSION_GRANT",
            "ROLE_ASSIGN", 
            "IMPERSONATE",
            "DELETE",
        }
        
        # Check for high-risk permission grants
        if self.action == "PERMISSION_GRANT":
            permission = self.changes.get('permission', {}).get('new', '')
            high_risk_permissions = {
                'SYSTEM_FULL_ACCESS',
                'USER_DELETE',
                'USER_IMPERSONATE',
                'ROLE_DELETE',
                'SYSTEM_CONFIG_UPDATE',
            }
            return any(perm in permission for perm in high_risk_permissions)
        
        return self.action in high_risk_actions