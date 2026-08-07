import inspect

from fastapi import APIRouter, HTTPException, File, UploadFile
from pydantic import BaseModel

from app.services.extractor import ExtractionError, extract_text


class ExtractedPage(BaseModel):
    page_number: int
    text: str


class UploadResponse(BaseModel):
    filename: str
    content_type: str
    page_count: int
    pages: list[ExtractedPage]


router = APIRouter(
    prefix="/upload",
    tags=["Upload"]
)


SUPPORTED_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/html",
    "text/plain",
}

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB
CHUNK_SIZE = 1024 * 1024          # 1 MB

@router.post("/", response_model=UploadResponse)
async def upload_doc(file: UploadFile = File(...)):
    normalized_content_type = file.content_type.split(";", 1)[0].strip().lower() if file.content_type else None

    if normalized_content_type not in SUPPORTED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}"
        )

    file_bytes = await file.read()

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File too large."
        )

    try:
        extracted_pages = extract_text(file_bytes, normalized_content_type)
        if inspect.isawaitable(extracted_pages):
            extracted_pages = await extracted_pages
    except ExtractionError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    return UploadResponse(
        filename=file.filename,
        content_type=file.content_type,
        page_count=len(extracted_pages),
        pages=extracted_pages,
    )
