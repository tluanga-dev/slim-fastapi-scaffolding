"""
RBAC Permission Caching System

This module provides high-performance caching for RBAC permissions to reduce database load
and improve response times. It includes cache invalidation strategies and cache warming.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Tuple
from uuid import UUID

from app.core.cache import cache_manager
from app.core.config import settings
from .models import Permission, Role, User
# from .rbac_service import RBACService  # Avoid circular import


class RBACCache:
    """
    High-performance caching system for RBAC permissions.
    
    Features:
    - User permission caching with TTL
    - Role hierarchy caching
    - Permission dependency caching
    - Cache invalidation on permission changes
    - Cache warming for frequently accessed data
    """
    
    def __init__(self):
        self.cache_prefix = "rbac:"
        self.default_ttl = settings.RBAC_CACHE_TTL if hasattr(settings, 'RBAC_CACHE_TTL') else 3600  # 1 hour
        self.hierarchy_ttl = settings.RBAC_HIERARCHY_TTL if hasattr(settings, 'RBAC_HIERARCHY_TTL') else 7200  # 2 hours
        self.dependency_ttl = settings.RBAC_DEPENDENCY_TTL if hasattr(settings, 'RBAC_DEPENDENCY_TTL') else 14400  # 4 hours
    
    # Cache key generators
    def _user_permissions_key(self, user_id: UUID) -> str:
        """Generate cache key for user permissions."""
        return f"{self.cache_prefix}user_permissions:{user_id}"
    
    def _role_permissions_key(self, role_id: UUID) -> str:
        """Generate cache key for role permissions."""
        return f"{self.cache_prefix}role_permissions:{role_id}"
    
    def _role_hierarchy_key(self, role_id: UUID) -> str:
        """Generate cache key for role hierarchy."""
        return f"{self.cache_prefix}role_hierarchy:{role_id}"
    
    def _permission_dependencies_key(self, permission_id: UUID) -> str:
        """Generate cache key for permission dependencies."""
        return f"{self.cache_prefix}permission_deps:{permission_id}"
    
    def _user_roles_key(self, user_id: UUID) -> str:
        """Generate cache key for user roles."""
        return f"{self.cache_prefix}user_roles:{user_id}"
    
    def _permission_by_code_key(self, permission_code: str) -> str:
        """Generate cache key for permission by code."""
        return f"{self.cache_prefix}permission_code:{permission_code}"
    
    def _cache_stats_key(self) -> str:
        """Generate cache key for cache statistics."""
        return f"{self.cache_prefix}stats"
    
    # User permission caching
    async def get_user_permissions(self, user_id: UUID) -> Optional[List[Dict[str, Any]]]:
        """Get cached user permissions."""
        cache_key = self._user_permissions_key(user_id)
        cached_data = await cache_manager.get(cache_key)
        
        if cached_data:
            await self._update_cache_stats('user_permissions', 'hit')
            return json.loads(cached_data)
        
        await self._update_cache_stats('user_permissions', 'miss')
        return None
    
    async def set_user_permissions(self, user_id: UUID, permissions: List[Permission], ttl: Optional[int] = None) -> bool:
        """Cache user permissions."""
        cache_key = self._user_permissions_key(user_id)
        ttl = ttl or self.default_ttl
        
        # Convert permissions to serializable format
        permissions_data = []
        for perm in permissions:
            permissions_data.append({
                'id': str(perm.id),
                'code': perm.code,
                'name': perm.name,
                'description': perm.description,
                'resource': perm.resource,
                'action': perm.action,
                'risk_level': perm.risk_level,
                'requires_approval': perm.requires_approval,
                'cached_at': datetime.utcnow().isoformat()
            })
        
        return await cache_manager.set(cache_key, json.dumps(permissions_data), ttl)
    
    # Role permission caching
    async def get_role_permissions(self, role_id: UUID) -> Optional[List[Dict[str, Any]]]:
        """Get cached role permissions."""
        cache_key = self._role_permissions_key(role_id)
        cached_data = await cache_manager.get(cache_key)
        
        if cached_data:
            await self._update_cache_stats('role_permissions', 'hit')
            return json.loads(cached_data)
        
        await self._update_cache_stats('role_permissions', 'miss')
        return None
    
    async def set_role_permissions(self, role_id: UUID, permissions: List[Permission], ttl: Optional[int] = None) -> bool:
        """Cache role permissions."""
        cache_key = self._role_permissions_key(role_id)
        ttl = ttl or self.default_ttl
        
        permissions_data = []
        for perm in permissions:
            permissions_data.append({
                'id': str(perm.id),
                'code': perm.code,
                'name': perm.name,
                'resource': perm.resource,
                'action': perm.action,
                'risk_level': perm.risk_level,
                'cached_at': datetime.utcnow().isoformat()
            })
        
        return await cache_manager.set(cache_key, json.dumps(permissions_data), ttl)
    
    # Role hierarchy caching
    async def get_role_hierarchy(self, role_id: UUID) -> Optional[Dict[str, Any]]:
        """Get cached role hierarchy."""
        cache_key = self._role_hierarchy_key(role_id)
        cached_data = await cache_manager.get(cache_key)
        
        if cached_data:
            await self._update_cache_stats('role_hierarchy', 'hit')
            return json.loads(cached_data)
        
        await self._update_cache_stats('role_hierarchy', 'miss')
        return None
    
    async def set_role_hierarchy(self, role_id: UUID, hierarchy_data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Cache role hierarchy."""
        cache_key = self._role_hierarchy_key(role_id)
        ttl = ttl or self.hierarchy_ttl
        
        # Serialize hierarchy data
        serializable_data = {
            'role_id': str(role_id),
            'parent_roles': [str(role.id) for role in hierarchy_data.get('parent_roles', [])],
            'child_roles': [str(role.id) for role in hierarchy_data.get('child_roles', [])],
            'cached_at': datetime.utcnow().isoformat()
        }
        
        return await cache_manager.set(cache_key, json.dumps(serializable_data), ttl)
    
    # Permission dependency caching
    async def get_permission_dependencies(self, permission_id: UUID) -> Optional[List[str]]:
        """Get cached permission dependencies."""
        cache_key = self._permission_dependencies_key(permission_id)
        cached_data = await cache_manager.get(cache_key)
        
        if cached_data:
            await self._update_cache_stats('permission_dependencies', 'hit')
            return json.loads(cached_data)
        
        await self._update_cache_stats('permission_dependencies', 'miss')
        return None
    
    async def set_permission_dependencies(self, permission_id: UUID, dependencies: List[str], ttl: Optional[int] = None) -> bool:
        """Cache permission dependencies."""
        cache_key = self._permission_dependencies_key(permission_id)
        ttl = ttl or self.dependency_ttl
        
        return await cache_manager.set(cache_key, json.dumps(dependencies), ttl)
    
    # Permission by code caching
    async def get_permission_by_code(self, permission_code: str) -> Optional[Dict[str, Any]]:
        """Get cached permission by code."""
        cache_key = self._permission_by_code_key(permission_code)
        cached_data = await cache_manager.get(cache_key)
        
        if cached_data:
            await self._update_cache_stats('permission_by_code', 'hit')
            return json.loads(cached_data)
        
        await self._update_cache_stats('permission_by_code', 'miss')
        return None
    
    async def set_permission_by_code(self, permission_code: str, permission: Permission, ttl: Optional[int] = None) -> bool:
        """Cache permission by code."""
        cache_key = self._permission_by_code_key(permission_code)
        ttl = ttl or self.dependency_ttl
        
        permission_data = {
            'id': str(permission.id),
            'code': permission.code,
            'name': permission.name,
            'description': permission.description,
            'resource': permission.resource,
            'action': permission.action,
            'risk_level': permission.risk_level,
            'requires_approval': permission.requires_approval,
            'cached_at': datetime.utcnow().isoformat()
        }
        
        return await cache_manager.set(cache_key, json.dumps(permission_data), ttl)
    
    # Cache invalidation methods
    async def invalidate_user_permissions(self, user_id: UUID) -> bool:
        """Invalidate cached user permissions."""
        cache_key = self._user_permissions_key(user_id)
        return await cache_manager.delete(cache_key)
    
    async def invalidate_role_permissions(self, role_id: UUID) -> bool:
        """Invalidate cached role permissions."""
        cache_key = self._role_permissions_key(role_id)
        return await cache_manager.delete(cache_key)
    
    async def invalidate_role_hierarchy(self, role_id: UUID) -> bool:
        """Invalidate cached role hierarchy."""
        cache_key = self._role_hierarchy_key(role_id)
        return await cache_manager.delete(cache_key)
    
    async def invalidate_permission_dependencies(self, permission_id: UUID) -> bool:
        """Invalidate cached permission dependencies."""
        cache_key = self._permission_dependencies_key(permission_id)
        return await cache_manager.delete(cache_key)
    
    async def invalidate_permission_by_code(self, permission_code: str) -> bool:
        """Invalidate cached permission by code."""
        cache_key = self._permission_by_code_key(permission_code)
        return await cache_manager.delete(cache_key)
    
    # Bulk invalidation methods
    async def invalidate_user_related_cache(self, user_id: UUID) -> Dict[str, bool]:
        """Invalidate all cache entries related to a user."""
        results = {}
        
        # Invalidate user permissions
        results['user_permissions'] = await self.invalidate_user_permissions(user_id)
        
        # Invalidate user roles
        user_roles_key = self._user_roles_key(user_id)
        results['user_roles'] = await cache_manager.delete(user_roles_key)
        
        return results
    
    async def invalidate_role_related_cache(self, role_id: UUID) -> Dict[str, bool]:
        """Invalidate all cache entries related to a role."""
        results = {}
        
        # Invalidate role permissions
        results['role_permissions'] = await self.invalidate_role_permissions(role_id)
        
        # Invalidate role hierarchy
        results['role_hierarchy'] = await self.invalidate_role_hierarchy(role_id)
        
        # TODO: Invalidate all users who have this role
        # This would require tracking user-role relationships
        
        return results
    
    async def invalidate_permission_related_cache(self, permission_id: UUID, permission_code: str) -> Dict[str, bool]:
        """Invalidate all cache entries related to a permission."""
        results = {}
        
        # Invalidate permission dependencies
        results['permission_dependencies'] = await self.invalidate_permission_dependencies(permission_id)
        
        # Invalidate permission by code
        results['permission_by_code'] = await self.invalidate_permission_by_code(permission_code)
        
        return results
    
    # Cache warming methods
    async def warm_user_permissions_cache(self, user_id: UUID, rbac_service) -> bool:
        """Pre-warm user permissions cache."""
        try:
            permissions = await rbac_service.get_user_all_permissions(user_id)
            return await self.set_user_permissions(user_id, permissions)
        except Exception as e:
            print(f"Error warming user permissions cache: {e}")
            return False
    
    async def warm_role_permissions_cache(self, role_id: UUID, rbac_service) -> bool:
        """Pre-warm role permissions cache."""
        try:
            permissions = await rbac_service.get_role_inherited_permissions(role_id)
            return await self.set_role_permissions(role_id, permissions)
        except Exception as e:
            print(f"Error warming role permissions cache: {e}")
            return False
    
    # Cache statistics
    async def _update_cache_stats(self, cache_type: str, operation: str) -> None:
        """Update cache statistics."""
        stats_key = self._cache_stats_key()
        
        try:
            # Get current stats
            cached_stats = await cache_manager.get(stats_key)
            if cached_stats:
                stats = json.loads(cached_stats)
            else:
                stats = {}
            
            # Update stats
            if cache_type not in stats:
                stats[cache_type] = {'hits': 0, 'misses': 0, 'total': 0}
            
            stats[cache_type][operation + 's'] += 1
            stats[cache_type]['total'] += 1
            
            # Update last updated timestamp
            stats['last_updated'] = datetime.utcnow().isoformat()
            
            # Cache for 1 hour
            await cache_manager.set(stats_key, json.dumps(stats), 3600)
        except Exception as e:
            print(f"Error updating cache stats: {e}")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats_key = self._cache_stats_key()
        cached_stats = await cache_manager.get(stats_key)
        
        if cached_stats:
            stats = json.loads(cached_stats)
            
            # Calculate hit ratios
            for cache_type in stats:
                if cache_type != 'last_updated' and isinstance(stats[cache_type], dict):
                    hits = stats[cache_type].get('hits', 0)
                    total = stats[cache_type].get('total', 0)
                    if total > 0:
                        stats[cache_type]['hit_ratio'] = hits / total
                    else:
                        stats[cache_type]['hit_ratio'] = 0.0
            
            return stats
        
        return {'message': 'No cache statistics available'}
    
    async def clear_all_cache(self) -> Dict[str, Any]:
        """Clear all RBAC cache entries."""
        try:
            # Get all cache keys with our prefix
            pattern = f"{self.cache_prefix}*"
            deleted_count = await cache_manager.delete_pattern(pattern)
            
            return {
                'success': True,
                'message': f'Cleared {deleted_count} cache entries',
                'cleared_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error clearing cache: {e}',
                'error_at': datetime.utcnow().isoformat()
            }
    
    # Cache health check
    async def health_check(self) -> Dict[str, Any]:
        """Perform cache health check."""
        try:
            # Test cache connectivity
            test_key = f"{self.cache_prefix}health_check"
            test_value = "test_value"
            
            # Set test value
            set_success = await cache_manager.set(test_key, test_value, 60)
            
            # Get test value
            cached_value = await cache_manager.get(test_key)
            
            # Clean up test key
            await cache_manager.delete(test_key)
            
            # Get cache stats
            stats = await self.get_cache_stats()
            
            return {
                'status': 'healthy' if set_success and cached_value == test_value else 'unhealthy',
                'connectivity': 'ok' if set_success else 'error',
                'read_write': 'ok' if cached_value == test_value else 'error',
                'stats': stats,
                'checked_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'checked_at': datetime.utcnow().isoformat()
            }


# Global cache instance
rbac_cache = RBACCache()