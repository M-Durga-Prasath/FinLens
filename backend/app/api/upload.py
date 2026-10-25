import inspect
import logging
from fastapi import APIRouter, Depends, HTTPException, File, Form, Request, UploadFile, status
from uuid import UUID
from app.auth.dependencies import get_current_user, verify_session_access
from app.db.database import get_db
from app.rate_limiter import limiter
from app.schemas.utils import UploadResponse
from app.services.extractor import ExtractionError, extract_text
from app.services.cleaner import clean_text
from app.services.chunking import chunk_text
from app.services.embedding import embed_chunks
from app.services.vector_store import store_document

router = APIRouter(prefix="/upload", tags=["Upload"])


SUPPORTED_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/html",
    "text/plain",
}

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB
CHUNK_SIZE = 1024 * 1024  # 1 MB


@router.post("/", response_model=UploadResponse)
@limiter.limit("10/minute")
async def upload_doc(
    request: Request,
    file: UploadFile = File(...),
    *,
    session_id: UUID = Form(...),
    current_user: dict = Depends(get_current_user),
):

    authenticated_user_id = UUID(current_user["userId"])

    await verify_session_access(session_id, current_user["userId"])
    normalized_content_type = (
        file.content_type.split(";", 1)[0].strip().lower()
        if file.content_type
        else None
    )

    if normalized_content_type not in SUPPORTED_TYPES:
        raise HTTPException(
            status_code=400, detail=f"Unsupported file type: {file.content_type}"
        )

    chunks = []
    total_size = 0
    while chunk := await file.read(CHUNK_SIZE):
        if not chunk:
            break

        total_size += len(chunk)

        if total_size > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large.")
        chunks.append(chunk)

    file_bytes = b"".join(chunks)

    try:
        extracted_pages = extract_text(file_bytes, normalized_content_type)
        if inspect.isawaitable(extracted_pages):
            extracted_pages = await extracted_pages

        cleaned_pages = clean_text(extracted_pages)
        chunks = chunk_text(cleaned_pages)
        embedded_chunks = embed_chunks(chunks)

        document_id = await store_document(
            filename=file.filename,
            filetype=normalized_content_type,
            user_id=authenticated_user_id,
            session_id=session_id,
            chunks=embedded_chunks,
        )

    except ExtractionError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        # import traceback
        # traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail="Failed to process document.",
        ) from exc

    return UploadResponse(
        document_id=document_id,
        filename=file.filename,
        content_type=file.content_type,
        page_count=len(cleaned_pages),
        # embedded_chunks=embedded_chunks,
        status="READY",
    )
