from uuid import UUID

import app.services.bm25 as bm25_service


TEST_SESSION_ID = UUID("44444444-4444-4444-4444-444444444444")


def test_tokenize_text_keeps_financial_terms():
    tokens = bm25_service.tokenize_text("Revenue up 10k in Q4, EPS improved.")

    assert tokens == ["revenue", "up", "10k", "in", "q4", "eps", "improved"]


def test_rank_chunks_by_bm25_prefers_exact_keyword_match():
    chunks = [
        {
            "id": UUID("11111111-1111-1111-1111-111111111111"),
            "content": "Operating expenses were flat.",
            "page_number": 1,
            "chunk_index": 1,
            "token_count": 4,
        },
        {
            "id": UUID("22222222-2222-2222-2222-222222222222"),
            "content": "Revenue increased significantly this quarter.",
            "page_number": 2,
            "chunk_index": 2,
            "token_count": 5,
        },
        {
            "id": UUID("33333333-3333-3333-3333-333333333333"),
            "content": "Cash flow remained stable.",
            "page_number": 3,
            "chunk_index": 3,
            "token_count": 4,
        },
    ]

    results = bm25_service.rank_chunks_by_bm25("revenue quarter", chunks, top_k=2)

    assert len(results) == 2
    assert results[0]["id"] == chunks[1]["id"]
    assert results[0]["content"] == "Revenue increased significantly this quarter."
    assert results[0]["similarity"] > results[1]["similarity"]


def test_rank_chunks_by_bm25_returns_empty_for_blank_query():
    chunks = [
        {
            "id": UUID("11111111-1111-1111-1111-111111111111"),
            "content": "Revenue increased significantly.",
            "page_number": 1,
            "chunk_index": 1,
            "token_count": 4,
        }
    ]

    assert bm25_service.rank_chunks_by_bm25("   ", chunks) == []


class FakeDB:
    async def fetch(self, *args, **kwargs):
        assert args[1] == TEST_SESSION_ID
        return [
            {
                "id": UUID("11111111-1111-1111-1111-111111111111"),
                "content": "Operating expenses were flat.",
                "pageNumber": 1,
                "chunkIndex": 1,
                "tokenCount": 4,
            },
            {
                "id": UUID("22222222-2222-2222-2222-222222222222"),
                "content": "Revenue increased significantly this quarter.",
                "pageNumber": 2,
                "chunkIndex": 2,
                "tokenCount": 5,
            },
        ]


async def _fake_get_db():
    return FakeDB()


def test_retrieve_chunks_ranks_db_results(monkeypatch):
    monkeypatch.setattr(bm25_service, "get_db", _fake_get_db)

    import asyncio

    results = asyncio.run(
        bm25_service.retrieve_chunks(
            query="revenue",
            session_id=TEST_SESSION_ID,
            top_k=5,
        )
    )

    assert len(results) == 2
    assert results[0]["content"] == "Revenue increased significantly this quarter."
    assert results[0]["similarity"] >= results[1]["similarity"]
