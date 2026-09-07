from functools import lru_cache
from uuid import UUID

from sentence_transformers import CrossEncoder

from app.services.hybird_retrival import retrieve_hybrid_chunks


@lru_cache(maxsize=1)
def get_reranker() -> CrossEncoder:
    return CrossEncoder(
        "cross-encoder/ms-marco-MiniLM-L-6-v2"
    )


def rerank_chunks(
    query: str,
    chunks: list[dict],
    top_k: int = 5,
) -> list[dict]:
    if not query.strip() or not chunks:
        return []

    pairs = [
        (query, chunk["content"])
        for chunk in chunks
    ]

    scores = get_reranker().predict(pairs)

    ranked_results = sorted(
        zip(chunks, scores),
        key=lambda item: float(item[1]),
        reverse=True,
    )

    results = []

    for chunk, score in ranked_results[:top_k]:
        reranked_chunk = chunk.copy()

        reranked_chunk["reranker_score"] = float(score)
        reranked_chunk["similarity"] = float(score)

        results.append(reranked_chunk)

    return results


async def retrieve_and_rerank(
    query: str,
    session_id: UUID,
    top_k: int = 5,
    candidate_k: int = 20,
) -> list[dict]:
    if not query.strip():
        return []

    hybrid_results = await retrieve_hybrid_chunks(
        query=query,
        session_id=session_id,
        top_k=candidate_k,
        candidate_k=candidate_k,
    )

    return rerank_chunks(
        query=query,
        chunks=hybrid_results,
        top_k=top_k,
    )