from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient

from app.api import upload as upload_module
from app.main import app
import app.main as main_module


DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "Apple10k.pdf"
TEST_USER_ID = UUID("11111111-1111-1111-1111-111111111111")
TEST_SESSION_ID = UUID("22222222-2222-2222-2222-222222222222")


async def _noop_async():
    return None


async def _fake_store_document(**kwargs):
    return UUID("33333333-3333-3333-3333-333333333333")


def _fake_embed_chunks(chunks):
    return []


def test_upload_api_with_one_real_file(monkeypatch):
    monkeypatch.setattr(main_module, "connect_db", _noop_async)
    monkeypatch.setattr(main_module, "close_db", _noop_async)
    monkeypatch.setattr(upload_module, "store_document", _fake_store_document)
    monkeypatch.setattr(upload_module, "embed_chunks", _fake_embed_chunks)

    assert DATA_FILE.exists(), f"Missing test file: {DATA_FILE}"

    with TestClient(app) as client:
        with DATA_FILE.open("rb") as f:
            response = client.post(
                "/upload/",
                files={"file": ("Apple10k.pdf", f, "application/pdf")},
                data={
                    "user_id": str(TEST_USER_ID),
                    "session_id": str(TEST_SESSION_ID),
                },
            )

    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "Apple10k.pdf"
    assert body["content_type"] == "application/pdf"
    assert body["page_count"] > 0
    assert body["status"] == "READY"
