"""Audit service for RBAC changes."""

from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.audit_log import RBACauditLog
from src.infrastructure.models.auth_models import RBACauditLogModel


class AuditService:
    """Service for logging RBAC audit events."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def log_user_created(
        self,
        actor_id: UUID,
        user_id: UUID,
        user_name: str,
        user_email: str,
        user_type: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        reason: Optional[str] = None
    ) -> RBACauditLog:
        """Log user creation."""
        changes = {
            'email': {'new': user_email, 'old': None},
            'name': {'new': user_name, 'old': None},
            'user_type': {'new': user_type, 'old': None},
        }
        
        return await self._create_audit_log(
            actor_id=actor_id,
            action="CREATE",
            entity_type="USER",
            entity_id=user_id,
            entity_name=user_name,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
            reason=reason
        )
    
    async def log_user_updated(
        self,
        actor_id: UUID,
        user_id: UUID,
        user_name: str,
        old_values: Dict[str, Any],
        new_values: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        reason: Optional[str] = None
    ) -> RBACauditLog:
        """Log user update."""
        changes = {}
        for field, new_value in new_values.items():
            old_value = old_values.get(field)
            if old_value != new_value:
                changes[field] = {'old': old_value, 'new': new_value}
        
        return await self._create_audit_log(
            actor_id=actor_id,
            action="UPDATE",
            entity_type="USER",
            entity_id=user_id,
            entity_name=user_name,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
            reason=reason
        )
    
    async def log_user_deleted(
        self,
        actor_id: UUID,
        user_id: UUID,
        user_name: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        reason: Optional[str] = None
    ) -> RBACauditLog:
        """Log user deletion."""
        return await self._create_audit_log(
            actor_id=actor_id,
            action="DELETE",
            entity_type="USER",
            entity_id=user_id,
            entity_name=user_name,
            ip_address=ip_address,
            user_agent=user_agent,
            reason=reason
        )
    
    async def log_role_assigned(
        self,
        actor_id: UUID,
        user_id: UUID,
        user_name: str,
        role_name: str,
        old_role_name: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        reason: Optional[str] = None
    ) -> RBACauditLog:
        """Log role assignment."""
        changes = {
            'role': {'old': old_role_name, 'new': role_name}
        }
        
        return await self._create_audit_log(
            actor_id=actor_id,
            action="ROLE_ASSIGN",
            entity_type="USER",
            entity_id=user_id,
            entity_name=user_name,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
            reason=reason
        )
    
    async def log_permission_granted(
        self,
        actor_id: UUID,
        user_id: UUID,
        user_name: str,
        permission_code: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        reason: Optional[str] = None
    ) -> RBACauditLog:
        """Log direct permission grant."""
        changes = {
            'permission': {'old': None, 'new': permission_code}
        }
        
        return await self._create_audit_log(
            actor_id=actor_id,
            action="PERMISSION_GRANT",
            entity_type="USER",
            entity_id=user_id,
            entity_name=user_name,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
            reason=reason
        )
    
    async def log_permission_revoked(
        self,
        actor_id: UUID,
        user_id: UUID,
        user_name: str,
        permission_code: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        reason: Optional[str] = None
    ) -> RBACauditLog:
        """Log direct permission revocation."""
        changes = {
            'permission': {'old': permission_code, 'new': None}
        }
        
        return await self._create_audit_log(
            actor_id=actor_id,
            action="PERMISSION_REVOKE",
            entity_type="USER",
            entity_id=user_id,
            entity_name=user_name,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
            reason=reason
        )
    
    async def log_login(
        self,
        user_id: UUID,
        user_name: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> RBACauditLog:
        """Log successful login."""
        return await self._create_audit_log(
            actor_id=user_id,
            action="LOGIN",
            entity_type="USER",
            entity_id=user_id,
            entity_name=user_name,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    async def log_login_failed(
        self,
        email: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        reason: Optional[str] = None
    ) -> RBACauditLog:
        """Log failed login attempt."""
        return await self._create_audit_log(
            actor_id=None,  # No valid user for failed login
            action="LOGIN_FAILED",
            entity_type="USER",
            entity_name=email,
            ip_address=ip_address,
            user_agent=user_agent,
            reason=reason
        )
    
    async def log_logout(
        self,
        user_id: UUID,
        user_name: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> RBACauditLog:
        """Log logout."""
        return await self._create_audit_log(
            actor_id=user_id,
            action="LOGOUT",
            entity_type="USER",
            entity_id=user_id,
            entity_name=user_name,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    async def log_impersonation(
        self,
        actor_id: UUID,
        actor_name: str,
        target_user_id: UUID,
        target_user_name: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        reason: Optional[str] = None
    ) -> RBACauditLog:
        """Log user impersonation."""
        changes = {
            'target_user': {'old': None, 'new': target_user_name}
        }
        
        return await self._create_audit_log(
            actor_id=actor_id,
            action="IMPERSONATE",
            entity_type="USER",
            entity_id=actor_id,
            entity_name=actor_name,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
            reason=reason
        )
    
    async def _create_audit_log(
        self,
        action: str,
        entity_type: str,
        actor_id: Optional[UUID] = None,
        entity_id: Optional[UUID] = None,
        entity_name: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        reason: Optional[str] = None
    ) -> RBACauditLog:
        """Create and persist an audit log entry."""
        
        # Create the audit log model
        audit_model = RBACauditLogModel(
            user_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
            reason=reason,
            created_at=datetime.utcnow()
        )
        
        self.session.add(audit_model)
        await self.session.commit()
        
        # Return the domain entity
        return RBACauditLog(
            user_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
            reason=reason,
            id=audit_model.id,
            created_at=audit_model.created_at
        )
    
    async def get_audit_logs(
        self,
        user_id: Optional[UUID] = None,
        entity_type: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[RBACauditLog]:
        """Get audit logs with filtering."""
        from sqlalchemy import select, and_
        
        conditions = []
        
        if user_id:
            conditions.append(RBACauditLogModel.user_id == user_id)
        if entity_type:
            conditions.append(RBACauditLogModel.entity_type == entity_type)
        if action:
            conditions.append(RBACauditLogModel.action == action)
        if start_date:
            conditions.append(RBACauditLogModel.created_at >= start_date)
        if end_date:
            conditions.append(RBACauditLogModel.created_at <= end_date)
        
        query = select(RBACauditLogModel)
        
        if conditions:
            query = query.filter(and_(*conditions))
        
        query = query.order_by(RBACauditLogModel.created_at.desc()).limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    def _model_to_entity(self, model: RBACauditLogModel) -> RBACauditLog:
        """Convert audit log model to entity."""
        return RBACauditLog(
            user_id=model.user_id,
            action=model.action,
            entity_type=model.entity_type,
            entity_id=model.entity_id,
            entity_name=model.entity_name,
            changes=model.changes,
            ip_address=model.ip_address,
            user_agent=model.user_agent,
            reason=model.reason,
            id=model.id,
            created_at=model.created_at
        )