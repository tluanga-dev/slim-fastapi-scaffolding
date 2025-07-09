"""Merge migration heads

Revision ID: 5f8a6196db7c
Revises: 2a3b4c5d6e7f, complete_rental_system
Create Date: 2025-07-09 12:08:36.811479

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5f8a6196db7c'
down_revision = ('2a3b4c5d6e7f', 'complete_rental_system')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass