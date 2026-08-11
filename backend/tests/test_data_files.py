from pathlib import Path

import pytest
from fastapi import HTTPException
from app.api import upload as upload_module
from app.services.cleaner import clean_text
from app.services.extractor import extract_text


DATA_DIR = Path(__file__).resolve().parents[2] / "data"

DATA_FILES = [
    ("amazon.pdf", "application/pdf"),
    ("Apple10k.pdf", "application/pdf"),
    ("MIcrosoft.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    ("NVIDIA.pdf", "application/pdf"),
    ("tesla.pdf", "application/pdf"),
]


@pytest.mark.parametrize("filename, content_type", DATA_FILES)
def test_extract_and_clean_real_data_file(filename, content_type):
    path = DATA_DIR / filename

    assert path.exists(), f"Missing data file: {path}"

    raw_bytes = path.read_bytes()
    extracted_pages = extract_text(raw_bytes, content_type)
    cleaned_pages = clean_text(extracted_pages)

    assert len(cleaned_pages) > 0
    assert cleaned_pages[0].page_number == 1
    assert any(page.text.strip() for page in cleaned_pages)
    assert all(page.page_number >= 1 for page in cleaned_pages)


class DummyUploadFile:
    def __init__(self, filename: str, content_type: str, file_bytes: bytes):
        self.filename = filename
        self.content_type = content_type
        self._file_bytes = file_bytes
        self._offset = 0

    async def read(self, size=-1):
        if self._offset >= len(self._file_bytes):
            return b""

        if size is None or size < 0:
            size = len(self._file_bytes) - self._offset

        start = self._offset
        end = min(start + size, len(self._file_bytes))
        self._offset = end
        return self._file_bytes[start:end]

@pytest.mark.asyncio
async def test_upload_doc_rejects_nvidia_pdf_over_size_limit_async():
    path = DATA_DIR / "NVIDIA.pdf"
    file = DummyUploadFile("NVIDIA.pdf", "application/pdf", path.read_bytes())

    with pytest.raises(HTTPException) as exc_info:
        await upload_module.upload_doc(file=file)

    assert exc_info.value.status_code == 413
    assert exc_info.value.detail == "File too large."


@pytest.mark.asyncio
async def test_upload_doc_accepts_smaller_pdf_from_data_folder():
    path = DATA_DIR / "Apple10k.pdf"
    file = DummyUploadFile("Apple10k.pdf", "application/pdf", path.read_bytes())

    response = await upload_module.upload_doc(file=file)

    assert response.filename == "Apple10k.pdf"
    assert response.content_type == "application/pdf"
    assert response.page_count > 0
