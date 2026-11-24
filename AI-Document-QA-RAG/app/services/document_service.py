from pathlib import Path
from uuid import uuid4

from docx import Document as DocxDocument
from langchain_core.documents import Document
from pypdf import PdfReader


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


def extract_documents(file_path: Path, original_name: str) -> list[Document]:
    suffix = file_path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {suffix}. Supported: PDF, DOCX, TXT, MD")

    docs: list[Document] = []
    if suffix == ".pdf":
        reader = PdfReader(str(file_path))
        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            if text.strip():
                docs.append(Document(
                    page_content=text,
                    metadata={"source": original_name, "page": page_number},
                ))
    elif suffix == ".docx":
        doc = DocxDocument(str(file_path))
        text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        if text.strip():
            docs.append(Document(page_content=text, metadata={"source": original_name}))
    else:
        text = file_path.read_text(encoding="utf-8", errors="replace")
        if text.strip():
            docs.append(Document(page_content=text, metadata={"source": original_name}))

    if not docs:
        raise ValueError("No readable text was found in the uploaded document.")
    return docs


def new_document_id() -> str:
    return str(uuid4())
