from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.schemas.utils import Chunk, EmbeddedChunk


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    return SentenceTransformer("all-MiniLM-L6-v2")


def embed_chunks(chunks:  list[Chunk]) -> list[EmbeddedChunk]:
    if not chunks:
        return []
    
    texts = [i.content for i in chunks]
    
    embeddings = get_model().encode(
        texts,
        batch_size=32,
        normalize_embeddings=True
    )
    
    embedded_chunks = []
    
    for chunk, embedding in zip(chunks, embeddings):
        embedded_chunks.append(
            EmbeddedChunk(
                content=chunk.content,
                page_number=chunk.page_number,
                token_count=chunk.token_count,
                chunk_index=chunk.chunk_index,
                embedding=embedding.tolist()
            )
        )
    
    return embedded_chunks
