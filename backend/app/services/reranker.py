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
    top_k: int = 6,
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


def hybrid_aware_select(
    candidates: list[dict],
    reranker_slots: int = 3,
    hybrid_slots: int = 3,
) -> list[dict]:
    if not candidates:
        return []

    selected_ids = set()
    anchors = []

    # --- precision picks (cross-encoder) ---
    by_reranker = sorted(
        candidates,
        key=lambda c: c.get("reranker_score", 0),
        reverse=True,
    )

    for chunk in by_reranker:
        if len(anchors) < reranker_slots and chunk["id"] not in selected_ids:
            anchors.append(chunk)
            selected_ids.add(chunk["id"])

    # --- coverage picks (RRF / hybrid rank) ---
    by_rrf = sorted(
        candidates,
        key=lambda c: c.get("rrf_score", 0),
        reverse=True,
    )

    hybrid_picked = 0
    for chunk in by_rrf:
        if hybrid_picked < hybrid_slots  and chunk["id"] not in selected_ids:
            anchors.append(chunk)
            selected_ids.add(chunk["id"])
            hybrid_picked += 1

    return anchors


async def retrieve_and_rerank(
    query: str,
    session_id: UUID,
    top_k: int = 6,
    candidate_k: int = 20,
    reranker_slots: int = 3,
    hybrid_slots: int = 3,
) -> list[dict]:
    if not query.strip():
        return []

    # 1. Get hybrid candidates (RRF-fused dense + BM25)
    hybrid_results = await retrieve_hybrid_chunks(
        query=query,
        session_id=session_id,
        top_k=candidate_k,
        candidate_k=candidate_k,
    )

    # 2. Score ALL candidates with cross-encoder
    reranked = rerank_chunks(
        query=query,
        chunks=hybrid_results,
        top_k=len(hybrid_results),
    )

    # 3. Hybrid-aware selection: reranker precision + hybrid coverage
    anchors = hybrid_aware_select(
        candidates=reranked,
        reranker_slots=reranker_slots,
        hybrid_slots=hybrid_slots,
    )

    return anchors[:top_k]