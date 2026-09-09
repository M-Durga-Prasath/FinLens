from fastapi import APIRouter

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
async def retrieve(request: RetrievalRequest):

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
