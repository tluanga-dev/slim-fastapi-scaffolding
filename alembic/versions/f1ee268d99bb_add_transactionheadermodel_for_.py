"""Add TransactionHeaderModel for inventory management

Revision ID: f1ee268d99bb
Revises: 
Create Date: 2025-07-09 05:07:24.770052

"""
from alembic import op
import sqlalchemy as sa
from app.db.base import UUID


# revision identifiers, used by Alembic.
revision = 'f1ee268d99bb'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('brands',
    sa.Column('id', UUID(), nullable=False),
    sa.Column('brand_name', sa.String(length=100), nullable=False),
    sa.Column('brand_code', sa.String(length=20), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('created_by', sa.String(length=255), nullable=True),
    sa.Column('updated_by', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_brand_active', 'brands', ['is_active'], unique=False)
    op.create_index('idx_brand_code', 'brands', ['brand_code'], unique=False)
    op.create_index('idx_brand_name', 'brands', ['brand_name'], unique=False)
    op.create_index('idx_brand_name_active', 'brands', ['brand_name', 'is_active'], unique=False)
    op.create_index(op.f('ix_brands_brand_code'), 'brands', ['brand_code'], unique=True)
    op.create_index(op.f('ix_brands_brand_name'), 'brands', ['brand_name'], unique=True)
    op.create_index(op.f('ix_brands_id'), 'brands', ['id'], unique=False)
    op.create_index(op.f('ix_brands_is_active'), 'brands', ['is_active'], unique=False)
    op.create_table('categories',
    sa.Column('id', UUID(length=36), nullable=False),
    sa.Column('category_name', sa.String(length=100), nullable=False),
    sa.Column('parent_category_id', UUID(length=36), nullable=True),
    sa.Column('category_path', sa.String(length=500), nullable=False),
    sa.Column('category_level', sa.Integer(), nullable=False),
    sa.Column('display_order', sa.Integer(), nullable=False),
    sa.Column('is_leaf', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_by', sa.String(length=100), nullable=True),
    sa.Column('updated_by', sa.String(length=100), nullable=True),
    sa.ForeignKeyConstraint(['parent_category_id'], ['categories.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_categories_category_name'), 'categories', ['category_name'], unique=False)
    op.create_index(op.f('ix_categories_category_path'), 'categories', ['category_path'], unique=False)
    op.create_index(op.f('ix_categories_is_active'), 'categories', ['is_active'], unique=False)
    op.create_index(op.f('ix_categories_parent_category_id'), 'categories', ['parent_category_id'], unique=False)
    op.create_table('customer_addresses',
    sa.Column('id', UUID(), nullable=False),
    sa.Column('customer_id', UUID(), nullable=False),
    sa.Column('address_type', sa.Enum('BILLING', 'SHIPPING', 'MAILING', 'BUSINESS', 'HOME', name='addresstype'), nullable=False),
    sa.Column('street', sa.String(length=200), nullable=False),
    sa.Column('address_line2', sa.String(length=200), nullable=True),
    sa.Column('city', sa.String(length=50), nullable=False),
    sa.Column('state', sa.String(length=50), nullable=False),
    sa.Column('country', sa.String(length=50), nullable=False),
    sa.Column('postal_code', sa.String(length=20), nullable=True),
    sa.Column('is_default', sa.Boolean(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('created_by', sa.String(length=255), nullable=True),
    sa.Column('updated_by', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_address_customer', 'customer_addresses', ['customer_id', 'is_active'], unique=False)
    op.create_index('idx_address_customer_default', 'customer_addresses', ['customer_id', 'is_default'], unique=False)
    op.create_index('idx_address_location', 'customer_addresses', ['city', 'state', 'country'], unique=False)
    op.create_index('idx_address_type_default', 'customer_addresses', ['customer_id', 'address_type', 'is_default'], unique=False)
    op.create_index(op.f('ix_customer_addresses_address_type'), 'customer_addresses', ['address_type'], unique=False)
    op.create_index(op.f('ix_customer_addresses_city'), 'customer_addresses', ['city'], unique=False)
    op.create_index(op.f('ix_customer_addresses_country'), 'customer_addresses', ['country'], unique=False)
    op.create_index(op.f('ix_customer_addresses_customer_id'), 'customer_addresses', ['customer_id'], unique=False)
    op.create_index(op.f('ix_customer_addresses_id'), 'customer_addresses', ['id'], unique=False)
    op.create_index(op.f('ix_customer_addresses_is_active'), 'customer_addresses', ['is_active'], unique=False)
    op.create_index(op.f('ix_customer_addresses_is_default'), 'customer_addresses', ['is_default'], unique=False)
    op.create_index(op.f('ix_customer_addresses_state'), 'customer_addresses', ['state'], unique=False)
    op.create_table('locations',
    sa.Column('id', UUID(), nullable=False),
    sa.Column('location_code', sa.String(length=50), nullable=False),
    sa.Column('location_name', sa.String(length=255), nullable=False),
    sa.Column('location_type', sa.Enum('STORE', 'WAREHOUSE', 'SERVICE_CENTER', name='locationtype'), nullable=False),
    sa.Column('address', sa.Text(), nullable=False),
    sa.Column('city', sa.String(length=100), nullable=False),
    sa.Column('state', sa.String(length=100), nullable=False),
    sa.Column('country', sa.String(length=100), nullable=False),
    sa.Column('postal_code', sa.String(length=20), nullable=True),
    sa.Column('contact_number', sa.String(length=20), nullable=True),
    sa.Column('email', sa.String(length=255), nullable=True),
    sa.Column('manager_user_id', UUID(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('created_by', sa.String(length=255), nullable=True),
    sa.Column('updated_by', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_locations_city'), 'locations', ['city'], unique=False)
    op.create_index(op.f('ix_locations_country'), 'locations', ['country'], unique=False)
    op.create_index(op.f('ix_locations_id'), 'locations', ['id'], unique=False)
    op.create_index(op.f('ix_locations_is_active'), 'locations', ['is_active'], unique=False)
    op.create_index(op.f('ix_locations_location_code'), 'locations', ['location_code'], unique=True)
    op.create_index(op.f('ix_locations_location_name'), 'locations', ['location_name'], unique=False)
    op.create_index(op.f('ix_locations_location_type'), 'locations', ['location_type'], unique=False)
    op.create_index(op.f('ix_locations_state'), 'locations', ['state'], unique=False)
    op.create_table('suppliers',
    sa.Column('id', UUID(), nullable=False),
    sa.Column('supplier_code', sa.String(length=50), nullable=False),
    sa.Column('company_name', sa.String(length=255), nullable=False),
    sa.Column('supplier_type', sa.Enum('MANUFACTURER', 'DISTRIBUTOR', 'RETAILER', 'SERVICE_PROVIDER', 'LOGISTICS', 'TECHNOLOGY', 'MATERIALS', 'EQUIPMENT', name='suppliertype'), nullable=False),
    sa.Column('contact_person', sa.String(length=255), nullable=True),
    sa.Column('email', sa.String(length=255), nullable=True),
    sa.Column('phone', sa.String(length=20), nullable=True),
    sa.Column('address', sa.Text(), nullable=True),
    sa.Column('tax_id', sa.String(length=50), nullable=True),
    sa.Column('payment_terms', sa.Enum('COD', 'NET15', 'NET30', 'NET45', 'NET60', 'NET90', 'PREPAID', name='paymentterms'), nullable=False),
    sa.Column('credit_limit', sa.DECIMAL(precision=15, scale=2), nullable=False),
    sa.Column('supplier_tier', sa.Enum('PREFERRED', 'STANDARD', 'RESTRICTED', name='suppliertier'), nullable=False),
    sa.Column('total_orders', sa.Integer(), nullable=False),
    sa.Column('total_spend', sa.DECIMAL(precision=15, scale=2), nullable=False),
    sa.Column('average_delivery_days', sa.Integer(), nullable=False),
    sa.Column('quality_rating', sa.DECIMAL(precision=3, scale=2), nullable=False),
    sa.Column('last_order_date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('created_by', sa.String(length=255), nullable=True),
    sa.Column('updated_by', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_suppliers_company_name'), 'suppliers', ['company_name'], unique=False)
    op.create_index(op.f('ix_suppliers_id'), 'suppliers', ['id'], unique=False)
    op.create_index(op.f('ix_suppliers_is_active'), 'suppliers', ['is_active'], unique=False)
    op.create_index(op.f('ix_suppliers_supplier_code'), 'suppliers', ['supplier_code'], unique=True)
    op.create_index(op.f('ix_suppliers_supplier_tier'), 'suppliers', ['supplier_tier'], unique=False)
    op.create_index(op.f('ix_suppliers_supplier_type'), 'suppliers', ['supplier_type'], unique=False)
    op.create_table('units_of_measurement',
    sa.Column('id', UUID(), nullable=False),
    sa.Column('unit_id', UUID(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('abbreviation', sa.String(length=10), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('created_by', sa.String(length=255), nullable=True),
    sa.Column('updated_by', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_unit_abbreviation_active', 'units_of_measurement', ['abbreviation', 'is_active'], unique=False)
    op.create_index('idx_unit_id_active', 'units_of_measurement', ['unit_id', 'is_active'], unique=False)
    op.create_index('idx_unit_name_active', 'units_of_measurement', ['name', 'is_active'], unique=False)
    op.create_index(op.f('ix_units_of_measurement_abbreviation'), 'units_of_measurement', ['abbreviation'], unique=False)
    op.create_index(op.f('ix_units_of_measurement_id'), 'units_of_measurement', ['id'], unique=False)
    op.create_index(op.f('ix_units_of_measurement_is_active'), 'units_of_measurement', ['is_active'], unique=False)
    op.create_index(op.f('ix_units_of_measurement_name'), 'units_of_measurement', ['name'], unique=False)
    op.create_index(op.f('ix_units_of_measurement_unit_id'), 'units_of_measurement', ['unit_id'], unique=True)
    op.create_table('items',
    sa.Column('item_id', UUID(length=36), nullable=False),
    sa.Column('sku', sa.String(length=100), nullable=False),
    sa.Column('item_name', sa.String(length=255), nullable=False),
    sa.Column('category_id', UUID(length=36), nullable=False),
    sa.Column('brand_id', UUID(length=36), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('is_serialized', sa.Boolean(), nullable=False),
    sa.Column('barcode', sa.String(length=100), nullable=True),
    sa.Column('model_number', sa.String(length=100), nullable=True),
    sa.Column('weight', sa.DECIMAL(precision=10, scale=3), nullable=True),
    sa.Column('dimensions', sa.JSON(), nullable=True),
    sa.Column('is_rentable', sa.Boolean(), nullable=False),
    sa.Column('is_saleable', sa.Boolean(), nullable=False),
    sa.Column('min_rental_days', sa.Integer(), nullable=False),
    sa.Column('rental_period', sa.Integer(), nullable=True),
    sa.Column('max_rental_days', sa.Integer(), nullable=True),
    sa.Column('rental_base_price', sa.DECIMAL(precision=10, scale=2), nullable=True),
    sa.Column('sale_base_price', sa.DECIMAL(precision=10, scale=2), nullable=True),
    sa.Column('id', UUID(length=36), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('created_by', sa.String(length=255), nullable=True),
    sa.Column('updated_by', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['brand_id'], ['brands.id'], ),
    sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_item_barcode_active', 'items', ['barcode', 'is_active'], unique=False)
    op.create_index('idx_item_brand_active', 'items', ['brand_id', 'is_active'], unique=False)
    op.create_index('idx_item_category_active', 'items', ['category_id', 'is_active'], unique=False)
    op.create_index('idx_item_name_active', 'items', ['item_name', 'is_active'], unique=False)
    op.create_index('idx_item_rentable_active', 'items', ['is_rentable', 'is_active'], unique=False)
    op.create_index('idx_item_saleable_active', 'items', ['is_saleable', 'is_active'], unique=False)
    op.create_index('idx_item_sku_active', 'items', ['sku', 'is_active'], unique=False)
    op.create_index(op.f('ix_items_barcode'), 'items', ['barcode'], unique=False)
    op.create_index(op.f('ix_items_brand_id'), 'items', ['brand_id'], unique=False)
    op.create_index(op.f('ix_items_category_id'), 'items', ['category_id'], unique=False)
    op.create_index(op.f('ix_items_id'), 'items', ['id'], unique=False)
    op.create_index(op.f('ix_items_is_active'), 'items', ['is_active'], unique=False)
    op.create_index(op.f('ix_items_is_rentable'), 'items', ['is_rentable'], unique=False)
    op.create_index(op.f('ix_items_is_saleable'), 'items', ['is_saleable'], unique=False)
    op.create_index(op.f('ix_items_item_id'), 'items', ['item_id'], unique=True)
    op.create_index(op.f('ix_items_item_name'), 'items', ['item_name'], unique=False)
    op.create_index(op.f('ix_items_model_number'), 'items', ['model_number'], unique=False)
    op.create_index(op.f('ix_items_sku'), 'items', ['sku'], unique=True)
    op.create_table('transaction_headers',
    sa.Column('transaction_number', sa.String(length=50), nullable=False),
    sa.Column('transaction_type', sa.Enum('SALE', 'RENTAL', 'RETURN', 'REFUND', 'PURCHASE', 'ADJUSTMENT', 'TRANSFER', name='transactiontype'), nullable=False),
    sa.Column('transaction_date', sa.DateTime(), nullable=False),
    sa.Column('customer_id', UUID(length=36), nullable=False),
    sa.Column('location_id', UUID(length=36), nullable=False),
    sa.Column('sales_person_id', UUID(length=36), nullable=True),
    sa.Column('status', sa.Enum('DRAFT', 'PENDING', 'CONFIRMED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', 'REFUNDED', name='transactionstatus'), nullable=False),
    sa.Column('payment_status', sa.Enum('PENDING', 'PARTIAL', 'PAID', 'OVERDUE', 'REFUNDED', 'CANCELLED', name='paymentstatus'), nullable=False),
    sa.Column('subtotal', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('discount_amount', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('tax_amount', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('total_amount', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('paid_amount', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('deposit_amount', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('reference_transaction_id', UUID(length=36), nullable=True),
    sa.Column('payment_method', sa.Enum('CASH', 'CREDIT_CARD', 'DEBIT_CARD', 'BANK_TRANSFER', 'CHECK', 'STORE_CREDIT', 'DIGITAL_WALLET', 'CRYPTOCURRENCY', 'INSTALLMENT', name='paymentmethod'), nullable=True),
    sa.Column('payment_reference', sa.String(length=100), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('id', UUID(length=36), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('created_by', sa.String(length=255), nullable=True),
    sa.Column('updated_by', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ),
    sa.ForeignKeyConstraint(['reference_transaction_id'], ['transaction_headers.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_customer_transaction_date', 'transaction_headers', ['customer_id', 'transaction_date'], unique=False)
    op.create_index('idx_location_transaction_date', 'transaction_headers', ['location_id', 'transaction_date'], unique=False)
    op.create_index('idx_payment_status_active', 'transaction_headers', ['payment_status', 'is_active'], unique=False)
    op.create_index('idx_transaction_date_type', 'transaction_headers', ['transaction_date', 'transaction_type'], unique=False)
    op.create_index('idx_transaction_number', 'transaction_headers', ['transaction_number'], unique=False)
    op.create_index('idx_transaction_status_active', 'transaction_headers', ['status', 'is_active'], unique=False)
    op.create_index('idx_transaction_type_status', 'transaction_headers', ['transaction_type', 'status'], unique=False)
    op.create_index(op.f('ix_transaction_headers_customer_id'), 'transaction_headers', ['customer_id'], unique=False)
    op.create_index(op.f('ix_transaction_headers_id'), 'transaction_headers', ['id'], unique=False)
    op.create_index(op.f('ix_transaction_headers_is_active'), 'transaction_headers', ['is_active'], unique=False)
    op.create_index(op.f('ix_transaction_headers_location_id'), 'transaction_headers', ['location_id'], unique=False)
    op.create_index(op.f('ix_transaction_headers_payment_status'), 'transaction_headers', ['payment_status'], unique=False)
    op.create_index(op.f('ix_transaction_headers_status'), 'transaction_headers', ['status'], unique=False)
    op.create_index(op.f('ix_transaction_headers_transaction_date'), 'transaction_headers', ['transaction_date'], unique=False)
    op.create_index(op.f('ix_transaction_headers_transaction_number'), 'transaction_headers', ['transaction_number'], unique=True)
    op.create_index(op.f('ix_transaction_headers_transaction_type'), 'transaction_headers', ['transaction_type'], unique=False)
    op.create_table('inventory_units',
    sa.Column('inventory_code', sa.String(length=50), nullable=False),
    sa.Column('serial_number', sa.String(length=100), nullable=True),
    sa.Column('current_status', sa.Enum('AVAILABLE_RENTAL', 'AVAILABLE_SALE', 'RENTED', 'SOLD', 'MAINTENANCE', 'DAMAGED', 'LOST', 'RETIRED', name='inventorystatus'), nullable=False),
    sa.Column('condition_grade', sa.Enum('A', 'B', 'C', 'D', 'F', name='conditiongrade'), nullable=False),
    sa.Column('purchase_date', sa.Date(), nullable=True),
    sa.Column('purchase_cost', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('current_value', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('last_inspection_date', sa.Date(), nullable=True),
    sa.Column('total_rental_days', sa.Integer(), nullable=False),
    sa.Column('rental_count', sa.Integer(), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('item_id', UUID(length=36), nullable=False),
    sa.Column('location_id', UUID(length=36), nullable=False),
    sa.Column('id', UUID(length=36), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('created_by', sa.String(length=255), nullable=True),
    sa.Column('updated_by', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['item_id'], ['items.id'], ),
    sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_inventory_active', 'inventory_units', ['is_active'], unique=False)
    op.create_index('idx_inventory_code', 'inventory_units', ['inventory_code'], unique=False)
    op.create_index('idx_inventory_condition', 'inventory_units', ['condition_grade'], unique=False)
    op.create_index('idx_inventory_item', 'inventory_units', ['item_id'], unique=False)
    op.create_index('idx_inventory_item_status', 'inventory_units', ['item_id', 'current_status'], unique=False)
    op.create_index('idx_inventory_location', 'inventory_units', ['location_id'], unique=False)
    op.create_index('idx_inventory_location_status', 'inventory_units', ['location_id', 'current_status'], unique=False)
    op.create_index('idx_inventory_purchase_date', 'inventory_units', ['purchase_date'], unique=False)
    op.create_index('idx_inventory_serial', 'inventory_units', ['serial_number'], unique=False)
    op.create_index('idx_inventory_status', 'inventory_units', ['current_status'], unique=False)
    op.create_index('idx_inventory_status_active', 'inventory_units', ['current_status', 'is_active'], unique=False)
    op.create_index(op.f('ix_inventory_units_condition_grade'), 'inventory_units', ['condition_grade'], unique=False)
    op.create_index(op.f('ix_inventory_units_current_status'), 'inventory_units', ['current_status'], unique=False)
    op.create_index(op.f('ix_inventory_units_id'), 'inventory_units', ['id'], unique=False)
    op.create_index(op.f('ix_inventory_units_inventory_code'), 'inventory_units', ['inventory_code'], unique=True)
    op.create_index(op.f('ix_inventory_units_is_active'), 'inventory_units', ['is_active'], unique=False)
    op.create_index(op.f('ix_inventory_units_item_id'), 'inventory_units', ['item_id'], unique=False)
    op.create_index(op.f('ix_inventory_units_location_id'), 'inventory_units', ['location_id'], unique=False)
    op.create_index(op.f('ix_inventory_units_purchase_date'), 'inventory_units', ['purchase_date'], unique=False)
    op.create_index(op.f('ix_inventory_units_serial_number'), 'inventory_units', ['serial_number'], unique=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_inventory_units_serial_number'), table_name='inventory_units')
    op.drop_index(op.f('ix_inventory_units_purchase_date'), table_name='inventory_units')
    op.drop_index(op.f('ix_inventory_units_location_id'), table_name='inventory_units')
    op.drop_index(op.f('ix_inventory_units_item_id'), table_name='inventory_units')
    op.drop_index(op.f('ix_inventory_units_is_active'), table_name='inventory_units')
    op.drop_index(op.f('ix_inventory_units_inventory_code'), table_name='inventory_units')
    op.drop_index(op.f('ix_inventory_units_id'), table_name='inventory_units')
    op.drop_index(op.f('ix_inventory_units_current_status'), table_name='inventory_units')
    op.drop_index(op.f('ix_inventory_units_condition_grade'), table_name='inventory_units')
    op.drop_index('idx_inventory_status_active', table_name='inventory_units')
    op.drop_index('idx_inventory_status', table_name='inventory_units')
    op.drop_index('idx_inventory_serial', table_name='inventory_units')
    op.drop_index('idx_inventory_purchase_date', table_name='inventory_units')
    op.drop_index('idx_inventory_location_status', table_name='inventory_units')
    op.drop_index('idx_inventory_location', table_name='inventory_units')
    op.drop_index('idx_inventory_item_status', table_name='inventory_units')
    op.drop_index('idx_inventory_item', table_name='inventory_units')
    op.drop_index('idx_inventory_condition', table_name='inventory_units')
    op.drop_index('idx_inventory_code', table_name='inventory_units')
    op.drop_index('idx_inventory_active', table_name='inventory_units')
    op.drop_table('inventory_units')
    op.drop_index(op.f('ix_transaction_headers_transaction_type'), table_name='transaction_headers')
    op.drop_index(op.f('ix_transaction_headers_transaction_number'), table_name='transaction_headers')
    op.drop_index(op.f('ix_transaction_headers_transaction_date'), table_name='transaction_headers')
    op.drop_index(op.f('ix_transaction_headers_status'), table_name='transaction_headers')
    op.drop_index(op.f('ix_transaction_headers_payment_status'), table_name='transaction_headers')
    op.drop_index(op.f('ix_transaction_headers_location_id'), table_name='transaction_headers')
    op.drop_index(op.f('ix_transaction_headers_is_active'), table_name='transaction_headers')
    op.drop_index(op.f('ix_transaction_headers_id'), table_name='transaction_headers')
    op.drop_index(op.f('ix_transaction_headers_customer_id'), table_name='transaction_headers')
    op.drop_index('idx_transaction_type_status', table_name='transaction_headers')
    op.drop_index('idx_transaction_status_active', table_name='transaction_headers')
    op.drop_index('idx_transaction_number', table_name='transaction_headers')
    op.drop_index('idx_transaction_date_type', table_name='transaction_headers')
    op.drop_index('idx_payment_status_active', table_name='transaction_headers')
    op.drop_index('idx_location_transaction_date', table_name='transaction_headers')
    op.drop_index('idx_customer_transaction_date', table_name='transaction_headers')
    op.drop_table('transaction_headers')
    op.drop_index(op.f('ix_items_sku'), table_name='items')
    op.drop_index(op.f('ix_items_model_number'), table_name='items')
    op.drop_index(op.f('ix_items_item_name'), table_name='items')
    op.drop_index(op.f('ix_items_item_id'), table_name='items')
    op.drop_index(op.f('ix_items_is_saleable'), table_name='items')
    op.drop_index(op.f('ix_items_is_rentable'), table_name='items')
    op.drop_index(op.f('ix_items_is_active'), table_name='items')
    op.drop_index(op.f('ix_items_id'), table_name='items')
    op.drop_index(op.f('ix_items_category_id'), table_name='items')
    op.drop_index(op.f('ix_items_brand_id'), table_name='items')
    op.drop_index(op.f('ix_items_barcode'), table_name='items')
    op.drop_index('idx_item_sku_active', table_name='items')
    op.drop_index('idx_item_saleable_active', table_name='items')
    op.drop_index('idx_item_rentable_active', table_name='items')
    op.drop_index('idx_item_name_active', table_name='items')
    op.drop_index('idx_item_category_active', table_name='items')
    op.drop_index('idx_item_brand_active', table_name='items')
    op.drop_index('idx_item_barcode_active', table_name='items')
    op.drop_table('items')
    op.drop_index(op.f('ix_units_of_measurement_unit_id'), table_name='units_of_measurement')
    op.drop_index(op.f('ix_units_of_measurement_name'), table_name='units_of_measurement')
    op.drop_index(op.f('ix_units_of_measurement_is_active'), table_name='units_of_measurement')
    op.drop_index(op.f('ix_units_of_measurement_id'), table_name='units_of_measurement')
    op.drop_index(op.f('ix_units_of_measurement_abbreviation'), table_name='units_of_measurement')
    op.drop_index('idx_unit_name_active', table_name='units_of_measurement')
    op.drop_index('idx_unit_id_active', table_name='units_of_measurement')
    op.drop_index('idx_unit_abbreviation_active', table_name='units_of_measurement')
    op.drop_table('units_of_measurement')
    op.drop_index(op.f('ix_suppliers_supplier_type'), table_name='suppliers')
    op.drop_index(op.f('ix_suppliers_supplier_tier'), table_name='suppliers')
    op.drop_index(op.f('ix_suppliers_supplier_code'), table_name='suppliers')
    op.drop_index(op.f('ix_suppliers_is_active'), table_name='suppliers')
    op.drop_index(op.f('ix_suppliers_id'), table_name='suppliers')
    op.drop_index(op.f('ix_suppliers_company_name'), table_name='suppliers')
    op.drop_table('suppliers')
    op.drop_index(op.f('ix_locations_state'), table_name='locations')
    op.drop_index(op.f('ix_locations_location_type'), table_name='locations')
    op.drop_index(op.f('ix_locations_location_name'), table_name='locations')
    op.drop_index(op.f('ix_locations_location_code'), table_name='locations')
    op.drop_index(op.f('ix_locations_is_active'), table_name='locations')
    op.drop_index(op.f('ix_locations_id'), table_name='locations')
    op.drop_index(op.f('ix_locations_country'), table_name='locations')
    op.drop_index(op.f('ix_locations_city'), table_name='locations')
    op.drop_table('locations')
    op.drop_index(op.f('ix_customer_addresses_state'), table_name='customer_addresses')
    op.drop_index(op.f('ix_customer_addresses_is_default'), table_name='customer_addresses')
    op.drop_index(op.f('ix_customer_addresses_is_active'), table_name='customer_addresses')
    op.drop_index(op.f('ix_customer_addresses_id'), table_name='customer_addresses')
    op.drop_index(op.f('ix_customer_addresses_customer_id'), table_name='customer_addresses')
    op.drop_index(op.f('ix_customer_addresses_country'), table_name='customer_addresses')
    op.drop_index(op.f('ix_customer_addresses_city'), table_name='customer_addresses')
    op.drop_index(op.f('ix_customer_addresses_address_type'), table_name='customer_addresses')
    op.drop_index('idx_address_type_default', table_name='customer_addresses')
    op.drop_index('idx_address_location', table_name='customer_addresses')
    op.drop_index('idx_address_customer_default', table_name='customer_addresses')
    op.drop_index('idx_address_customer', table_name='customer_addresses')
    op.drop_table('customer_addresses')
    op.drop_index(op.f('ix_categories_parent_category_id'), table_name='categories')
    op.drop_index(op.f('ix_categories_is_active'), table_name='categories')
    op.drop_index(op.f('ix_categories_category_path'), table_name='categories')
    op.drop_index(op.f('ix_categories_category_name'), table_name='categories')
    op.drop_table('categories')
    op.drop_index(op.f('ix_brands_is_active'), table_name='brands')
    op.drop_index(op.f('ix_brands_id'), table_name='brands')
    op.drop_index(op.f('ix_brands_brand_name'), table_name='brands')
    op.drop_index(op.f('ix_brands_brand_code'), table_name='brands')
    op.drop_index('idx_brand_name_active', table_name='brands')
    op.drop_index('idx_brand_name', table_name='brands')
    op.drop_index('idx_brand_code', table_name='brands')
    op.drop_index('idx_brand_active', table_name='brands')
    op.drop_table('brands')
    # ### end Alembic commands ###