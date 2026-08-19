from fastapi import APIRouter

from app.schemas.utils import (
    RetrievalRequest,
    RetrievalResponse,
    RetrievedChunk,
)
from app.services.retriever import retrieve_chunks


router = APIRouter(
    prefix="/retrieve",
    tags=["Retrieval"],
)


@router.post("/", response_model=RetrievalResponse)
async def retrieve(request: RetrievalRequest):

    results = await retrieve_chunks(
        query=request.query,
        document_id=request.document_id,
        top_k=request.top_k,
    )

    return RetrievalResponse(
        query=request.query,
        results=[
            RetrievedChunk(**result)
            for result in results
        ],
    )