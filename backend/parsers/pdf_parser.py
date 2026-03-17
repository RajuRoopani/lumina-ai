import fitz  # PyMuPDF


def parse_pdf(file_path: str) -> str:
    """Extract text from a PDF file, annotating each page."""
    doc = fitz.open(file_path)
    parts: list[str] = []
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text("text")
        if text.strip():
            parts.append(f"[Page {page_num}]\n{text.strip()}")
    doc.close()
    return "\n\n".join(parts)
