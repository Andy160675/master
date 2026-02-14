"""
Sovereign Evidence Analyser — Document Parser
Extracts text from PDF, DOCX, TXT, MD files. 100% local.
"""
import hashlib
from pathlib import Path
from typing import Optional

from ..config import DOCUMENT_EXTENSIONS


def parse_document(file_path: str) -> Optional[dict]:
    """Parse a document and return structured data with extracted text."""
    path = Path(file_path)
    if not path.exists():
        print(f"[DocParser] File not found: {file_path}")
        return None

    ext = path.suffix.lower()
    if ext not in DOCUMENT_EXTENSIONS:
        return None

    try:
        content = ""
        metadata = {}

        if ext == ".pdf":
            content, metadata = _parse_pdf(path)
        elif ext in (".docx", ".doc"):
            content, metadata = _parse_docx(path)
        elif ext in (".txt", ".md"):
            content, metadata = _parse_text(path)

        file_hash = _hash_file(path)

        return {
            "file_path": str(path.resolve()),
            "file_name": path.name,
            "file_type": ext,
            "source_dir": str(path.parent),
            "file_size": path.stat().st_size,
            "file_hash": file_hash,
            "content_text": content,
            "metadata": metadata,
        }
    except Exception as e:
        print(f"[DocParser] Error parsing {file_path}: {e}")
        return None


def _parse_pdf(path: Path) -> tuple[str, dict]:
    """Extract text from PDF using pdfplumber (better tables) or PyPDF2 fallback."""
    text = ""
    metadata = {}

    try:
        import pdfplumber
        with pdfplumber.open(str(path)) as pdf:
            metadata["pages"] = len(pdf.pages)
            pages_text = []
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    pages_text.append(page_text)
            text = "\n\n".join(pages_text)
    except ImportError:
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(str(path))
            metadata["pages"] = len(reader.pages)
            pages_text = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    pages_text.append(page_text)
            text = "\n\n".join(pages_text)
        except ImportError:
            print("[DocParser] No PDF library available. Install pdfplumber or PyPDF2.")

    return text, metadata


def _parse_docx(path: Path) -> tuple[str, dict]:
    """Extract text from DOCX."""
    metadata = {}
    try:
        from docx import Document
        doc = Document(str(path))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        metadata["paragraphs"] = len(paragraphs)
        return "\n\n".join(paragraphs), metadata
    except ImportError:
        print("[DocParser] python-docx not installed.")
        return "", metadata


def _parse_text(path: Path) -> tuple[str, dict]:
    """Read plain text / markdown files."""
    text = path.read_text(encoding="utf-8", errors="replace")
    return text, {"lines": text.count("\n") + 1}


def _hash_file(path: Path) -> str:
    """SHA-256 hash for integrity verification."""
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def scan_document_directory(directory: str) -> list[dict]:
    """Scan a directory recursively for supported documents."""
    results = []
    dir_path = Path(directory)
    if not dir_path.exists():
        print(f"[DocParser] Directory not found: {directory}")
        return results

    files = [f for f in dir_path.rglob("*") if f.suffix.lower() in DOCUMENT_EXTENSIONS]
    print(f"[DocParser] Found {len(files)} documents in {directory}")

    for file in files:
        parsed = parse_document(str(file))
        if parsed:
            results.append(parsed)

    return results
