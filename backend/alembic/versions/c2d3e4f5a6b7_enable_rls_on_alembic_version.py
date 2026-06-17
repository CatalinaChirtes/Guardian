"""enable rls on alembic_version table

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-06-17 12:30:00.000000
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'c2d3e4f5a6b7'
down_revision: Union[str, None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('ALTER TABLE public.alembic_version ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE public.alembic_version FORCE ROW LEVEL SECURITY')


def downgrade() -> None:
    op.execute('ALTER TABLE public.alembic_version DISABLE ROW LEVEL SECURITY')
