import asyncio
from uuid import UUID
import pytest
from app.services.generator import generate_answer


@pytest.mark.asyncio
async def test_generate_answer():
    session_id = UUID("22222222-2222-2222-2222-222222222222")

    result = await generate_answer(
        query="What was the company's total revenue?",
        session_id=session_id,
        top_k=5,
        candidate_k=20,
    )

    print(result["answer"])
    assert result["answer"]