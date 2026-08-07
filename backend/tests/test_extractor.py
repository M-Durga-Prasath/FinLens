import pytest

from app.api import upload as upload_module
from app.services.extractor import ExtractionError, extract_text


def test_extract_text_supports_text_plain_with_charset():
    result = extract_text(b"hello world", "text/plain; charset=utf-8")

    assert result == [{"page_number": 1, "text": "hello world"}]


def test_extract_text_rejects_empty_bytes():
    with pytest.raises(ExtractionError):
        extract_text(b"", "text/plain")


@pytest.mark.asyncio
async def test_upload_doc_normalizes_content_type(monkeypatch):
    calls = {}

    class DummyUploadFile:
        filename = "notes.txt"
        content_type = "text/plain; charset=utf-8"

        async def read(self):
            return b"hello world"

    async def fake_extract_text(file_bytes, content_type):
        calls["content_type"] = content_type
        return [{"page_number": 1, "text": "hello world"}]

    monkeypatch.setattr(upload_module, "extract_text", fake_extract_text)

    response = await upload_module.upload_doc(file=DummyUploadFile())

    assert response.content_type == "text/plain; charset=utf-8"
    assert calls["content_type"] == "text/plain"


@pytest.mark.asyncio
async def test_upload_doc_returns_422_for_extraction_error(monkeypatch):
    class DummyUploadFile:
        filename = "notes.txt"
        content_type = "text/plain"

        async def read(self):
            return b"hello world"

    def fake_extract_text(*args, **kwargs):
        raise ExtractionError("Document is empty")

    monkeypatch.setattr(upload_module, "extract_text", fake_extract_text)

    with pytest.raises(Exception) as exc_info:
        await upload_module.upload_doc(file=DummyUploadFile())

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == "Document is empty"
