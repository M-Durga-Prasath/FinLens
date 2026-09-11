import asyncio
import json
import os
import time
from uuid import UUID

from app.services.generator import get_gemini_client
from app.evaluation.get_chunks import get_chunks


def generate_multi_chunk_qa(chunk_group: list[dict]) -> dict | None:
    client = get_gemini_client()

    formatted_chunks = []
    for idx, c in enumerate(chunk_group, start=1):
        formatted_chunks.append(
            f"--- CHUNK {idx} (ID: {c['id']}, Page: {c['page_number']}) ---\n{c['content']}"
        )

    context = "\n\n".join(formatted_chunks)

    prompt = f"""
You are generating a multi-chunk evaluation dataset for a financial document RAG system.

Below are {len(chunk_group)} document chunks.

Your task is to generate ONE question that REQUIRES combining or comparing information from AT LEAST THREE of the provided chunks to answer accurately.

Rules:
- The question MUST require facts/numbers/details from more than one chunk (e.g. comparisons, totals, trend analyses, or multi-step financial reasoning).
- The answer must be explicitly supported by the chunks provided.
- Do not require information outside these chunks.
- Return ONLY valid JSON.

Required format:

{{
    "question": "...",
    "ground_truth": "..."
}}

Chunks:

{context}
""".strip()

    try:
        response = client.models.generate_content(
            model=os.getenv(
                "GEMINI_MODEL",
                "gemini-3.5-flash-lite",
            ),
            contents=prompt,
            config={
                "response_mime_type": "application/json",
            },
        )

        data = json.loads(response.text.strip())

        if not data.get("question") or not data.get("ground_truth"):
            print(f"No usable multi-chunk QA generated for chunk group.")
            return None

        chunk_ids = [str(c["id"]) for c in chunk_group]
        page_numbers = sorted(list({c["page_number"] for c in chunk_group if c["page_number"] is not None}))

        return {
            "question": data["question"],
            "ground_truth": data["ground_truth"],
            "relevant_chunk_ids": chunk_ids,
            "page_numbers": page_numbers,
        }

    except Exception as exc:
        print(f"Failed for multi-chunk group: {exc}")
        return None


from dotenv import load_dotenv

load_dotenv()


async def main():
    document_id = UUID(
        os.getenv("EVAL_DOCUMENT_ID", "11111111-1111-1111-1111-111111111111")
    )

    chunks = await get_chunks(document_id)

    if len(chunks) < 3:
        print("Not enough chunks in document to form 3-chunk groups.")
        return

    chunk_groups = []
    max_questions = 12

    for i in range(0, len(chunks) - 2, 3):
        chunk_groups.append([chunks[i], chunks[i + 1], chunks[i + 2]])
        if len(chunk_groups) >= max_questions:
            break

    dataset = []

    for index, group in enumerate(chunk_groups, start=1):
        print(f"\nGenerating multi-chunk question {index}/{len(chunk_groups)}...")

        result = generate_multi_chunk_qa(group)

        if result:
            dataset.append(result)
            print("Multi-chunk question generated successfully.")
        else:
            print("Skipping group.")

        if index < len(chunk_groups):
            print("Waiting 5 seconds...")
            await asyncio.sleep(5)

    output_path = "app/evaluation/dataset/multi_chunk_dataset.json"

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

    print(f"\nGenerated {len(dataset)} new multi-chunk evaluation samples.")
    print(f"Total samples in multi-chunk dataset: {len(combined_dataset)}")
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
