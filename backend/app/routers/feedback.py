from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.db_models import FeedbackEvent, ResearchEvent, TutorSession, User
from app.models.schemas import FeedbackCreate

router = APIRouter()


@router.post("", status_code=201)
async def submit_feedback(
    request: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TutorSession).where(
            TutorSession.id == request.session_id,
            TutorSession.user_id == current_user.id,
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    feedback = FeedbackEvent(
        session_id=request.session_id,
        message_id=request.message_id,
        user_id=current_user.id,
        feedback_type=request.feedback_type,
        value=request.value,
    )
    db.add(feedback)

    event = ResearchEvent(
        user_id=current_user.id,
        session_id=request.session_id,
        event_type="feedback",
        payload={
            "message_id": str(request.message_id),
            "feedback_type": request.feedback_type,
        },
    )
    db.add(event)
    await db.flush()

    return {"id": feedback.id}
