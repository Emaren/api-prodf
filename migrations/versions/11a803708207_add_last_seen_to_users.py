"""Add last_seen to users

Revision ID: 11a803708207
Revises: de1b724f6c0e
Create Date: 2025-05-18 19:32:53.218392
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '11a803708207'
down_revision = 'de1b724f6c0e'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('users', sa.Column('last_seen', sa.DateTime(), nullable=True))

def downgrade():
    op.drop_column('users', 'last_seen')
