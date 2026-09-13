import os
from functools import lru_cache
from uuid import UUID

from google import genai
from app.services.reranker import retrieve_and_rerank


@lru_cache(maxsize=1)
def get_gemini_client():
    return genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def build_context(chunks: list[dict]) -> str:
    context_parts = []

    for index, chunk in enumerate(chunks, start=1):
        context_parts.append(f"""
            [Source {index}]
            Document: {chunk["document_filename"]}
            Page: {chunk["page_number"]}

            Content:
            {chunk["content"]}
            """.strip()
        )

    return "\n\n".join(context_parts)


def build_sources(chunks: list[dict]) -> list[dict]:
    sources = []

    for index, chunk in enumerate(chunks, start=1):
        sources.append(
            {
                "citation_id": index,
                "chunk_id": chunk["id"],
                "document_id": chunk["document_id"],
                "document_filename": chunk["document_filename"],
                "page_number": chunk["page_number"],
            }
        )

    return sources


def build_prompt(
    query: str,
    context: str,
) -> str:
    return f"""
            You are FinLens, a financial document analysis assistant.

            Answer the user's question using ONLY the provided context.

            Rules:
            - Do not use information outside the provided context.
            - If the answer cannot be found in the context, clearly say so.
            - Cite factual statements using [1], [2], etc.
            - Only use citation numbers that exist in the provided context.
            - Do not invent citations.
            - Be clear and concise.

            Context:

            {context}

            User question:

            {query}

            Answer:
            """.strip()


def generate_with_gemini(prompt: str) -> str:
    client = get_gemini_client()

    response = client.models.generate_content(
        model=os.getenv(
            "GEMINI_MODEL",
            "gemma-4-31b-a4b-it",
        ),
        contents=prompt,
    )

    return response.text




async def generate_answer(
    query: str,
    session_id: UUID,
    top_k: int = 6,
    candidate_k: int = 20,
) -> dict:
    if not query.strip():
        return {
            "answer": "",
            "sources": [],
        }

    chunks = await retrieve_and_rerank(
        query=query,
        session_id=session_id,
        top_k=top_k,
        candidate_k=candidate_k,
    )

    if not chunks:
        return {
            "answer": (
                "I could not find relevant information " "in the uploaded documents."
            ),
            "sources": [],
        }

    context = build_context(chunks)

    prompt = build_prompt(
        query=query,
        context=context,
    )

    provider = os.getenv(
        "LLM_PROVIDER",
        "gemini",
    ).lower()

    if provider == "gemini":
        answer = generate_with_gemini(prompt)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")

    sources = build_sources(chunks)

    return {
        "answer": answer,
        "sources": sources,
    }
