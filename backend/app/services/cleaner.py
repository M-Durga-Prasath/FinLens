import re
from app.schemas.utils import ExtractedPage


def clean_single_text(text: str):
    # normalize text
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\t", " ")
    text = re.sub(r" {2,}", " ", text)
    text = re.sub(r"[ ]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    return text


def clean_text(pages: list[ExtractedPage]) -> list[ExtractedPage]:
    cleaned_pages = []
    for page in pages:
        if isinstance(page, dict):
            page_number = page["page_number"]
            text = page["text"]
        else:
            page_number = page.page_number
            text = page.text

        cleaned_pages.append(
            ExtractedPage(
                page_number=page_number,
                text=clean_single_text(text),
            )
        )
    return cleaned_pages
