import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255))
    group_label: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())

    sessions: Mapped[list["TutorSession"]] = relationship(back_populates="user")
    feedback_events: Mapped[list["FeedbackEvent"]] = relationship(back_populates="user")


class TutorSession(Base):
    __tablename__ = "tutor_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    session_type: Mapped[str] = mapped_column(String(20), nullable=False, default="chat")
    exercise_id: Mapped[str | None] = mapped_column(String(100))
    title: Mapped[str | None] = mapped_column(String(500))
    llm_provider: Mapped[str] = mapped_column(String(50), nullable=False)
    total_attempts: Mapped[int] = mapped_column(Integer, default=0)
    puzzle_triggered: Mapped[bool] = mapped_column(Boolean, default=False)
    solved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(DateTime)

    user: Mapped["User"] = relationship(back_populates="sessions")
    messages: Mapped[list["ChatMessage"]] = relationship(back_populates="session")
    code_snapshots: Mapped[list["CodeSnapshot"]] = relationship(back_populates="session")
    puzzle_events: Mapped[list["ParsonsPuzzleEvent"]] = relationship(
        back_populates="session"
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tutor_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    mode: Mapped[str | None] = mapped_column(String(50))
    llm_provider: Mapped[str | None] = mapped_column(String(50))
    llm_model: Mapped[str | None] = mapped_column(String(100))
    prompt_tokens: Mapped[int | None] = mapped_column(Integer)
    completion_tokens: Mapped[int | None] = mapped_column(Integer)
    latency_ms: Mapped[float | None] = mapped_column(Float)
    sources: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())

    session: Mapped["TutorSession"] = relationship(back_populates="messages")
    feedback_events: Mapped[list["FeedbackEvent"]] = relationship(
        back_populates="message"
    )


class CodeSnapshot(Base):
    __tablename__ = "code_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tutor_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chat_messages.id", ondelete="CASCADE")
    )
    code: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str | None] = mapped_column(String(20))
    syntax_errors: Mapped[dict | None] = mapped_column(JSONB)
    attempt_number: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())

    session: Mapped["TutorSession"] = relationship(back_populates="code_snapshots")


class FeedbackEvent(Base):
    __tablename__ = "feedback_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tutor_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chat_messages.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    feedback_type: Mapped[str] = mapped_column(String(20), nullable=False)
    value: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="feedback_events")
    message: Mapped["ChatMessage"] = relationship(back_populates="feedback_events")


class ParsonsPuzzleEvent(Base):
    __tablename__ = "parsons_puzzle_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tutor_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    correct_order: Mapped[list] = mapped_column(JSONB, nullable=False)
    student_order: Mapped[list | None] = mapped_column(JSONB)
    is_correct: Mapped[bool | None] = mapped_column(Boolean)
    attempt_number: Mapped[int] = mapped_column(Integer, default=0)
    time_spent_seconds: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())

    session: Mapped["TutorSession"] = relationship(back_populates="puzzle_events")


class CurriculumDocument(Base):
    __tablename__ = "curriculum_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())


class AllowedEmail(Base):
    __tablename__ = "allowed_emails"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
        server_default=func.gen_random_uuid()
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())


class ResearchEvent(Base):
    __tablename__ = "research_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tutor_sessions.id", ondelete="CASCADE"), index=True
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())
