"""merge all heads into one

Revision ID: 00b629e79c10
Revises: bb984b935531, bc70818f31f5, f179f34ebfd8
Create Date: 2025-11-02 10:38:21.029428
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '00b629e79c10'
down_revision = ('bb984b935531', 'bc70818f31f5', 'f179f34ebfd8')
branch_labels = None
depends_on = None


def upgrade():
    """Merge multiple heads into one unified migration history."""
    pass


def downgrade():
    """No downgrade logic required for merge migration."""
    pass
