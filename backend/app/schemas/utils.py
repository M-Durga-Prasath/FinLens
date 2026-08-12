from pydantic import BaseModel



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
    filename: str
    content_type: str
    page_count: int
    pages: list[ExtractedPage]
    # embedded_chunks: list[EmbeddedChunk]
    status: str
   
    