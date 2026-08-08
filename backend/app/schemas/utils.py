from pydantic import BaseModel



class ExtractedPage(BaseModel):
    page_number: int
    text: str


class UploadResponse(BaseModel):
    filename: str
    content_type: str
    page_count: int
    pages: list[ExtractedPage]

