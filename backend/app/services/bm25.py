from __future__ import annotations

import math
import re
from collections import Counter
from typing import Iterable
from uuid import UUID

TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+")

get_db = None


def tokenize_text(text: str) -> list[str]:
    if not text:
        return []

    return TOKEN_PATTERN.findall(text.lower())


class BM25Index:
    def __init__(self, corpus: Iterable[Iterable[str]], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus = [list(doc) for doc in corpus]
        self.doc_count = len(self.corpus)
        self.doc_lengths = [len(doc) for doc in self.corpus]
        self.avg_doc_length = (
            sum(self.doc_lengths) / self.doc_count if self.doc_count else 0.0
        )
        self.term_frequencies = [Counter(doc) for doc in self.corpus]
        self.document_frequencies = Counter()

        for doc in self.corpus:
            self.document_frequencies.update(set(doc))

        self.idf = {
            term: math.log(1.0 + (self.doc_count - freq + 0.5) / (freq + 0.5))
            for term, freq in self.document_frequencies.items()
        }

    def score(self, query_tokens: Iterable[str]) -> list[float]:
        query_terms = list(query_tokens)
        if not query_terms or self.doc_count == 0:
            return [0.0] * self.doc_count

        scores = [0.0] * self.doc_count

        for term in query_terms:
            idf = self.idf.get(term)
            if idf is None:
                continue

            for idx, term_freqs in enumerate(self.term_frequencies):
                freq = term_freqs.get(term, 0)
                if freq == 0:
                    continue

                doc_length = self.doc_lengths[idx]
                norm = freq + self.k1 * (
                    1.0 - self.b + self.b * doc_length / self.avg_doc_length
                )
                scores[idx] += idf * (freq * (self.k1 + 1.0)) / norm

        return scores


def rank_chunks_by_bm25(
    query: str,
    chunks: list[dict],
    top_k: int = 5,
) -> list[dict]:
    if not query.strip() or not chunks:
        return []

    tokenized_corpus = [tokenize_text(chunk.get("content", "")) for chunk in chunks]
    index = BM25Index(tokenized_corpus)
    scores = index.score(tokenize_text(query))

    ranked = sorted(
        enumerate(zip(chunks, scores)),
        key=lambda item: (-item[1][1], item[0]),
    )[:top_k]

    results = []
    for _, (chunk, score) in ranked:
        results.append(
            {
                "id": chunk["id"],
                "content": chunk["content"],
                "page_number": chunk.get("page_number"),
                "chunk_index": chunk["chunk_index"],
                "token_count": chunk["token_count"],
                "similarity": float(score),
            }
        )

    return results


async def retrieve_chunks(
    query: str,
    session_id: UUID,
    top_k: int = 5,
) -> list[dict]:
    if not query.strip():
        return []

    db_getter = get_db
    if db_getter is None:
        from app.db.database import get_db as db_getter  # local import for testability

    db = await db_getter()
    rows = await db.fetch(
        """
        SELECT
            c.id,
            c.content,
            c."pageNumber",
            c."chunkIndex",
            c."tokenCount"
        FROM chunks c
        INNER JOIN documents d ON d.id = c."documentId"
        WHERE d."sessionId" = $1
            AND d."status" = 'READY'
        ORDER BY c."chunkIndex" ASC
        """,
        session_id,
    )

    chunks = [
        {
            "id": row["id"],
            "content": row["content"],
            "page_number": row["pageNumber"],
            "chunk_index": row["chunkIndex"],
            "token_count": row["tokenCount"],
        }
        for row in rows
    ]

    return rank_chunks_by_bm25(query=query, chunks=chunks, top_k=top_k)
