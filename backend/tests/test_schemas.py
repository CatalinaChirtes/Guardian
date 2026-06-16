import pytest
from pydantic import ValidationError

from app.models.schemas import FeedbackCreate, RegisterRequest, SessionCreate


def test_register_accepts_any_email():
    req = RegisterRequest(email="user@gmail.com", password="securepass123")
    assert req.email == "user@gmail.com"


def test_register_lowercases_email():
    req = RegisterRequest(email="Student@E-UVT.RO", password="securepass123")
    assert req.email == "student@e-uvt.ro"


def test_register_strips_whitespace():
    req = RegisterRequest(email="  student@e-uvt.ro  ", password="securepass123")
    assert req.email == "student@e-uvt.ro"


def test_register_rejects_short_password():
    with pytest.raises(ValidationError, match="at least 8 characters"):
        RegisterRequest(email="student@e-uvt.ro", password="short")


def test_register_accepts_valid_password():
    req = RegisterRequest(email="student@e-uvt.ro", password="longpassword123")
    assert req.password == "longpassword123"


def test_session_create_validates_provider():
    with pytest.raises(ValidationError):
        SessionCreate(llm_provider="invalid_provider")


def test_session_create_accepts_valid_providers():
    for provider in ["gemini", "openai", "anthropic", "ollama-qwen", "ollama-gemma"]:
        session = SessionCreate(llm_provider=provider)
        assert session.llm_provider == provider


def test_session_create_defaults_to_gemini():
    session = SessionCreate()
    assert session.llm_provider == "gemini"


def test_feedback_validates_type():
    with pytest.raises(ValidationError):
        FeedbackCreate(
            session_id="00000000-0000-0000-0000-000000000001",
            message_id="00000000-0000-0000-0000-000000000002",
            feedback_type="invalid_type",
        )


def test_feedback_accepts_valid_types():
    for ftype in ["thumbs_up", "thumbs_down", "free_text"]:
        fb = FeedbackCreate(
            session_id="00000000-0000-0000-0000-000000000001",
            message_id="00000000-0000-0000-0000-000000000002",
            feedback_type=ftype,
        )
        assert fb.feedback_type == ftype
