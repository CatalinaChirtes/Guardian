import asyncio
import logging
import os
import tempfile
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.db_models import CurriculumDocument, ResearchEvent, User
from app.models.schemas import CurriculumDocumentResponse
from app.services.rag import rag_engine
from app.services import storage

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_DOCUMENTS = 10
MAX_FILE_SIZE = 20 * 1024 * 1024


@router.post("/upload", response_model=CurriculumDocumentResponse, status_code=201)
async def upload_curriculum(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    if not file.filename.endswith((".pdf", ".txt")):
        raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported")

    safe_filename = os.path.basename(file.filename)
    if not safe_filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    existing = await db.execute(
        select(CurriculumDocument).where(
            CurriculumDocument.user_id == current_user.id,
            CurriculumDocument.filename == safe_filename,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"'{safe_filename}' has already been uploaded")

    count_result = await db.execute(
        select(func.count()).where(CurriculumDocument.user_id == current_user.id)
    )
    doc_count = count_result.scalar() or 0
    if doc_count >= MAX_DOCUMENTS:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum of {MAX_DOCUMENTS} documents allowed. Delete a document before uploading a new one.",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)}MB.",
        )
    if safe_filename.endswith(".pdf") and not content[:5].startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="File content does not match PDF format")
    if safe_filename.endswith(".txt"):
        try:
            content.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="File is not valid UTF-8 text")

    suffix = os.path.splitext(safe_filename)[1]
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp_path = tmp.name
    try:
        await asyncio.to_thread(tmp.write, content)
        await asyncio.to_thread(tmp.close)

        doc = CurriculumDocument(
            user_id=current_user.id,
            filename=safe_filename,
            chunk_count=0,
        )
        db.add(doc)
        await db.flush()

        storage_path = f"{current_user.id}/{doc.id}_{safe_filename}"
        try:
            await asyncio.to_thread(storage.upload_file, tmp_path, storage_path)
        except Exception as e:
            logger.warning("Failed to upload file to Supabase Storage: %s", e)

        chunk_count = await rag_engine.ingest_file(tmp_path, str(doc.id), safe_filename)
        doc.chunk_count = chunk_count

        event = ResearchEvent(
            user_id=current_user.id,
            event_type="curriculum_upload",
            payload={"filename": safe_filename, "chunk_count": chunk_count},
        )
        db.add(event)
        await db.flush()

        return doc
    finally:
        os.unlink(tmp_path)


@router.get("", response_model=list[CurriculumDocumentResponse])
async def list_curriculum(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CurriculumDocument)
        .where(CurriculumDocument.user_id == current_user.id)
        .order_by(CurriculumDocument.uploaded_at.desc())
    )
    return result.scalars().all()


@router.delete("/{doc_id}", status_code=204)
async def delete_curriculum(
    doc_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CurriculumDocument).where(
            CurriculumDocument.id == doc_id,
            CurriculumDocument.user_id == current_user.id,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    await rag_engine.delete_document(str(doc.id))

    storage_path = f"{current_user.id}/{doc.id}_{doc.filename}"
    try:
        await asyncio.to_thread(storage.delete_file, storage_path)
    except Exception as e:
        logger.warning("Failed to delete file from Supabase Storage: %s", e)

    await db.delete(doc)

    db.add(ResearchEvent(
        user_id=current_user.id,
        event_type="curriculum_delete",
        payload={"filename": doc.filename, "doc_id": str(doc.id)},
    ))
    await db.flush()


