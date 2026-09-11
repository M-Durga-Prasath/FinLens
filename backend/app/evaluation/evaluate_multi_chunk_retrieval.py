import asyncio
import json
from pathlib import Path
from uuid import UUID

from app.services.retriever import retrieve_dense_chunks
from app.services.bm25 import retrieve_bm25_chunks
from app.services.hybird_retrival import retrieve_hybrid_chunks
from app.services.reranker import retrieve_and_rerank


import os
from dotenv import load_dotenv

load_dotenv()

DATASET_PATH = Path("app/evaluation/dataset/multi_chunk_dataset.json")

SESSION_ID = UUID(
    os.getenv("EVAL_SESSION_ID", "11111111-1111-1111-1111-111111111111")
)

TOP_K = 5
CANDIDATE_K = 20


def load_dataset() -> list[dict]:
    if not DATASET_PATH.exists():
        return []
    with open(DATASET_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def calculate_multi_chunk_metrics(
    results: list[dict],
    relevant_chunk_ids: list[str],
    k: int,
) -> dict:
    relevant_ids = set(relevant_chunk_ids)
    if not relevant_ids:
        return {"partial_hit": 0, "complete_hit": 0, "recall": 0.0, "mrr": 0.0}

    retrieved_ids = [str(result["id"]) for result in results[:k]]
    retrieved_set = set(retrieved_ids)

    found_relevant = retrieved_set & relevant_ids

    partial_hit = 1 if len(found_relevant) > 0 else 0
    complete_hit = 1 if found_relevant == relevant_ids else 0
    recall = len(found_relevant) / len(relevant_ids)

    relevant_ranks = [
        rank
        for rank, chunk_id in enumerate(retrieved_ids, start=1)
        if chunk_id in relevant_ids
    ]
    mrr = 1.0 / relevant_ranks[0] if relevant_ranks else 0.0

    return {
        "partial_hit": partial_hit,
        "complete_hit": complete_hit,
        "recall": recall,
        "mrr": mrr,
    }


async def evaluate_method(
    name: str,
    dataset: list[dict],
) -> dict:
    total = len(dataset)

    partial_hit_total = 0
    complete_hit_total = 0
    recall_total = 0.0
    mrr_total = 0.0

    print(f"\n{'=' * 65}")
    print(f"Evaluating Multi-Chunk Retrieval: {name.upper()}")
    print(f"{'=' * 65}")

    for index, item in enumerate(dataset, start=1):
        query = item["question"]
        relevant_chunk_ids = item["relevant_chunk_ids"]

        if name == "dense":
            results = await retrieve_dense_chunks(
                query=query,
                session_id=SESSION_ID,
                top_k=TOP_K,
            )

        elif name == "bm25":
            results = await retrieve_bm25_chunks(
                query=query,
                session_id=SESSION_ID,
                top_k=TOP_K,
            )

        elif name == "hybrid":
            results = await retrieve_hybrid_chunks(
                query=query,
                session_id=SESSION_ID,
                top_k=TOP_K,
                candidate_k=CANDIDATE_K,
            )

        elif name == "reranker":
            results = await retrieve_and_rerank(
                query=query,
                session_id=SESSION_ID,
                top_k=TOP_K,
                candidate_k=CANDIDATE_K,
            )

        else:
            raise ValueError(f"Unknown evaluation method: {name}")

        metrics = calculate_multi_chunk_metrics(
            results=results,
            relevant_chunk_ids=relevant_chunk_ids,
            k=TOP_K,
        )

        partial_hit_total += metrics["partial_hit"]
        complete_hit_total += metrics["complete_hit"]
        recall_total += metrics["recall"]
        mrr_total += metrics["mrr"]

        status = "✓ All" if metrics["complete_hit"] else ("~ Part" if metrics["partial_hit"] else "✗ None")

        print(
            f"{index:02d}. [{status:<6}] "
            f"Recall: {metrics['recall']*100:5.1f}% | "
            f"{query[:55]}"
        )

    return {
        "partial_hit_rate": partial_hit_total / total if total else 0.0,
        "complete_hit_rate": complete_hit_total / total if total else 0.0,
        "recall": recall_total / total if total else 0.0,
        "mrr": mrr_total / total if total else 0.0,
    }


async def main():
    dataset = load_dataset()

    if not dataset:
        print(f"Dataset is empty or file not found at {DATASET_PATH}")
        return

    print(f"Loaded {len(dataset)} multi-chunk evaluation questions.")

    methods = [
        "dense",
        "bm25",
        "hybrid",
        "reranker",
    ]

    results = {}

    for method in methods:
        results[method] = await evaluate_method(
            name=method,
            dataset=dataset,
        )

    print("\n")
    print("=" * 75)
    print("FINAL MULTI-CHUNK RETRIEVAL EVALUATION")
    print("=" * 75)

    print(
        f"{'Method':<15}"
        f"{'PartialHit@5':>15}"
        f"{'CompleteHit@5':>16}"
        f"{'Recall@5':>12}"
        f"{'MRR@5':>12}"
    )

    print("-" * 75)

    for method, metrics in results.items():
        print(
            f"{method:<15}"
            f"{metrics['partial_hit_rate'] * 100:>14.1f}%"
            f"{metrics['complete_hit_rate'] * 100:>15.1f}%"
            f"{metrics['recall'] * 100:>11.1f}%"
            f"{metrics['mrr']:>12.3f}"
        )

    output_path = Path("app/evaluation/results/multi_chunk_retrieval_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(results, file, indent=2)

    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
