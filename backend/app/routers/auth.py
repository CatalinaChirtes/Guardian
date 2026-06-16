import logging
import re
import time
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from supabase import Client, create_client

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.db_models import AllowedEmail, User
from app.models.schemas import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    UserResponse,
)

logger = logging.getLogger(__name__)

_login_attempts: dict[str, list[float]] = defaultdict(list)
MAX_LOGIN_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 300

router = APIRouter()

_escaped_domain = re.escape(settings.allowed_email_domain)
EMAIL_REGEX = re.compile(rf"^[a-zA-Z0-9._%+-]+@{_escaped_domain}$")

_supabase_client: Client | None = None
_supabase_admin: Client | None = None


def get_supabase_client() -> Client:
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(settings.supabase_url, settings.supabase_key)
    return _supabase_client


def get_supabase_admin() -> Client:
    global _supabase_admin
    if _supabase_admin is None:
        _supabase_admin = create_client(settings.supabase_url, settings.supabase_service_key)
    return _supabase_admin


async def _check_registration_allowed(email: str, db: AsyncSession) -> None:
    if settings.registration_mode == "allowlist":
        is_university = bool(EMAIL_REGEX.match(email))
        if not is_university:
            result = await db.execute(
                select(AllowedEmail).where(AllowedEmail.email == email)
            )
            if result.scalar_one_or_none() is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Registration is currently by invitation only. Please complete the pre-study survey first.",
                )
    elif settings.registration_mode == "domain":
        if not EMAIL_REGEX.match(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only @{settings.allowed_email_domain} emails are allowed",
            )


@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    await _check_registration_allowed(request.email, db)

    supabase = get_supabase_client()
    try:
        response = supabase.auth.sign_up(
            {
                "email": request.email,
                "password": request.password,
            }
        )
    except Exception as e:
        logger.warning("Registration failed for %s: %s", request.email, e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed. Please try again.",
        )

    if response.user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed",
        )

    if not response.user.identities:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    return AuthResponse(
        access_token="",
        refresh_token="",
        user_id=str(response.user.id),
        email=request.email,
    )


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    email = request.email.lower()
    now = time.monotonic()
    attempts = _login_attempts[email]
    attempts[:] = [t for t in attempts if now - t < LOGIN_WINDOW_SECONDS]
    if not attempts:
        _login_attempts.pop(email, None)
        attempts = _login_attempts[email]
    if len(attempts) >= MAX_LOGIN_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
        )
    attempts.append(now)
    supabase = get_supabase_client()
    try:
        response = supabase.auth.sign_in_with_password(
            {"email": request.email, "password": request.password}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    return AuthResponse(
        access_token=response.session.access_token,
        refresh_token=response.session.refresh_token,
        user_id=str(response.user.id),
        email=response.user.email,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
