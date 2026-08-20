from uuid import UUID

from app.db.database import get_db
from app.services.embedding import get_model


async def retrieve_chunks(
    query: str,
    session_id: UUID,
    top_k: int = 5,
):
    if not query.strip():
        return []

    query_embedding = get_model().encode(query, normalize_embeddings=True)

    embedding_string = (
        "[" + ",".join(str(float(value)) for value in query_embedding) + "]"
    )

    db = await get_db()

    rows = await db.fetch(
        """
        SELECT 
            c.id, 
            c.content, 
            c."pageNumber", 
            c."chunkIndex",
            c."tokenCount",
            1 - (c.embedding <=> $1::vector) AS similarity
        FROM chunks c
        INNER JOIN documents d ON d.id = c."documentId"
        WHERE d."sessionId" = $2
            AND d."status" = 'READY'
        ORDER BY c.embedding <=> $1::vector
        LIMIT $3
        """,
        embedding_string,
        session_id,
        top_k,
    )

    return [
        {
            "id": row["id"],
            "content": row["content"],
            "page_number": row["pageNumber"],
            "chunk_index": row["chunkIndex"],
            "token_count": row["tokenCount"],
            "similarity": float(row["similarity"]),
        }
        for row in rows
    ]
