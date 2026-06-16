import uuid
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.db_models import ChatMessage, TutorSession


@dataclass
class SessionState:
    session_id: uuid.UUID
    user_id: uuid.UUID
    llm_provider: str
    attempt_count: int = 0
    puzzle_triggered: bool = False
    active_exercise_id: str | None = None
    active_exercise_question: str | None = None
    active_exercise_starter_code: str | None = None
    active_exercise_solution: str | None = None
    history_window: list[dict] = field(default_factory=list)


async def load_session_state(
    session: TutorSession, db: AsyncSession
) -> SessionState:
    msg_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(settings.chat_history_window)
    )
    recent_messages = list(reversed(msg_result.scalars().all()))

    history = []
    for msg in recent_messages:
        if msg.role != "system":
            role = "user" if msg.role == "student" else "assistant"
            history.append({"role": role, "content": msg.content})

    exercise_question = None
    exercise_starter_code = None
    exercise_solution = None
    if session.exercise_id:
        from app.services.exercise_db import exercise_db
        problem = await exercise_db.get_problem_by_id(session.exercise_id)
        if problem:
            exercise_question = problem["question"]
            exercise_starter_code = problem.get("starter_code", "")
            exercise_solution = problem.get("solution", "")

    return SessionState(
        session_id=session.id,
        user_id=session.user_id,
        llm_provider=session.llm_provider,
        attempt_count=session.total_attempts,
        puzzle_triggered=session.puzzle_triggered,
        active_exercise_id=session.exercise_id,
        active_exercise_question=exercise_question,
        active_exercise_starter_code=exercise_starter_code,
        active_exercise_solution=exercise_solution,
        history_window=history,
    )


def apply_state_to_session(state: SessionState, session: TutorSession) -> None:
    session.total_attempts = state.attempt_count
    session.puzzle_triggered = state.puzzle_triggered
