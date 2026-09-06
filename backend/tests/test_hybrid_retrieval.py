from uuid import UUID

import pytest

import app.services.hybird_retrival as hybrid_service


CHUNK_A = UUID("11111111-1111-1111-1111-111111111111")
CHUNK_B = UUID("22222222-2222-2222-2222-222222222222")
CHUNK_C = UUID("33333333-3333-3333-3333-333333333333")
TEST_SESSION_ID = UUID("44444444-4444-4444-4444-444444444444")


def _chunk(chunk_id, content, similarity=0.9):
    return {
        "id": chunk_id,
        "content": content,
        "page_number": 1,
        "chunk_index": 1,
        "token_count": 4,
        "similarity": similarity,
    }


def test_reciprocal_rank_fusion_prefers_chunk_returned_by_both_retrievers():
    dense_results = [
        _chunk(CHUNK_A, "semantic match"),
        _chunk(CHUNK_B, "shared match"),
    ]
    bm25_results = [
        _chunk(CHUNK_B, "shared match", similarity=2.1),
        _chunk(CHUNK_C, "keyword match", similarity=1.5),
    ]

    results = hybrid_service.reciprocal_rank_fusion(
        [dense_results, bm25_results],
        rrf_k=60,
    )

    assert [result["id"] for result in results] == [CHUNK_B, CHUNK_A, CHUNK_C]
    assert results[0]["rrf_score"] == pytest.approx(1 / 62 + 1 / 61)
    assert results[0]["similarity"] == results[0]["rrf_score"]


@pytest.mark.asyncio
async def test_retrieve_hybrid_chunks_fuses_dense_and_bm25(monkeypatch):
    async def fake_dense(query, session_id, top_k):
        assert query == "revenue"
        assert session_id == TEST_SESSION_ID
        assert top_k == 20
        return [
            _chunk(CHUNK_A, "semantic match"),
            _chunk(CHUNK_B, "shared match"),
        ]

    async def fake_bm25(query, session_id, top_k):
        assert query == "revenue"
        assert session_id == TEST_SESSION_ID
        assert top_k == 20
        return [
            _chunk(CHUNK_B, "shared match", similarity=2.1),
            _chunk(CHUNK_C, "keyword match", similarity=0.0),
        ]

    monkeypatch.setattr(hybrid_service, "retrieve_dense_chunks", fake_dense)
    monkeypatch.setattr(hybrid_service, "retrieve_bm25_chunks", fake_bm25)

    results = await hybrid_service.retrieve_hybrid_chunks(
        query="revenue",
        session_id=TEST_SESSION_ID,
        top_k=2,
    )

    assert [result["id"] for result in results] == [CHUNK_B, CHUNK_A]
