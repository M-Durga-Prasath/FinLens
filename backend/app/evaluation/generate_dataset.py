import asyncio
import json
import os
import time
from uuid import UUID

from app.services.generator import get_gemini_client
from app.evaluation.get_chunks import get_chunks


def generate_qa(chunk: dict) -> dict | None:
    client = get_gemini_client()

    prompt = f"""
You are generating an evaluation dataset for a financial document RAG system.

Generate ONE question that can be answered using ONLY the document chunk below.

Rules:
- The answer must be explicitly supported by the chunk.
- Prefer useful financial questions involving facts, numbers,
  comparisons, or business information.
- Do not require information outside the chunk.
- Return ONLY valid JSON.

Required format:

{{
    "question": "...",
    "ground_truth": "..."
}}

Chunk:

{chunk["content"]}
""".strip()

    try:
        response = client.models.generate_content(
            model=os.getenv(
                "GEMINI_MODEL",
                "gemini-3.5-flash-lite",
                # "gemma-4-26b-a4b-it",
            ),
            contents=prompt,
            config={
                "response_mime_type": "application/json",
            },
        )

        data = json.loads(response.text.strip())

        if not data.get("question") or not data.get("ground_truth"):
            print(f"No usable answer generated for chunk {chunk['id']}")
            return None

        return {
            "question": data["question"],
            "ground_truth": data["ground_truth"],
            "relevant_chunk_ids": [str(chunk["id"])],
            "page_number": chunk["page_number"],
        }

    except Exception as exc:
        print(f"Failed for chunk {chunk['id']}: {exc}")
        return None


async def main():
    document_id = UUID(
        "11111111-1111-1111-1111-111111111111"
    )

    chunks = await get_chunks(document_id)

    chunks = chunks[15:]

    dataset = []

    for index, chunk in enumerate(chunks, start=1):
        print(f"\nGenerating question {index}/{len(chunks)}...")

        result = generate_qa(chunk)

        if result:
            dataset.append(result)
            print("Question generated successfully.")
        else:
            print("Skipping chunk.")

        if index < len(chunks):
            print("Waiting 5 seconds...")
            await asyncio.sleep(5)

    output_path = "app/evaluation/dataset/dataset.json"

    os.makedirs(
        "app/evaluation/dataset",
        exist_ok=True,
    )

    existing_dataset = []
    if os.path.exists(output_path):
        try:
            with open(output_path, "r", encoding="utf-8") as file:
                existing_dataset = json.load(file)
                if not isinstance(existing_dataset, list):
                    existing_dataset = []
        except Exception:
            existing_dataset = []

    combined_dataset = existing_dataset + dataset

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            combined_dataset,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print(f"\nGenerated {len(dataset)} new evaluation samples.")
    print(f"Total samples in dataset: {len(combined_dataset)}")
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())