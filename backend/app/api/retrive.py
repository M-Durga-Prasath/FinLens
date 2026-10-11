import logging
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user, verify_session_access
from app.db.database import get_db
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
async def retrieve(
    request: RetrievalRequest,
    current_user: dict = Depends(get_current_user),
):
    await verify_session_access(request.session_id, current_user["userId"])

    results = await retrieve_and_rerank(
        query=request.query,
        session_id=request.session_id,
        top_k=request.top_k,
    )

    return RetrievalResponse(
        query=request.query,
        results=[
            RetrievedChunk(**result)
            for result in results
        ],
    )
