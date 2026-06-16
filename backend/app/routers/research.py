import csv
import io

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_admin_user
from app.models.db_models import ResearchEvent, User

router = APIRouter()


@router.get("/export")
async def export_research_data(
    format: str = Query("csv", enum=["csv", "json"]),
    limit: int = Query(10000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ResearchEvent)
        .order_by(ResearchEvent.created_at)
        .limit(limit)
        .offset(offset)
    )
    events = result.scalars().all()

    count_result = await db.execute(select(func.count()).select_from(ResearchEvent))
    total = count_result.scalar() or 0

    if format == "json":
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "events": [
                {
                    "id": str(e.id),
                    "user_id": str(e.user_id) if e.user_id else None,
                    "session_id": str(e.session_id) if e.session_id else None,
                    "event_type": e.event_type,
                    "payload": e.payload,
                    "created_at": e.created_at.isoformat(),
                }
                for e in events
            ],
        }

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        ["id", "user_id", "session_id", "event_type", "payload", "created_at"]
    )
    for e in events:
        writer.writerow(
            [
                str(e.id),
                str(e.user_id) if e.user_id else "",
                str(e.session_id) if e.session_id else "",
                e.event_type,
                str(e.payload) if e.payload else "",
                e.created_at.isoformat(),
            ]
        )
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=research_events.csv"},
    )
