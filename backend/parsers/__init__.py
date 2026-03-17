from models import DocumentORM
from .pdf_parser import parse_pdf
from .docx_parser import parse_docx
from .url_parser import parse_url
from .image_parser import parse_image
from .text_parser import parse_text


def parse_document(doc: DocumentORM, raw_content: str = "") -> str:
    """Dispatch to the correct parser based on source_type. Returns extracted text."""
    if doc.source_type == "pdf":
        if not doc.file_path:
            raise ValueError("file_path required for pdf")
        return parse_pdf(doc.file_path)
    elif doc.source_type == "docx":
        if not doc.file_path:
            raise ValueError("file_path required for docx")
        return parse_docx(doc.file_path)
    elif doc.source_type == "url":
        if not doc.source_url:
            raise ValueError("source_url required for url type")
        return parse_url(doc.source_url)
    elif doc.source_type == "image":
        if not doc.file_path:
            raise ValueError("file_path required for image")
        return parse_image(doc.file_path)
    elif doc.source_type in ("markdown", "text"):
        if not raw_content and doc.file_path:
            raw_content = open(doc.file_path, encoding="utf-8", errors="replace").read()
        return parse_text(raw_content or "")
    else:
        raise ValueError(f"Unknown source_type: {doc.source_type}")
