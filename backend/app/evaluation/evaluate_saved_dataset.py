import json
import os
import random
import time
from pathlib import Path

from dotenv import load_dotenv
from datasets import Dataset
from ragas import evaluate
try:
    from importlib import import_module

    _google_genai = import_module("langchain_google_genai")
    ChatGoogleGenerativeAI = _google_genai.ChatGoogleGenerativeAI
    GoogleGenerativeAIEmbeddings = _google_genai.GoogleGenerativeAIEmbeddings
except ImportError as exc:
    raise ImportError(
        "Install the Google GenAI integration with "
        "`pip install -U langchain-google-genai`."
    ) from exc
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper

load_dotenv()

INPUT_PATH = Path("app/evaluation/results/ragas_dataset.json")
OUTPUT_PATH = Path("app/evaluation/results/ragas_results.json")

FAILED_ANSWERS = {
    "Answer generation failed due to API error.",
    "No answer generated.",
}

# Build LLM and embeddings wrappers using Gemini
gemini_key = os.getenv("GEMINI_API_KEY")

ragas_llm = LangchainLLMWrapper(
    ChatGoogleGenerativeAI(
        model="gemma-4-31b-it",
        google_api_key=gemini_key,
    )
)

ragas_embeddings = LangchainEmbeddingsWrapper(
    GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=gemini_key,
    )
)

# Initialize metrics with the LLM
from ragas.metrics import (
    Faithfulness,
    AnswerRelevancy,
    ContextPrecision,
    ContextRecall,
)

METRICS_MAP = {
    "faithfulness": Faithfulness(llm=ragas_llm),
    "answer_relevancy": AnswerRelevancy(llm=ragas_llm, embeddings=ragas_embeddings),
    "context_precision": ContextPrecision(llm=ragas_llm),
    "context_recall": ContextRecall(llm=ragas_llm),
}


def load_evaluation_data() -> list[dict]:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input file not found at {INPUT_PATH}."
        )
    with open(INPUT_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def filter_failed_records(records: list[dict]) -> list[dict]:
    valid = [r for r in records if r.get("answer", "") not in FAILED_ANSWERS]
    skipped = len(records) - len(valid)
    if skipped:
        print(f"⚠ Skipped {skipped} records with failed/missing answers.")
    return valid


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


def main():
    print(f"Loading pre-generated evaluation records from: {INPUT_PATH}")
    records = load_evaluation_data()
    print(f"Total evaluation records loaded: {len(records)}")

    records = filter_failed_records(records)
    print(f"Valid records for evaluation: {len(records)}")

    if not records:
        print("No valid records to evaluate. Exiting.")
        return

    ragas_dataset = build_ragas_dataset(records)

    print("\n" + "=" * 70)
    print("RUNNING RAGAS EVALUATION ON SAVED DATASET")
    print("=" * 70 + "\n")

    combined_results = {}

    for idx, (metric_name, metric) in enumerate(METRICS_MAP.items()):
        print(f"[{idx + 1}/{len(METRICS_MAP)}] Evaluating: {metric_name}...")

        try:
            result = evaluate(
                dataset=ragas_dataset,
                metrics=[metric],
                llm=ragas_llm,
                embeddings=ragas_embeddings,
            )

            df = result.to_pandas()
            score = df.mean(numeric_only=True).to_dict()
            combined_results.update(score)

            for key, val in score.items():
                print(f"  ✓ {key:<25} {val:.4f}")

        except Exception as exc:
            print(f"  ✗ {metric_name} failed: {exc}")

        # Random sleep between metrics to avoid hitting Gemini RPM limits
        if idx < len(METRICS_MAP) - 1:
            sleep_time = random.uniform(25, 35)
            print(f"  ⏳ Sleeping {sleep_time:.0f}s to avoid rate limits...\n")
            time.sleep(sleep_time)

    print("\n" + "=" * 70)
    print("RAGAS EVALUATION METRICS SUMMARY")
    print("=" * 70)

    for metric, score in combined_results.items():
        print(f"{metric:<25} {score:.4f}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(combined_results, f, indent=2)

    print(f"\nFinal Ragas metrics saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
