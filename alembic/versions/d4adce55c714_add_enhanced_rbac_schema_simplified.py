"""Add enhanced RBAC schema - simplified

Revision ID: d4adce55c714
Revises: 4df33911dd8b
Create Date: 2025-07-10 01:34:21.789432

"""
from alembic import op
import sqlalchemy as sa
from app.db.base import UUIDType

# revision identifiers, used by Alembic.
revision = 'd4adce55c714'
down_revision = '4df33911dd8b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create permission_categories table
    op.create_table('permission_categories',
        sa.Column('code', sa.String(length=50), nullable=False, comment='Category code'),
        sa.Column('name', sa.String(length=100), nullable=False, comment='Category name'),
        sa.Column('description', sa.Text(), nullable=True, comment='Category description'),
        sa.Column('display_order', sa.Integer(), nullable=False, default=0, comment='Display order'),
        sa.Column('icon', sa.String(length=50), nullable=True, comment='Icon name'),
        sa.Column('color', sa.String(length=20), nullable=True, comment='Display color'),
        sa.Column('id', UUIDType(length=36), nullable=False, comment='Primary key'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False, comment='Record last update timestamp'),
        sa.Column('created_by', sa.String(length=255), nullable=True, comment='User who created the record'),
        sa.Column('updated_by', sa.String(length=255), nullable=True, comment='User who last updated the record'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True, comment='Soft delete flag'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Soft delete timestamp'),
        sa.Column('deleted_by', sa.String(length=255), nullable=True, comment='User who deleted the record'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    
    # Create rbac_audit_logs table
    op.create_table('rbac_audit_logs',
        sa.Column('user_id', UUIDType(length=36), nullable=True, comment='User ID'),
        sa.Column('action', sa.String(length=50), nullable=False, comment='Action performed'),
        sa.Column('entity_type', sa.String(length=50), nullable=False, comment='Entity type'),
        sa.Column('entity_id', UUIDType(length=36), nullable=True, comment='Entity ID'),
        sa.Column('changes', sa.Text(), nullable=True, comment='Changes made (JSON)'),
        sa.Column('ip_address', sa.String(length=45), nullable=True, comment='Client IP address'),
        sa.Column('user_agent', sa.String(length=500), nullable=True, comment='Client user agent'),
        sa.Column('timestamp', sa.DateTime(), nullable=False, default=sa.text('(CURRENT_TIMESTAMP)'), comment='Event timestamp'),
        sa.Column('success', sa.Boolean(), nullable=False, default=True, comment='Success flag'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='Error message if failed'),
        sa.Column('session_id', sa.String(length=255), nullable=True, comment='Session ID'),
        sa.Column('id', UUIDType(length=36), nullable=False, comment='Primary key'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False, comment='Record last update timestamp'),
        sa.Column('created_by', sa.String(length=255), nullable=True, comment='User who created the record'),
        sa.Column('updated_by', sa.String(length=255), nullable=True, comment='User who last updated the record'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True, comment='Soft delete flag'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Soft delete timestamp'),
        sa.Column('deleted_by', sa.String(length=255), nullable=True, comment='User who deleted the record'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create permission_dependencies table
    op.create_table('permission_dependencies',
        sa.Column('permission_id', UUIDType(length=36), nullable=False, comment='Permission ID'),
        sa.Column('depends_on_id', UUIDType(length=36), nullable=False, comment='Depends on permission ID'),
        sa.Column('id', UUIDType(length=36), nullable=False, comment='Primary key'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False, comment='Record last update timestamp'),
        sa.Column('created_by', sa.String(length=255), nullable=True, comment='User who created the record'),
        sa.Column('updated_by', sa.String(length=255), nullable=True, comment='User who last updated the record'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True, comment='Soft delete flag'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Soft delete timestamp'),
        sa.Column('deleted_by', sa.String(length=255), nullable=True, comment='User who deleted the record'),
        sa.ForeignKeyConstraint(['depends_on_id'], ['permissions.id'], ),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create user_permissions table
    op.create_table('user_permissions',
        sa.Column('user_id', UUIDType(length=36), nullable=False),
        sa.Column('permission_id', UUIDType(length=36), nullable=False),
        sa.Column('granted_by', UUIDType(length=36), nullable=True),
        sa.Column('granted_at', sa.DateTime(), nullable=False, default=sa.text('(CURRENT_TIMESTAMP)')),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['granted_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('user_id', 'permission_id')
    )
    
    # Create role_hierarchy table
    op.create_table('role_hierarchy',
        sa.Column('parent_role_id', UUIDType(length=36), nullable=False),
        sa.Column('child_role_id', UUIDType(length=36), nullable=False),
        sa.Column('inherit_permissions', sa.Boolean(), nullable=False, default=True),
        sa.ForeignKeyConstraint(['child_role_id'], ['roles.id'], ),
        sa.ForeignKeyConstraint(['parent_role_id'], ['roles.id'], ),
        sa.PrimaryKeyConstraint('parent_role_id', 'child_role_id')
    )
    
    # Add new columns to permissions table (only if they don't exist)
    # category_id already exists - add foreign key
    op.create_foreign_key('fk_permissions_category', 'permissions', 'permission_categories', ['category_id'], ['id'])
    
    # Add missing columns to permissions table
    op.add_column('permissions', sa.Column('risk_level', sa.String(length=20), nullable=False, server_default='LOW', comment='Risk level'))
    op.add_column('permissions', sa.Column('requires_approval', sa.Boolean(), nullable=False, server_default='0', comment='Requires approval flag'))
    op.add_column('permissions', sa.Column('code', sa.String(length=100), nullable=False, server_default='', comment='Permission code'))
    
    # Add new columns to roles table
    op.add_column('roles', sa.Column('template', sa.String(length=50), nullable=True, comment='Role template type'))
    op.add_column('roles', sa.Column('parent_role_id', UUIDType(length=36), nullable=True, comment='Parent role for hierarchy'))
    op.add_column('roles', sa.Column('can_be_deleted', sa.Boolean(), nullable=False, server_default='1', comment='Can be deleted flag'))
    op.add_column('roles', sa.Column('max_users', sa.Integer(), nullable=True, comment='Maximum users allowed'))
    op.create_foreign_key('fk_roles_parent', 'roles', 'roles', ['parent_role_id'], ['id'])
    
    # Add new columns to users table
    op.add_column('users', sa.Column('user_type', sa.String(length=20), nullable=False, server_default='USER', comment='User type hierarchy'))
    op.add_column('users', sa.Column('account_locked_until', sa.DateTime(), nullable=True, comment='Account locked until timestamp'))
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='0', comment='Email verification status'))
    op.add_column('users', sa.Column('email_verification_token', sa.String(length=255), nullable=True, comment='Email verification token'))
    op.add_column('users', sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='0', comment='Superuser flag'))


def downgrade() -> None:
    # Remove new columns from users table
    op.drop_column('users', 'is_superuser')
    op.drop_column('users', 'email_verification_token')
    op.drop_column('users', 'email_verified')
    op.drop_column('users', 'account_locked_until')
    op.drop_column('users', 'user_type')
    
    # Remove new columns from roles table
    op.drop_constraint('fk_roles_parent', 'roles', type_='foreignkey')
    op.drop_column('roles', 'max_users')
    op.drop_column('roles', 'can_be_deleted')
    op.drop_column('roles', 'parent_role_id')
    op.drop_column('roles', 'template')
    
    # Remove new columns from permissions table
    op.drop_constraint('fk_permissions_category', 'permissions', type_='foreignkey')
    op.drop_column('permissions', 'code')
    op.drop_column('permissions', 'requires_approval')
    op.drop_column('permissions', 'risk_level')
    
    # Drop new tables
    op.drop_table('role_hierarchy')
    op.drop_table('user_permissions')
    op.drop_table('permission_dependencies')
    op.drop_table('rbac_audit_logs')
    op.drop_table('permission_categories')