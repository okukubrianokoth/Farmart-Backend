"""merge all heads into one

Revision ID: 00b629e79c10
Revises: 554cd66ef274, bb984b935531, bc70818f31f5, f179f34ebfd8
Create Date: 2025-11-02 10:38:21.029428

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '00b629e79c10'
down_revision = ('554cd66ef274', 'bb984b935531', 'bc70818f31f5', 'f179f34ebfd8')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
