from uuid import UUID

from fastapi.testclient import TestClient

from app.main import app
import app.main as main_module
from app.api import retrive as retrive_module


TEST_SESSION_ID = UUID("44444444-4444-4444-4444-444444444444")


async def _noop_async():
    return None


def test_retrieve_api_returns_results(monkeypatch):
    monkeypatch.setattr(main_module, "connect_db", _noop_async)
    monkeypatch.setattr(main_module, "close_db", _noop_async)

    async def fake_retrieve_hybrid_chunks(query, session_id, top_k):
        assert query == "revenue"
        assert session_id == TEST_SESSION_ID
        assert top_k == 5
        return [
            {
                "id": UUID("55555555-5555-5555-5555-555555555555"),
                "content": "Revenue increased significantly.",
                "document_id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
                "document_filename": "annual_report.pdf",
                "page_number": 1,
                "chunk_index": 1,
                "token_count": 4,
                "similarity": 0.0325,
                "rrf_score": 0.0325,
            }
        ]

    monkeypatch.setattr(
        retrive_module,
        "retrieve_hybrid_chunks",
        fake_retrieve_hybrid_chunks,
    )

    with TestClient(app) as client:
            response = client.post(
                "/retrieve/",
                json={
                    "query": "revenue",
                    "session_id": str(TEST_SESSION_ID),
                    "top_k": 5,
                },
            )

    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "revenue"
    assert len(body["results"]) == 1
    assert body["results"][0]["content"] == "Revenue increased significantly."
    assert body["results"][0]["document_id"] == "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    assert body["results"][0]["document_filename"] == "annual_report.pdf"
    assert body["results"][0]["similarity"] == 0.0325
    assert body["results"][0]["rrf_score"] == 0.0325
