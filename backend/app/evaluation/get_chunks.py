from uuid import UUID

from app.db.database import get_db


async def get_chunks(document_id: UUID) -> list[dict]:
    db = await get_db()

    rows = await db.fetch(
        """
        SELECT
            id,
            content,
            "chunkIndex",
            "pageNumber"
        FROM chunks
        WHERE "documentId" = $1
        ORDER BY "chunkIndex" ASC
        """,
        document_id,
    )

    return [
        {
            "id": row["id"],
            "content": row["content"],
            "page_number": row["pageNumber"],
            "chunk_index": row["chunkIndex"],
        }
        for row in rows
    ]