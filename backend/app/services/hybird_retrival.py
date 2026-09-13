from collections import defaultdict
from uuid import UUID

from app.services.retriever import retrieve_dense_chunks
from app.services.bm25 import retrieve_bm25_chunks


def reciprocal_rank_fusion(
    result_sets: list[list[dict]],
    rrf_k: int = 60,
) -> list[dict]:
    scores = defaultdict(float)
    chunks_by_id = {}

    for results in result_sets:
        for rank, chunk in enumerate(results, start=1):
            chunk_id = chunk["id"]

            scores[chunk_id] += 1.0 / (rrf_k + rank)

            if chunk_id not in chunks_by_id:
                chunks_by_id[chunk_id] = chunk

    ranked_ids = sorted(
        scores,
        key=lambda chunk_id: scores[chunk_id],
        reverse=True,
    )

    results = []

    for chunk_id in ranked_ids:
        chunk = chunks_by_id[chunk_id].copy()
        rrf_score = scores[chunk_id]

        chunk["rrf_score"] = rrf_score
        chunk["similarity"] = rrf_score

        results.append(chunk)

    return results


Rrf = reciprocal_rank_fusion


async def retrieve_hybrid_chunks(
    query: str,
    session_id: UUID,
    top_k: int = 5,
    candidate_k: int = 20,
) -> list[dict]:

    dense_results = await retrieve_dense_chunks(
        query=query,
        session_id=session_id,
        top_k=candidate_k,
    )

    bm25_results = await retrieve_bm25_chunks(
        query=query,
        session_id=session_id,
        top_k=candidate_k,
    )

    bm25_results = [chunk for chunk in bm25_results if chunk["similarity"] > 0]

    fused_results = reciprocal_rank_fusion(
        [dense_results, bm25_results],
    )

    return fused_results[:candidate_k]
