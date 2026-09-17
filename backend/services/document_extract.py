from __future__ import annotations

import io
import zipfile
from html import unescape
from pathlib import Path
from xml.etree import ElementTree


TEXT_EXTENSIONS = {".txt", ".md", ".markdown"}
PDF_EXTENSIONS = {".pdf"}
DOCX_EXTENSIONS = {".docx"}


def extract_document_text(filename: str, content: bytes, content_type: str = "") -> str:
    suffix = Path(filename or "").suffix.lower()
    normalized_type = (content_type or "").lower()

    if suffix in TEXT_EXTENSIONS or normalized_type.startswith("text/"):
        return decode_text(content)

    if suffix in PDF_EXTENSIONS or normalized_type == "application/pdf":
        return extract_pdf_text(content)

    if suffix in DOCX_EXTENSIONS or normalized_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return extract_docx_text(content)

    raise ValueError("Unsupported file type. Upload a PDF, DOCX, TXT, or Markdown file.")


def decode_text(content: bytes) -> str:
    for encoding in ("utf-8", "utf-16", "latin-1"):
        try:
            return content.decode(encoding).strip()
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="ignore").strip()


def extract_pdf_text(content: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("PDF extraction requires the pypdf package.") from exc

    reader = PdfReader(io.BytesIO(content))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(page.strip() for page in pages if page.strip()).strip()


def extract_docx_text(content: bytes) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            document_xml = archive.read("word/document.xml")
    except (KeyError, zipfile.BadZipFile) as exc:
        raise ValueError("Could not read DOCX content from the uploaded file.") from exc

    root = ElementTree.fromstring(document_xml)
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs = []

    for paragraph in root.findall(".//w:p", namespace):
        parts = [node.text or "" for node in paragraph.findall(".//w:t", namespace)]
        text = unescape("".join(parts)).strip()
        if text:
            paragraphs.append(text)

    return "\n".join(paragraphs).strip()
