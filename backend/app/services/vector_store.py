from uuid import UUID

from app.db.database import get_db
from app.schemas.utils import EmbeddedChunk


def vector_to_pgvector(vector: list[float]):

    # Convert a Python list of floats into PostgreSQL pgvector format.

    return "[" + ",".join(str(float(value)) for value in vector) + "]"


async def create_document(
    filename: str,
    filetype: str,
    user_id: UUID,
    session_id: UUID,
):
    db = await get_db
    document_id = await db.fetchval(
        """
        INSERT INTO documents (
            filename,
            filetype,
            status,
            "userId",
            "sessionId"
        )
        VALUES (
            $1,
            $2,
            'PROCESSING',
            $3,
            $4
        )
        RETURNING id
        """,
        filename,
        filetype,
        user_id,
        session_id,
    )

    return document_id


async def store_chunks(
    document_id: UUID,
    chunks: list[EmbeddedChunk],
):
    if not chunks:
        return

    db = await get_db()

    async with db.acquire() as connection:

        async with connection.transaction():

            for chunk in chunks:

                embedding = vector_to_pgvector(chunk.embedding)

                await connection.execute(
                    """
                    INSERT INTO chunks (
                        content,
                        "chunkIndex",
                        "pageNumber",
                        "tokenCount",
                        embedding,
                        "documentId"
                    )
                    VALUES (
                        $1,
                        $2,
                        $3,
                        $4,
                        $5::vector,
                        $6
                    )
                    """,
                    chunk.content,
                    chunk.chunk_index,
                    chunk.page_number,
                    chunk.token_count,
                    embedding,
                    document_id,
                )


async def update_document_status(
    document_id: UUID,
    status: str,
):
    db = await get_db()

    await db.execute(
        """
        UPDATE documents
        SET status = $1::"DocStatus"
        WHERE id = $2
        """,
        status,
        document_id,
    )



async def store_document(
    filename: str,
    filetype: str,
    user_id: UUID,
    session_id: UUID,
    chunks: list[EmbeddedChunk]  
):
    document_id = await create_document(
        filename=filename,
        filetype=filetype,
        user_id=user_id,
        session_id=session_id
    )

    try:
        await store_chunks(
            document_id=document_id,
            chunks=chunks,
        )
        
        await update_document_status(
            document_id=document_id,
            status="READY"
        )
        return document_id
        
    except Exception:
        
        await update_document_status(
            document_id=document_id,
            status="FAILED"
        )
        
        raise