from pathlib import Path

import pytest

from app.services.cleaner import clean_text
from app.services.extractor import extract_text


DATA_DIR = Path(__file__).resolve().parents[2] / "data"

DATA_FILES = [
    ("amazon.pdf", "application/pdf"),
    ("Apple10k.pdf", "application/pdf"),
    ("MIcrosoft.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    ("NVIDIA.pdf", "application/pdf"),
    ("tesla.pdf", "application/pdf"),
]


@pytest.mark.parametrize("filename, content_type", DATA_FILES)
def test_extract_and_clean_real_data_file(filename, content_type):
    path = DATA_DIR / filename

    assert path.exists(), f"Missing data file: {path}"

    raw_bytes = path.read_bytes()
    extracted_pages = extract_text(raw_bytes, content_type)
    cleaned_pages = clean_text(extracted_pages)

    assert len(cleaned_pages) > 0
    assert cleaned_pages[0].page_number == 1
    assert any(page.text.strip() for page in cleaned_pages)
    assert all(page.page_number >= 1 for page in cleaned_pages)
