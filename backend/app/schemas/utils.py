from pydantic import BaseModel



class ExtractedPage(BaseModel):
    page_number: int
    text: str
class Chunk(BaseModel):
    content: str
    page_number: int
    chunk_index: int
    token_count: int

class UploadResponse(BaseModel):
    filename: str
    content_type: str
    page_count: int
    pages: list[ExtractedPage]
    chunks: list[Chunk]
