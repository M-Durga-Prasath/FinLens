
import json
import time
import logging
import os

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.schemas.utils import ChatRequest
from app.services.guardrails import validate_query, sanitize_chunks
from app.services.hybird_retrival import retrieve_hybrid_chunks
from app.services.reranker import rerank_chunks, hybrid_aware_select
from app.services.generator import (
    build_context,
    build_prompt,
    build_no_context_prompt,
    build_sources,
    generate_with_gemini_stream,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/benchmark",
    tags=["Benchmark"],
)


@router.post("/")
async def benchmark_chat(request: ChatRequest):

    timings: dict[str, float | None] = {
        "guardrail_ms": None,
        "retrieval_ms": None,
        "reranking_ms": None,
        "prompt_build_ms": None,
        "ttft_ms": None,          # time to first token (from Gemini request start)
        "generation_ms": None,    # full generation duration (from first token)
        "gemini_total_ms": None,  # full Gemini call (request → last token)
        "total_ms": None,         # end-to-end latency
    }
    token_count = 0

    t_start = time.perf_counter()

    async def event_generator():
        nonlocal token_count

        # ── 1. Guardrails ─────────────────────────────────────────
        t_guard_start = time.perf_counter()
        error = validate_query(request.query)
        timings["guardrail_ms"] = _elapsed_ms(t_guard_start)

        if error:
            yield _sse({"type": "error", "message": error})
            timings["total_ms"] = _elapsed_ms(t_start)
            yield _sse({"type": "timings", "timings": timings})
            return

        # ── 2. Hybrid retrieval ───────────────────────────────────
        t_retrieval_start = time.perf_counter()
        try:
            hybrid_results = await retrieve_hybrid_chunks(
                query=request.query,
                session_id=request.session_id,
                top_k=request.candidate_k,
                candidate_k=request.candidate_k,
            )
        except Exception as exc:
            logger.error("Benchmark retrieval failed: %s", exc)
            yield _sse({"type": "error", "message": "Retrieval failed."})
            timings["retrieval_ms"] = _elapsed_ms(t_retrieval_start)
            timings["total_ms"] = _elapsed_ms(t_start)
            yield _sse({"type": "timings", "timings": timings})
            return

        timings["retrieval_ms"] = _elapsed_ms(t_retrieval_start)

        # ── 2b. No documents — handle gracefully ─────────────────
        if not hybrid_results:
            prompt = build_no_context_prompt(request.query)
            t_gemini_start = time.perf_counter()
            first_token_seen = False

            try:
                for text in generate_with_gemini_stream(prompt):
                    if not first_token_seen:
                        timings["ttft_ms"] = _elapsed_ms(t_gemini_start)
                        first_token_seen = True
                        t_first_token = time.perf_counter()

                    token_count += 1
                    yield _sse({"type": "token", "content": text})
            except Exception as exc:
                logger.error("Benchmark Gemini (no-context) failed: %s", exc)
                yield _sse({"type": "error", "message": "Generation failed."})

            if first_token_seen:
                timings["generation_ms"] = _elapsed_ms(t_first_token)
            timings["gemini_total_ms"] = _elapsed_ms(t_gemini_start)
            timings["total_ms"] = _elapsed_ms(t_start)
            yield _sse({"type": "timings", "timings": timings, "token_count": token_count})
            return

        # ── 3. Reranking ──────────────────────────────────────────
        t_rerank_start = time.perf_counter()

        reranked = rerank_chunks(
            query=request.query,
            chunks=hybrid_results,
            top_k=len(hybrid_results),
        )
        anchors = hybrid_aware_select(
            candidates=reranked,
            reranker_slots=3,
            hybrid_slots=3,
        )
        chunks = anchors[:request.top_k]

        timings["reranking_ms"] = _elapsed_ms(t_rerank_start)

        # ── 3b. Sanitize ──────────────────────────────────────────
        chunks = sanitize_chunks(chunks)

        # ── 4. Prompt building ────────────────────────────────────
        t_prompt_start = time.perf_counter()
        context = build_context(chunks)
        prompt = build_prompt(query=request.query, context=context)
        timings["prompt_build_ms"] = _elapsed_ms(t_prompt_start)

        provider = os.getenv("LLM_PROVIDER", "gemini").lower()
        if provider != "gemini":
            yield _sse({"type": "error", "message": f"Unsupported provider: {provider}"})
            timings["total_ms"] = _elapsed_ms(t_start)
            yield _sse({"type": "timings", "timings": timings})
            return

        # ── 5. Gemini streaming ───────────────────────────────────
        t_gemini_start = time.perf_counter()
        first_token_seen = False
        t_first_token = None

        try:
            for text in generate_with_gemini_stream(prompt):
                if not first_token_seen:
                    timings["ttft_ms"] = _elapsed_ms(t_gemini_start)
                    first_token_seen = True
                    t_first_token = time.perf_counter()

                token_count += 1
                yield _sse({"type": "token", "content": text})
        except Exception as exc:
            logger.error("Benchmark Gemini streaming failed: %s", exc)
            yield _sse({"type": "error", "message": "Generation failed."})
            timings["gemini_total_ms"] = _elapsed_ms(t_gemini_start)
            timings["total_ms"] = _elapsed_ms(t_start)
            yield _sse({"type": "timings", "timings": timings})
            return

        if t_first_token is not None:
            timings["generation_ms"] = _elapsed_ms(t_first_token)
        timings["gemini_total_ms"] = _elapsed_ms(t_gemini_start)

        # ── 6. Sources ────────────────────────────────────────────
        yield _sse({
            "type": "sources",
            "sources": build_sources(chunks),
        })

        # ── 7. Timing summary ────────────────────────────────────
        timings["total_ms"] = _elapsed_ms(t_start)
        yield _sse({
            "type": "timings",
            "timings": timings,
            "token_count": token_count,
        })

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )


def _elapsed_ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 2)


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"
