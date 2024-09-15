"""creating table users

Revision ID: 6efc39319011
Revises: 
Create Date: 2024-09-15 10:54:03.625039

"""
from datetime import datetime

import sqlalchemy as sa
from typing import Sequence, Union
from alembic import op


# revision identifiers, used by Alembic.
revision: str = '6efc39319011'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Определение схемы базы данных
metadata = sa.MetaData()
user = sa.Table('user', metadata)


def upgrade():
    # Добавление новой таблицы
    op.create_table('users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(100)),
        sa.Column('username', sa.String(50), nullable=False, unique=True),
        sa.Column('email', sa.String(100), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(100), nullable=False),
        sa.Column('superuser', sa.Boolean, default=False),
        sa.Column('created_on', sa.DateTime(), default=datetime.utcnow),
        sa.Column('updated_on', sa.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow))


def downgrade():
    # Удаление новой таблицы
    op.drop_table('users')
