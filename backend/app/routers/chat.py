import asyncio
import json
import logging
import time
import uuid

import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.database as _db
from app.config import settings
from app.dependencies import decode_supabase_jwt, ensure_user
from app.models.db_models import (
    ChatMessage,
    CodeSnapshot,
    CurriculumDocument,
    ParsonsPuzzleEvent,
    ResearchEvent,
    TutorSession,
    User,
)
from app.services.intent import classify_intent
from app.services.llm.factory import get_provider
from app.services.parsons import check_puzzle_solution
from app.services.rag import rag_engine
from app.services.session_manager import (
    SessionState,
    apply_state_to_session,
    load_session_state,
)
from app.services.static_analysis import analyze_code
from app.services.tutor import generate_theory_response, generate_tutor_response

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_MESSAGE_SIZE = 65_536
MAX_MESSAGES_PER_MINUTE = 10


async def authenticate_ws(token: str, db: AsyncSession) -> User | None:
    try:
        payload = decode_supabase_jwt(token)
        user_id = payload.get("sub")
        if not user_id:
            return None
    except jwt.PyJWTError:
        return None

    uid = uuid.UUID(user_id)
    email = payload.get("email", "")
    try:
        return await ensure_user(uid, email, db)
    except Exception:
        return None


async def _save_student_message(
    db: AsyncSession, state: SessionState, content: str
) -> ChatMessage:
    student_msg = ChatMessage(
        session_id=state.session_id,
        role="student",
        content=content,
        mode=None,
    )
    db.add(student_msg)
    await db.flush()
    return student_msg


async def _set_session_title(
    db: AsyncSession, session: TutorSession, content: str
) -> None:
    if not session.title and content.strip():
        session.title = content.strip()[:80]


async def _save_code_snapshot(
    db: AsyncSession, state: SessionState, msg: ChatMessage, code: str
) -> dict | None:
    analysis = analyze_code(code)
    snapshot = CodeSnapshot(
        session_id=state.session_id,
        message_id=msg.id,
        code=code,
        language=analysis["language"],
        syntax_errors={"errors": analysis["errors"]} if analysis["errors"] else None,
        attempt_number=state.attempt_count,
    )
    db.add(snapshot)
    return analysis


async def _generate_response(
    state: SessionState, provider, content: str, code: str,
    user_doc_ids: set[str] | None = None, skip_solution_check: bool = False
):
    result = None
    if settings.enable_rag:
        intent = await classify_intent(content, code, rag_engine.is_loaded, provider)
        if intent == "theory":
            rag_results = await rag_engine.search(content, user_doc_ids=user_doc_ids)
            if rag_results:
                result = await generate_theory_response(
                    user_query=content,
                    rag_results=rag_results,
                    state=state,
                    provider=provider,
                )

    if result is None:
        result = await generate_tutor_response(
            student_code=code,
            user_query=content,
            state=state,
            provider=provider,
            skip_solution_check=skip_solution_check,
        )
    return result


async def _persist_puzzle(
    db: AsyncSession, websocket: WebSocket, state: SessionState, user: User, result
) -> None:
    shuffled_lines = result.puzzle_data["shuffled_lines"]

    puzzle_msg = ChatMessage(
        session_id=state.session_id,
        role="tutor",
        content=result.content,
        mode="puzzle",
        sources=json.dumps(shuffled_lines),
    )
    db.add(puzzle_msg)
    await db.flush()

    await websocket.send_text(
        json.dumps({
            "type": "puzzle",
            "content": result.content,
            "lines": shuffled_lines,
            "mode": "puzzle",
            "message_id": str(puzzle_msg.id),
        })
    )

    db.add(ParsonsPuzzleEvent(
        session_id=state.session_id,
        user_id=user.id,
        correct_order=result.puzzle_data["correct_order"],
    ))

    db.add(ResearchEvent(
        user_id=user.id,
        session_id=state.session_id,
        event_type="puzzle_triggered",
        payload={"attempt_number": state.attempt_count},
    ))


async def _persist_response(
    db: AsyncSession, websocket: WebSocket, state: SessionState,
    session: TutorSession, user: User, result
) -> None:
    tutor_msg = ChatMessage(
        session_id=state.session_id,
        role="tutor",
        content=result.content,
        mode=result.mode,
        llm_provider=result.llm_response.provider if result.llm_response else None,
        llm_model=result.llm_response.model if result.llm_response else None,
        prompt_tokens=result.llm_response.prompt_tokens if result.llm_response else None,
        completion_tokens=result.llm_response.completion_tokens if result.llm_response else None,
        latency_ms=result.llm_response.latency_ms if result.llm_response else None,
        sources=result.sources,
    )
    db.add(tutor_msg)
    await db.flush()

    if result.challenge_solved:
        session.solved = True

    await websocket.send_text(
        json.dumps({
            "type": "response",
            "content": result.content,
            "message_id": str(tutor_msg.id),
            "mode": result.mode,
            "challenge_solved": result.challenge_solved,
            "sources": result.sources,
        })
    )

    db.add(ResearchEvent(
        user_id=user.id,
        session_id=state.session_id,
        event_type="hint_delivered",
        payload={
            "mode": result.mode,
            "llm_provider": result.llm_response.provider if result.llm_response else None,
            "llm_model": result.llm_response.model if result.llm_response else None,
            "prompt_tokens": result.llm_response.prompt_tokens if result.llm_response else 0,
            "completion_tokens": result.llm_response.completion_tokens if result.llm_response else 0,
            "latency_ms": result.llm_response.latency_ms if result.llm_response else 0,
            "code_police_triggered": result.code_police_triggered,
            "code_police_retries": result.code_police_retries,
        },
    ))


async def handle_message(
    websocket: WebSocket,
    user: User,
    session: TutorSession,
    state: SessionState,
    provider,
    data: dict,
    last_checked_code: dict,
):
    content = data.get("content", "")
    code = data.get("code", "")
    code_hash = hash(code.strip()) if code.strip() else None
    skip_solution_check = code_hash is not None and code_hash == last_checked_code["hash"]

    async with _db.async_session() as db:
        student_msg = await _save_student_message(db, state, content)
        await _set_session_title(db, session, content)

        analysis = None
        if code.strip():
            analysis = await _save_code_snapshot(db, state, student_msg, code)
            await websocket.send_text(json.dumps({
                "type": "analysis",
                "language": analysis["language"],
                "is_valid": analysis["is_valid"],
                "feedback": analysis["feedback"],
                "errors": analysis["errors"],
            }))

        user_doc_ids = None
        if rag_engine.is_loaded:
            doc_result = await db.execute(
                select(CurriculumDocument.id).where(CurriculumDocument.user_id == user.id)
            )
            user_doc_ids = {str(doc_id) for doc_id in doc_result.scalars().all()}

        result = await _generate_response(state, provider, content, code, user_doc_ids, skip_solution_check)

        if code_hash is not None:
            last_checked_code["hash"] = code_hash

        if result.mode == "puzzle" and result.puzzle_data:
            await _persist_puzzle(db, websocket, state, user, result)
        else:
            await _persist_response(db, websocket, state, session, user, result)

        state.history_window.append({"role": "user", "content": content})
        state.history_window.append({"role": "assistant", "content": result.content})
        max_window = settings.chat_history_window * 2
        if len(state.history_window) > max_window:
            state.history_window = state.history_window[-max_window:]

        apply_state_to_session(state, session)
        await db.merge(session)
        await db.commit()


async def handle_puzzle_submit(
    websocket: WebSocket,
    user: User,
    session: TutorSession,
    state: SessionState,
    data: dict,
):
    student_order = data.get("student_order", [])

    async with _db.async_session() as db:
        result = await db.execute(
            select(ParsonsPuzzleEvent)
            .where(
                ParsonsPuzzleEvent.session_id == state.session_id,
                ParsonsPuzzleEvent.user_id == user.id,
            )
            .order_by(ParsonsPuzzleEvent.created_at.desc())
            .limit(1)
        )
        puzzle_event = result.scalar_one_or_none()

        if puzzle_event is None:
            await websocket.send_text(
                json.dumps({"type": "error", "message": "No active puzzle found"})
            )
            return

        correct = check_puzzle_solution(student_order, puzzle_event.correct_order)

        puzzle_event.student_order = student_order
        puzzle_event.is_correct = correct
        puzzle_event.attempt_number += 1
        time_spent = data.get("time_spent_seconds")
        if time_spent:
            puzzle_event.time_spent_seconds = time_spent

        if correct:
            session.solved = True

        result_text = "Correct! Well done!" if correct else "Not quite right. Try again!"
        result_msg = ChatMessage(
            session_id=state.session_id,
            role="tutor",
            content=result_text,
            mode="puzzle_result",
        )
        db.add(result_msg)
        await db.flush()

        db.add(ResearchEvent(
            user_id=user.id,
            session_id=state.session_id,
            event_type="puzzle_attempt",
            payload={
                "is_correct": correct,
                "attempt_number": puzzle_event.attempt_number,
                "time_spent_seconds": time_spent,
            },
        ))

        apply_state_to_session(state, session)
        await db.merge(session)
        await db.commit()

        await websocket.send_text(
            json.dumps({
                "type": "puzzle_result",
                "is_correct": correct,
                "message": result_text,
                "message_id": str(result_msg.id),
            })
        )


@router.websocket("/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: uuid.UUID):
    await websocket.accept()

    try:
        raw = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
        auth_msg = json.loads(raw)
        if auth_msg.get("type") != "auth" or not auth_msg.get("token"):
            await websocket.close(code=4001, reason="Missing auth")
            return
        token = auth_msg["token"]
    except (asyncio.TimeoutError, json.JSONDecodeError):
        await websocket.close(code=4001, reason="Auth timeout")
        return

    if _db.async_session is None:
        await websocket.close(code=4003, reason="Database not initialized")
        return

    async with _db.async_session() as db:
        user = await authenticate_ws(token, db)
        if user is None:
            await websocket.close(code=4001, reason="Invalid token")
            return

        result = await db.execute(
            select(TutorSession).where(
                TutorSession.id == session_id,
                TutorSession.user_id == user.id,
            )
        )
        session = result.scalar_one_or_none()
        if session is None:
            await websocket.close(code=4004, reason="Session not found")
            return

        db.expunge(user)
        db.expunge(session)

        state = await load_session_state(session, db)
        await db.commit()

    provider = get_provider(state.llm_provider)
    message_timestamps: list[float] = []
    last_checked_code = {"hash": None}

    try:
        while True:
            raw = await websocket.receive_text()

            if len(raw) > MAX_MESSAGE_SIZE:
                await websocket.send_text(
                    json.dumps({"type": "error", "message": "Message too large"})
                )
                continue

            now = time.monotonic()
            message_timestamps[:] = [t for t in message_timestamps if now - t < 60]
            if len(message_timestamps) >= MAX_MESSAGES_PER_MINUTE:
                await websocket.send_text(
                    json.dumps({"type": "error", "message": "Too many messages. Please wait a moment."})
                )
                continue
            message_timestamps.append(now)

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(
                    json.dumps({"type": "error", "message": "Invalid message format"})
                )
                continue
            msg_type = data.get("type", "message")

            if msg_type == "message":
                await handle_message(
                    websocket, user, session, state, provider, data, last_checked_code
                )
            elif msg_type == "puzzle_submit":
                await handle_puzzle_submit(
                    websocket, user, session, state, data
                )

    except WebSocketDisconnect:
        async with _db.async_session() as db:
            db.add(ResearchEvent(
                user_id=user.id,
                session_id=session_id,
                event_type="session_end",
                payload={
                    "total_attempts": state.attempt_count,
                    "puzzle_triggered": state.puzzle_triggered,
                },
            ))
            await db.commit()
    except Exception as e:
        logger.exception("WebSocket error for session %s", session_id)
        try:
            await websocket.send_text(
                json.dumps({"type": "error", "message": "An internal error occurred"})
            )
        except Exception:
            pass
