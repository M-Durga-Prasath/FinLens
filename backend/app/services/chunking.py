from langchain_text_splitters import RecursiveCharacterTextSplitter
import tiktoken
from app.schemas.utils import Chunk, ExtractedPage

chunk_size = 500
chunk_overlap = 50

Encoding = tiktoken.get_encoding("cl100k_base")

splitter = RecursiveCharacterTextSplitter(
    chunk_size = chunk_size,
    chunk_overlap = chunk_overlap
)

def chunk_text(pages: list[ExtractedPage]) -> list[Chunk]:
    chunks = []
    chunk_index = 1
    
    for page in pages:
        if not page:
            continue
        
        page_chunks = splitter.split_text(page.text)

        for chunk in page_chunks:
            token_count = len(Encoding.encode(chunk))

            chunks.append(
                Chunk(
                    content=chunk,
                    page_number=page.page_number,
                    chunk_index=chunk_index,
                    token_count=token_count,
                )
            )
        
            chunk_index += 1

    return chunks
    
