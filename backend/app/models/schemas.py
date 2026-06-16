import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator


class RegisterRequest(BaseModel):
    email: str
    password: str
    display_name: str | None = None

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    user_id: str
    email: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str | None
    group_label: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionCreate(BaseModel):
    exercise_id: str | None = None
    title: str | None = None
    llm_provider: Literal["gemini", "openai", "anthropic", "ollama-qwen", "ollama-gemma"] = "gemini"


class SessionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    session_type: str
    exercise_id: str | None
    title: str | None
    llm_provider: str
    total_attempts: int
    puzzle_triggered: bool
    solved: bool
    created_at: datetime
    ended_at: datetime | None

    model_config = {"from_attributes": True}


class ChatMessageResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    mode: str | None
    llm_provider: str | None
    llm_model: str | None
    latency_ms: float | None
    sources: str | None = None
    feedback: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionDetailResponse(SessionResponse):
    messages: list[ChatMessageResponse] = []
    last_code: str | None = None
    last_language: str | None = None


class ExerciseResponse(BaseModel):
    id: str
    question: str
    starter_code: str
    difficulty: str


class FeedbackCreate(BaseModel):
    session_id: uuid.UUID
    message_id: uuid.UUID
    feedback_type: Literal["thumbs_up", "thumbs_down", "free_text"]
    value: str | None = None


class CurriculumDocumentResponse(BaseModel):
    id: uuid.UUID
    filename: str
    chunk_count: int
    uploaded_at: datetime

    model_config = {"from_attributes": True}


