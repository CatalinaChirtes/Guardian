import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.db_models import ChatMessage, CodeSnapshot, TutorSession, User
from app.models.schemas import SessionCreate, SessionDetailResponse, SessionResponse

router = APIRouter()


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    request: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = TutorSession(
        user_id=current_user.id,
        session_type="challenge" if request.exercise_id else "chat",
        exercise_id=request.exercise_id,
        title=request.title,
        llm_provider=request.llm_provider,
    )
    db.add(session)
    await db.flush()
    return session


@router.get("", response_model=list[SessionResponse])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    has_messages = exists().where(ChatMessage.session_id == TutorSession.id)
    result = await db.execute(
        select(TutorSession)
        .where(TutorSession.user_id == current_user.id, has_messages)
        .order_by(TutorSession.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TutorSession)
        .options(
            selectinload(TutorSession.messages).selectinload(ChatMessage.feedback_events)
        )
        .where(
            TutorSession.id == session_id,
            TutorSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    snapshot_result = await db.execute(
        select(CodeSnapshot)
        .where(CodeSnapshot.session_id == session_id)
        .order_by(CodeSnapshot.created_at.desc())
        .limit(1)
    )
    last_snapshot = snapshot_result.scalar_one_or_none()

    feedback_by_msg = {
        m.id: m.feedback_events[-1].feedback_type
        for m in session.messages
        if m.feedback_events
    }

    resp = SessionDetailResponse.model_validate(session)
    for msg_resp in resp.messages:
        msg_resp.feedback = feedback_by_msg.get(msg_resp.id)
    if last_snapshot:
        resp.last_code = last_snapshot.code
        resp.last_language = last_snapshot.language
    return resp
