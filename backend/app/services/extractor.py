from io import BytesIO

from bs4 import BeautifulSoup
from docx import Document
import fitz


class ExtractionError(ValueError):
    pass


# extract texts form teh pdf and returns list of text and pg_no
def extract_text(docs: bytes, content_type:str):

    if not docs:
        raise ExtractionError("Document is empty")

    normalized_content_type = content_type.split(";", 1)[0].strip().lower() if content_type else ""

    # ---------- PDF ----------
    if normalized_content_type == "application/pdf":
        return extract_pdf(docs)

    # ---------- DOCX ----------
    elif normalized_content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return extract_docx(docs)

    # ---------- HTML ----------
    elif normalized_content_type == "text/html":
        return extract_html(docs)

    # ---------- TXT ----------
    elif normalized_content_type == "text/plain":
        return extract_txt(docs)

    raise ExtractionError(f"Unsupported file type: {content_type}")

def extract_html(docs):
    html = docs.decode("utf-8", errors="ignore")
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(separator="\n")

    return [
        {
            "page_number": 1,
            "text": text.strip(),
        }
    ]

def extract_txt(docs):
    text = docs.decode("utf-8", errors="ignore")

    return [
        {
            "page_number": 1,
            "text": text.strip(),
        }
    ]


def extract_docx(docs):
    document = Document(BytesIO(docs))

    paragraphs = []

    for para in document.paragraphs:

        text = para.text.strip()

        if text:
            paragraphs.append(text)

    return [
        {
            "page_number": 1,
            "text": "\n".join(paragraphs),
        }
    ]


def extract_pdf(docs):
    document = fitz.open(stream=docs, filetype="pdf")

    pages = []

    for page_number, page in enumerate(document, start=1):
        text = page.get_text()

        pages.append(
            {
                "page_number": page_number,
                "text": text.strip()
            }
        )

    document.close()

    return pages
