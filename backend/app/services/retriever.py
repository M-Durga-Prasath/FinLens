from uuid import UUID

from app.db.database import get_db
from app.services.embedding import get_model


async def retrieve_chunks(
    query: str,
    document_id: UUID,
    top_k: 5,
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
            id, 
            content, 
            "pageNumber", 
            "chunkIndex",
            "tokenCount",
            1-(embedding <=> $1::vector) AS similarity
        FROM chunks
        WHERE "documentId" = $2
        ORDER BY embedding <=> $1::vector
        LIMIT $3
        """,
        embedding_string,
        document_id,
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