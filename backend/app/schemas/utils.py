from pydantic import BaseModel, Field
from uuid import UUID


class ExtractedPage(BaseModel):
    page_number: int
    text: str
class Chunk(BaseModel):
    content: str
    page_number: int
    chunk_index: int
    token_count: int
class EmbeddedChunk(BaseModel):
    content: str
    page_number: int
    chunk_index: int
    token_count: int
    embedding: list[float]

class UploadResponse(BaseModel):
    document_id: UUID
    filename: str
    content_type: str
    page_count: int
    pages: list[ExtractedPage] | None = None
    # embedded_chunks: list[EmbeddedChunk]
    status: str
   
class RetrievalRequest(BaseModel):
    query: str
    session_id: UUID
    top_k: int = Field(default=6, ge=3, le=10)
    
class RetrievedChunk(BaseModel):
    id: UUID
    content: str
    document_id: UUID
    document_filename: str
    page_number: int | None
    chunk_index: int
    token_count: int | None
    similarity: float
    rrf_score: float | None = None
    reranker_score: float | None = None

class RetrievalResponse(BaseModel):
    query: str
    results: list[RetrievedChunk]

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1)
    session_id: UUID
    top_k: int = Field(default=6, ge=3, le=10)
    candidate_k: int = Field(default=20, ge=10, le=30)
