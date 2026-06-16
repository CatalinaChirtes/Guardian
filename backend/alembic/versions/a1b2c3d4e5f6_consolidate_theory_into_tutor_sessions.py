"""Consolidate theory tables into tutor_sessions and chat_messages

Revision ID: a1b2c3d4e5f6
Revises: 69b799662096
Create Date: 2026-05-13 18:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '69b799662096'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('chat_messages', sa.Column('sources', sa.Text(), nullable=True))

    conn = op.get_bind()

    conn.execute(sa.text(
        "INSERT INTO tutor_sessions (id, user_id, session_type, llm_provider, total_attempts, puzzle_triggered, solved, created_at) "
        "SELECT id, user_id, 'theory', 'gemini', 0, FALSE, FALSE, created_at "
        "FROM theory_sessions"
    ))

    conn.execute(sa.text(
        "INSERT INTO chat_messages (id, session_id, role, content, mode, llm_provider, llm_model, sources, created_at) "
        "SELECT id, session_id, "
        "CASE WHEN role = 'professor' THEN 'tutor' ELSE role END, "
        "content, 'theory', llm_provider, llm_model, sources, created_at "
        "FROM theory_messages"
    ))

    op.drop_table('theory_messages')
    op.drop_table('theory_sessions')


def downgrade() -> None:
    op.create_table(
        'theory_sessions',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('user_id', sa.UUID(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime()),
    )
    op.create_table(
        'theory_messages',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('session_id', sa.UUID(), sa.ForeignKey('theory_sessions.id'), nullable=False),
        sa.Column('user_id', sa.UUID(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('llm_provider', sa.String(50)),
        sa.Column('llm_model', sa.String(100)),
        sa.Column('sources', sa.Text()),
        sa.Column('created_at', sa.DateTime()),
    )

    conn = op.get_bind()

    conn.execute(sa.text(
        "INSERT INTO theory_sessions (id, user_id, created_at) "
        "SELECT id, user_id, created_at FROM tutor_sessions WHERE session_type = 'theory'"
    ))

    conn.execute(sa.text(
        "INSERT INTO theory_messages (id, session_id, user_id, role, content, llm_provider, llm_model, sources, created_at) "
        "SELECT cm.id, cm.session_id, ts.user_id, "
        "CASE WHEN cm.role = 'tutor' THEN 'professor' ELSE cm.role END, "
        "cm.content, cm.llm_provider, cm.llm_model, cm.sources, cm.created_at "
        "FROM chat_messages cm JOIN tutor_sessions ts ON cm.session_id = ts.id "
        "WHERE ts.session_type = 'theory'"
    ))

    conn.execute(sa.text("DELETE FROM chat_messages WHERE session_id IN (SELECT id FROM tutor_sessions WHERE session_type = 'theory')"))
    conn.execute(sa.text("DELETE FROM tutor_sessions WHERE session_type = 'theory'"))

    op.drop_column('chat_messages', 'sources')
