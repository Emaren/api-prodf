"""Remove duplicate operations for last_seen

Revision ID: 173e2e09e57f
Revises: cf85382dc83e
Create Date: 2025-06-08 11:38:30.551954
"""
from alembic import op
import sqlalchemy as sa

revision = "173e2e09e57f"
down_revision = "cf85382dc83e"
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Already applied by previous revisions — skip
    pass

def downgrade() -> None:
    # Nothing to undo
    pass

