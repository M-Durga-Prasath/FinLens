from pathlib import Path

from app.schemas.utils import ExtractedPage
from app.services.cleaner import clean_text
from app.services.extractor import extract_text
from app.services.chunking import chunk_text


def test_chunk_text():
    pages = [
        ExtractedPage(
            page_number=1,
            text="Revenue increased significantly during the nais year. " * 100,
        )
    ]
    
    chunks = chunk_text(pages)
    
    assert len(chunks) > 1
    
    for i in chunks:
        assert i.content
        assert i.token_count > 0
    
    assert chunks[0].chunk_index == 1


def test_chunk_text_from_data_file_prints_output():
    data_file = Path(__file__).resolve().parents[2] / "data" / "Apple10k.pdf"

    assert data_file.exists(), f"Missing data file: {data_file}"

    extracted_pages = extract_text(data_file.read_bytes(), "application/pdf")
    cleaned_pages = clean_text(extracted_pages)
    chunks = chunk_text(cleaned_pages)

    print(f"file: {data_file.name}")
    print(f"pages: {len(cleaned_pages)}")
    print(f"chunks: {len(chunks)}")

    def safe_text(value: str) -> str:
        return value.encode("ascii", errors="backslashreplace").decode("ascii")

    print("chunks:")
    for chunk in chunks[:10]:
        print(
            f"page={chunk.page_number} chunk={chunk.chunk_index} "
            f"tokens={chunk.token_count} text={safe_text(chunk.content[:200])!r}"
        )

    assert len(chunks) > 0
    
    
