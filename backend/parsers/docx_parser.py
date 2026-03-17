from docx import Document as DocxDocument


def parse_docx(file_path: str) -> str:
    """Extract text from a DOCX file, preserving heading hierarchy and table content."""
    doc = DocxDocument(file_path)
    parts: list[str] = []

    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            style = para.style.name if para.style else ""
            prefix = "# " if "Heading 1" in style else "## " if "Heading 2" in style else ""
            parts.append(f"{prefix}{text}")

    for table in doc.tables:
        for row in table.rows:
            cells = " | ".join(c.text.strip() for c in row.cells if c.text.strip())
            if cells:
                parts.append(cells)

    return "\n\n".join(parts)
