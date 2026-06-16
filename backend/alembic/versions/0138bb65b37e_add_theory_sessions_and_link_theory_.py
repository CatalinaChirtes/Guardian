"""Add theory_sessions and link theory_messages

Revision ID: 0138bb65b37e
Revises: 477887f8a894
Create Date: 2026-05-13 11:23:49.987895
"""
from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '0138bb65b37e'
down_revision: Union[str, None] = '477887f8a894'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('theory_sessions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.add_column('theory_messages', sa.Column('session_id', sa.UUID(), nullable=True))

    conn = op.get_bind()
    rows = conn.execute(
        sa.text("SELECT DISTINCT user_id FROM theory_messages WHERE session_id IS NULL")
    ).fetchall()
    for (user_id,) in rows:
        session_id = uuid4()
        min_ts = conn.execute(
            sa.text("SELECT MIN(created_at) FROM theory_messages WHERE user_id = :uid"),
            {"uid": user_id},
        ).scalar()
        conn.execute(
            sa.text(
                "INSERT INTO theory_sessions (id, user_id, created_at) VALUES (:sid, :uid, :ts)"
            ),
            {"sid": session_id, "uid": user_id, "ts": min_ts},
        )
        conn.execute(
            sa.text(
                "UPDATE theory_messages SET session_id = :sid WHERE user_id = :uid AND session_id IS NULL"
            ),
            {"sid": session_id, "uid": user_id},
        )

    op.alter_column('theory_messages', 'session_id', nullable=False)
    op.create_foreign_key(
        'fk_theory_messages_session_id', 'theory_messages', 'theory_sessions',
        ['session_id'], ['id'],
    )


def downgrade() -> None:
    op.drop_constraint('fk_theory_messages_session_id', 'theory_messages', type_='foreignkey')
    op.drop_column('theory_messages', 'session_id')
    op.drop_table('theory_sessions')
