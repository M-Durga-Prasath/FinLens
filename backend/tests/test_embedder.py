from app.services.embedding import embed_chunks
from app.schemas.utils import Chunk

def text_embed_chunks():
    chunks = [
        Chunk(
            content="Revenue increased by 18 percent.",
            page_number=1,
            chunk_index=0,
            token_count=7,
        ),
        Chunk(
            content="Operating expenses increased by 5 percent.",
            page_number=1,
            chunk_index=1,
            token_count=8,
        ),
    ]
    
    chunks_res = embed_chunks(chunks)
    
    assert len(chunks_res) == 2
    
    for i in chunks_res:
        assert len(i.embedding) == 384
        print(i)
    
    