"""added categories table

Revision ID: a9bb1de39580
Revises: f897b6293f11
Create Date: 2024-10-13 22:31:42.379770

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a9bb1de39580'
down_revision: Union[str, None] = 'f897b6293f11'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('categories',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('description', sa.String(length=255), nullable=True),
    sa.Column('type', sa.Enum('INCOME', 'OUTCOME', name='category_type'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('categories')
