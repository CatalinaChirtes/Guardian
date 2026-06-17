"""enable row level security on all public tables

Revision ID: b1c2d3e4f5a6
Revises: 8c5a12df6194
Create Date: 2026-06-17 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, None] = '8c5a12df6194'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = [
    'users',
    'tutor_sessions',
    'chat_messages',
    'code_snapshots',
    'feedback_events',
    'parsons_puzzle_events',
    'curriculum_documents',
    'research_events',
    'allowed_emails',
]


def upgrade() -> None:
    for table in TABLES:
        op.execute(f'ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY')
        op.execute(
            f'ALTER TABLE public.{table} FORCE ROW LEVEL SECURITY'
        )


def downgrade() -> None:
    for table in TABLES:
        op.execute(f'ALTER TABLE public.{table} DISABLE ROW LEVEL SECURITY')
