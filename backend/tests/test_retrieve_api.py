from uuid import UUID

from fastapi.testclient import TestClient

from app.api import retrive as retrive_module
from app.main import app
import app.main as main_module
import app.services.retriever as retriever_service


TEST_SESSION_ID = UUID("44444444-4444-4444-4444-444444444444")


async def _noop_async():
    return None


class FakeModel:
    def encode(self, query, normalize_embeddings=True):
        return [0.1, 0.2, 0.3]


class FakeDB:
    async def fetch(self, *args, **kwargs):
        assert args[2] == TEST_SESSION_ID
        return [
            {
                "id": UUID("55555555-5555-5555-5555-555555555555"),
                "content": "Revenue increased significantly.",
                "pageNumber": 1,
                "chunkIndex": 1,
                "tokenCount": 4,
                "similarity": 0.92,
            }
        ]


async def _fake_get_db():
    return FakeDB()


def test_retrieve_api_returns_results(monkeypatch):
    monkeypatch.setattr(main_module, "connect_db", _noop_async)
    monkeypatch.setattr(main_module, "close_db", _noop_async)
    monkeypatch.setattr(retriever_service, "get_db", _fake_get_db)
    monkeypatch.setattr(retriever_service, "get_model", lambda: FakeModel())

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
    assert body["results"][0]["similarity"] == 0.92
