import fitz  # PyMuPDF

def parse_pdf(file_path: str) -> str:
    parts: list[str] = []
    with fitz.open(file_path) as doc:
        for page_num, page in enumerate(doc, start=1):
            text = page.get_text("text")
            if text.strip():
                parts.append(f"[Page {page_num}]\n{text.strip()}")
    return "\n\n".join(parts)
