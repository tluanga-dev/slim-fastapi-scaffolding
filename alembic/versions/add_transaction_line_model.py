"""Add TransactionLineModel with rental support

Revision ID: 2a3b4c5d6e7f
Revises: f1ee268d99bb
Create Date: 2025-01-09 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2a3b4c5d6e7f'
down_revision = 'f1ee268d99bb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create transaction_lines table
    op.create_table('transaction_lines',
        sa.Column('id', sa.CHAR(36), nullable=False),
        sa.Column('transaction_id', sa.CHAR(36), nullable=False),
        sa.Column('line_number', sa.Integer(), nullable=False),
        sa.Column('line_type', sa.Enum('product', 'service', 'rental', 'deposit', 'fee', 'discount', 'tax', 'shipping', 'adjustment', name='lineitemtype'), nullable=False),
        sa.Column('item_id', sa.CHAR(36), nullable=True),
        sa.Column('inventory_unit_id', sa.CHAR(36), nullable=True),
        sa.Column('description', sa.String(500), nullable=False),
        sa.Column('quantity', sa.Numeric(10, 3), nullable=False, server_default='1'),
        sa.Column('unit_price', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('discount_percentage', sa.Numeric(5, 2), nullable=False, server_default='0'),
        sa.Column('discount_amount', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('tax_rate', sa.Numeric(5, 2), nullable=False, server_default='0'),
        sa.Column('tax_amount', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('line_total', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('rental_period_value', sa.Integer(), nullable=True),
        sa.Column('rental_period_unit', sa.Enum('hour', 'day', 'week', 'month', 'year', name='rentalperiodunit'), nullable=True),
        sa.Column('rental_start_date', sa.Date(), nullable=True),
        sa.Column('rental_end_date', sa.Date(), nullable=True),
        sa.Column('returned_quantity', sa.Numeric(10, 3), nullable=False, server_default='0'),
        sa.Column('return_date', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('updated_by', sa.String(255), nullable=True),
        sa.ForeignKeyConstraint(['transaction_id'], ['transaction_headers.id'], ),
        sa.ForeignKeyConstraint(['item_id'], ['items.id'], ),
        sa.ForeignKeyConstraint(['inventory_unit_id'], ['inventory_units.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_transaction_lines_id'), 'transaction_lines', ['id'])
    op.create_index(op.f('ix_transaction_lines_is_active'), 'transaction_lines', ['is_active'])
    op.create_index('ix_transaction_lines_transaction_id', 'transaction_lines', ['transaction_id'])
    op.create_index('ix_transaction_lines_line_type', 'transaction_lines', ['line_type'])
    op.create_index('ix_transaction_lines_item_id', 'transaction_lines', ['item_id'])
    op.create_index('ix_transaction_lines_inventory_unit_id', 'transaction_lines', ['inventory_unit_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_transaction_lines_inventory_unit_id', table_name='transaction_lines')
    op.drop_index('ix_transaction_lines_item_id', table_name='transaction_lines')
    op.drop_index('ix_transaction_lines_line_type', table_name='transaction_lines')
    op.drop_index('ix_transaction_lines_transaction_id', table_name='transaction_lines')
    op.drop_index(op.f('ix_transaction_lines_is_active'), table_name='transaction_lines')
    op.drop_index(op.f('ix_transaction_lines_id'), table_name='transaction_lines')
    
    # Drop table
    op.drop_table('transaction_lines')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS lineitemtype')
    op.execute('DROP TYPE IF EXISTS rentalperiodunit')