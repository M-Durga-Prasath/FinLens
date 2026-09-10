import asyncio
import json
from pathlib import Path
from uuid import UUID

from app.services.retriever import retrieve_dense_chunks
from app.services.bm25 import retrieve_bm25_chunks
from app.services.hybird_retrival import retrieve_hybrid_chunks
from app.services.reranker import retrieve_and_rerank


DATASET_PATH = Path("app/evaluation/dataset/dataset.json")

SESSION_ID = UUID(
    "11111111-1111-1111-1111-111111111111"
)

TOP_K = 5
CANDIDATE_K = 20


def load_dataset() -> list[dict]:
    with open(DATASET_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def calculate_metrics(
    results: list[dict],
    relevant_chunk_ids: list[str],
    k: int,
) -> dict:
    relevant_ids = set(relevant_chunk_ids)

    retrieved_ids = [
        str(result["id"])
        for result in results[:k]
    ]

    relevant_ranks = [
        rank
        for rank, chunk_id in enumerate(retrieved_ids, start=1)
        if chunk_id in relevant_ids
    ]

    hit = 1 if relevant_ranks else 0

    recall = (
        len(set(retrieved_ids) & relevant_ids)
        / len(relevant_ids)
        if relevant_ids
        else 0.0
    )

    mrr = (
        1.0 / relevant_ranks[0]
        if relevant_ranks
        else 0.0
    )

    return {
        "hit": hit,
        "recall": recall,
        "mrr": mrr,
    }


async def evaluate_method(
    name: str,
    dataset: list[dict],
) -> dict:
    total = len(dataset)

    hit_total = 0
    recall_total = 0.0
    mrr_total = 0.0

    print(f"\n{'=' * 60}")
    print(f"Evaluating: {name}")
    print(f"{'=' * 60}")

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

        metrics = calculate_metrics(
            results=results,
            relevant_chunk_ids=relevant_chunk_ids,
            k=TOP_K,
        )

        hit_total += metrics["hit"]
        recall_total += metrics["recall"]
        mrr_total += metrics["mrr"]

        status = "✓" if metrics["hit"] else "✗"

        print(
            f"{index:02d}. {status} "
            f"{query[:70]}"
        )

    return {
        "hit_rate": hit_total / total if total else 0.0,
        "recall": recall_total / total if total else 0.0,
        "mrr": mrr_total / total if total else 0.0,
    }


async def main():
    dataset = load_dataset()

    if not dataset:
        print("Dataset is empty.")
        return

    print(f"Loaded {len(dataset)} evaluation questions.")

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
    print("=" * 70)
    print("FINAL RETRIEVAL EVALUATION")
    print("=" * 70)

    print(
        f"{'Method':<15}"
        f"{'Hit@5':>12}"
        f"{'Recall@5':>12}"
        f"{'MRR@5':>12}"
    )

    print("-" * 70)

    for method, metrics in results.items():
        print(
            f"{method:<15}"
            f"{metrics['hit_rate'] * 100:>11.1f}%"
            f"{metrics['recall'] * 100:>11.1f}%"
            f"{metrics['mrr']:>12.3f}"
        )

    output_path = Path(
        "app/evaluation/results/retrieval_results.json"
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            results,
            file,
            indent=2,
        )

    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())