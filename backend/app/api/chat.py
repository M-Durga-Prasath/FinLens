import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.db.database import get_db
from app.schemas.utils import ChatRequest
from app.services.generator import generate_answer_stream


router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post("/")
async def chat(request: ChatRequest):
    collected_tokens: list[str] = []
    collected_sources: list[dict] = []

    async def event_generator():

        async for event in generate_answer_stream(
            query=request.query,
            session_id=request.session_id,
            top_k=request.top_k,
            candidate_k=request.candidate_k,
        ):
            if event["type"] == "token":
                collected_tokens.append(event["content"])

            elif event["type"] == "sources":
                collected_sources.extend(event["sources"])

            yield f"data: {json.dumps(event)}\n\n"

    async def on_stream_complete():
        full_answer = "".join(collected_tokens)

        if not full_answer and not collected_sources:
            return

        pool = await get_db()

        async with pool.acquire() as conn:
            async with conn.transaction():
                # 1. Save user message
                await conn.execute(
                    """
                    INSERT INTO messages (id, role, content, session_id)
                    VALUES (gen_random_uuid(), 'USER', $1, $2)
                    """,
                    request.query,
                    request.session_id,
                )

                # 2. Save model message and get its id
                model_msg_id = await conn.fetchval(
                    """
                    INSERT INTO messages (id, role, content, session_id)
                    VALUES (gen_random_uuid(), 'MODEL', $1, $2)
                    RETURNING id
                    """,
                    full_answer,
                    request.session_id,
                )

                # 3. Save citations
                if collected_sources:
                    await conn.executemany(
                        """
                        INSERT INTO citations
                            (id, relevance_score, chunk_id, message_id)
                        VALUES
                            (gen_random_uuid(), $1, $2, $3)
                        """,
                        [
                            (
                                src["relevance_score"],
                                src["chunk_id"],
                                model_msg_id,
                            )
                            for src in collected_sources
                        ],
                    )

    async def streaming_with_persist():
        async for chunk in event_generator():
            yield chunk

        await on_stream_complete()

    return StreamingResponse(
        streaming_with_persist(),
        media_type="text/event-stream",
    )
