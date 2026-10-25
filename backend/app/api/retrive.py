import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth.dependencies import get_current_user, verify_session_access
from app.db.database import get_db
from app.rate_limiter import limiter
from app.schemas.utils import (
    RetrievalRequest,
    RetrievalResponse,
    RetrievedChunk,
)

from app.services.reranker import retrieve_and_rerank


router = APIRouter(
    prefix="/retrieve",
    tags=["Retrieval"],
)


@router.post("/", response_model=RetrievalResponse)
@limiter.limit("30/minute")
async def retrieve(
    request: Request,
    body: RetrievalRequest,
    current_user: dict = Depends(get_current_user),
):
    await verify_session_access(body.session_id, current_user["userId"])

    results = await retrieve_and_rerank(
        query=body.query,
        session_id=body.session_id,
        top_k=body.top_k,
    )

    return RetrievalResponse(
        query=body.query,
        results=[
            RetrievedChunk(**result)
            for result in results
        ],
    )
