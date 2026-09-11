import asyncio
import json
import os
import time
from pathlib import Path
from uuid import UUID

from dotenv import load_dotenv
from datasets import Dataset
from ragas import evaluate
from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    GoogleGenerativeAIEmbeddings,
)
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.metrics import (
    Faithfulness,
    AnswerRelevancy,
    ContextPrecision,
    ContextRecall,
)

from app.services.reranker import retrieve_and_rerank
from app.services.generator import get_gemini_client

load_dotenv()

# Build Gemini LLM and embeddings for Ragas
_gemini_key = os.getenv("GEMINI_API_KEY")

ragas_llm = LangchainLLMWrapper(
    ChatGoogleGenerativeAI(
        model="gemma-4-31b-it",
        google_api_key=_gemini_key,
    )
)

ragas_embeddings = LangchainEmbeddingsWrapper(
    GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=_gemini_key,
    )
)

METRICS = [
    Faithfulness(llm=ragas_llm),
    AnswerRelevancy(llm=ragas_llm, embeddings=ragas_embeddings),
    ContextPrecision(llm=ragas_llm),
    ContextRecall(llm=ragas_llm),
]

SINGLE_DATASET_PATH = Path("app/evaluation/dataset/dataset.json")
MULTI_DATASET_PATH = Path("app/evaluation/dataset/multi_chunk_dataset.json")

RECORD_OUTPUT_PATH = Path("app/evaluation/results/ragas_dataset.json")
METRIC_OUTPUT_PATH = Path("app/evaluation/results/ragas_results.json")

SESSION_ID = UUID(
    os.getenv("EVAL_SESSION_ID", "11111111-1111-1111-1111-111111111111")
)

TOP_K = 5
CANDIDATE_K = 20
DELAY_SECONDS = 3.5


def load_combined_datasets() -> list[dict]:
    combined = []
    for path in [SINGLE_DATASET_PATH, MULTI_DATASET_PATH]:
        if path.exists():
            with open(path, "r", encoding="utf-8") as file:
                combined.extend(json.load(file))
    return combined


def build_context(chunks: list[dict]) -> str:
    return "\n\n".join(chunk["content"] for chunk in chunks)


def build_prompt(question: str, context: str) -> str:
    return f"""
You are FinLens, a financial document analysis assistant.

Answer the question using ONLY the provided context.

Rules:
- Do not use information outside the context.
- If the answer cannot be determined from the context, say so clearly.
- Be concise and precise with financial facts.
- Do not invent information.

Context:

{context}

Question:

{question}

Answer:
""".strip()


MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 5


def generate_answer(question: str, context: str) -> str:
    client = get_gemini_client()

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=os.getenv("GEMINI_MODEL", "gemma-4-31b-it"),
                contents=build_prompt(question, context),
            )
            return response.text.strip()
        except Exception as exc:
            if attempt == MAX_RETRIES:
                raise
            wait = INITIAL_RETRY_DELAY * (2 ** (attempt - 1))
            print(f"  ⟳ Attempt {attempt} failed ({exc}), retrying in {wait}s...")
            time.sleep(wait)


def build_ragas_dataset(records: list[dict]) -> Dataset:
    data = {
        "question": [],
        "answer": [],
        "contexts": [],
        "ground_truth": [],
    }

    for record in records:
        data["question"].append(record["question"])
        data["answer"].append(record["answer"])
        data["contexts"].append(record["contexts"])
        data["ground_truth"].append(record["ground_truth"])

    return Dataset.from_dict(data)


async def main():
    dataset_items = load_combined_datasets()

    print(f"\nTotal combined evaluation items: {len(dataset_items)}")
    print(f"{'=' * 70}\n")

    records = []
    failed_count = 0

    for index, item in enumerate(dataset_items, start=1):
        question = item["question"]
        print(f"[{index}/{len(dataset_items)}] Generating answer for: {question[:65]}...")

        try:
            chunks = await retrieve_and_rerank(
                query=question,
                session_id=SESSION_ID,
                top_k=TOP_K,
                candidate_k=CANDIDATE_K,
            )

            if not chunks:
                print("  ✗ No chunks retrieved.")
                contexts = []
                answer = "I could not find relevant information in the documents."
            else:
                contexts = [chunk["content"] for chunk in chunks]
                context_str = build_context(chunks)
                answer = generate_answer(question=question, context=context_str)
                print("  ✓ Answer generated.")

        except Exception as exc:
            print(f"  ✗ Failed after {MAX_RETRIES} retries: {exc}")
            contexts = []
            answer = "Answer generation failed due to API error."
            failed_count += 1

        record = {
            "question": question,
            "ground_truth": item["ground_truth"],
            "contexts": contexts if contexts else [""],
            "answer": answer if answer else "No answer generated.",
            "relevant_chunk_ids": item.get("relevant_chunk_ids", []),
        }
        records.append(record)

        # Save progress incrementally
        RECORD_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(RECORD_OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)

        if index < len(dataset_items):
            time.sleep(DELAY_SECONDS)

    print(f"\n✓ {len(records) - failed_count}/{len(records)} answers generated successfully.")
    if failed_count:
        print(f"✗ {failed_count} items failed and have fallback answers.")

    print("\n" + "=" * 70)
    print("RUNNING RAGAS EVALUATION")
    print("=" * 70 + "\n")

    ragas_dataset = build_ragas_dataset(records)

    try:
        results = evaluate(
            dataset=ragas_dataset,
            metrics=METRICS,
            llm=ragas_llm,
            embeddings=ragas_embeddings,
        )

        print("\n" + "=" * 70)
        print("RAGAS EVALUATION METRICS SUMMARY")
        print("=" * 70)

        result_dict = results.to_pandas().mean(numeric_only=True).to_dict()

        for metric, score in result_dict.items():
            print(f"{metric:<25} {score:.4f}")

        METRIC_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(METRIC_OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(result_dict, f, indent=2)

        print(f"\nFinal Ragas metrics saved to: {METRIC_OUTPUT_PATH}")

    except Exception as exc:
        print(f"Ragas evaluation failed: {exc}")
        print(f"Generated RAG records remain safely saved at: {RECORD_OUTPUT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
