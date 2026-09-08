from uuid import UUID, uuid4

import pytest

from app.services import reranker

TEST_DOC_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
TEST_DOC_FILENAME = "annual_report.pdf"


def make_chunk(chunk_id: str, content: str) -> dict:
    return {
        "id": chunk_id,
        "content": content,
        "document_id": TEST_DOC_ID,
        "document_filename": TEST_DOC_FILENAME,
        "page_number": 1,
        "chunk_index": 0,
        "token_count": 10,
        "similarity": 0.5,
        "rrf_score": 0.02,
    }


class FakeReranker:
    def predict(self, pairs):
        scores = []

        for query, content in pairs:
            if "revenue" in content.lower():
                scores.append(10.0)
            elif "profit" in content.lower():
                scores.append(5.0)
            else:
                scores.append(1.0)

        return scores


def test_rerank_chunks_orders_by_reranker_score(monkeypatch):
    chunks = [
        make_chunk(
            "chunk-1",
            "The company reported increased operating expenses.",
        ),
        make_chunk(
            "chunk-2",
            "The company's total revenue was $100 million.",
        ),
        make_chunk(
            "chunk-3",
            "Net profit increased compared with last year.",
        ),
    ]

    monkeypatch.setattr(
        reranker,
        "get_reranker",
        lambda: FakeReranker(),
    )

    results = reranker.rerank_chunks(
        query="What was the company's revenue?",
        chunks=chunks,
        top_k=3,
    )

    result_ids = [chunk["id"] for chunk in results]

    assert result_ids == [
        "chunk-2",
        "chunk-3",
        "chunk-1",
    ]

    assert results[0]["reranker_score"] == 10.0
    assert results[0]["similarity"] == 10.0
    assert results[0]["document_id"] == TEST_DOC_ID
    assert results[0]["document_filename"] == TEST_DOC_FILENAME


def test_rerank_chunks_respects_top_k(monkeypatch):
    chunks = [
        make_chunk("chunk-1", "General information"),
        make_chunk("chunk-2", "Revenue information"),
        make_chunk("chunk-3", "Profit information"),
    ]

    monkeypatch.setattr(
        reranker,
        "get_reranker",
        lambda: FakeReranker(),
    )

    results = reranker.rerank_chunks(
        query="What was the revenue?",
        chunks=chunks,
        top_k=2,
    )

    assert len(results) == 2

    assert results[0]["id"] == "chunk-2"
    assert results[1]["id"] == "chunk-3"


def test_rerank_chunks_empty_chunks():
    results = reranker.rerank_chunks(
        query="What was the revenue?",
        chunks=[],
    )

    assert results == []


def test_rerank_chunks_empty_query():
    chunks = [
        make_chunk(
            "chunk-1",
            "Revenue was $100 million.",
        )
    ]

    results = reranker.rerank_chunks(
        query="   ",
        chunks=chunks,
    )

    assert results == []


@pytest.mark.asyncio
async def test_retrieve_and_rerank(monkeypatch):
    session_id = uuid4()

    hybrid_chunks = [
        make_chunk(
            "chunk-1",
            "The company reported operating expenses.",
        ),
        make_chunk(
            "chunk-2",
            "The company reported revenue of $100 million.",
        ),
        make_chunk(
            "chunk-3",
            "The company reported net profit.",
        ),
    ]

    async def fake_hybrid_retrieval(
        query: str,
        session_id,
        top_k: int,
        candidate_k: int,
    ):
        assert query == "What was the company's revenue?"
        assert top_k == 20
        assert candidate_k == 20

        return hybrid_chunks

    monkeypatch.setattr(
        reranker,
        "retrieve_hybrid_chunks",
        fake_hybrid_retrieval,
    )

    monkeypatch.setattr(
        reranker,
        "get_reranker",
        lambda: FakeReranker(),
    )

    results = await reranker.retrieve_and_rerank(
        query="What was the company's revenue?",
        session_id=session_id,
        top_k=2,
        candidate_k=20,
    )

    assert len(results) == 2

    assert results[0]["id"] == "chunk-2"
    assert results[0]["reranker_score"] == 10.0
    assert results[0]["document_id"] == TEST_DOC_ID
    assert results[0]["document_filename"] == TEST_DOC_FILENAME

    assert results[1]["id"] == "chunk-3"
