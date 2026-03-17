from docx import Document as DocxDocument
from docx.oxml.ns import qn

def parse_docx(file_path: str) -> str:
    doc = DocxDocument(file_path)
    parts: list[str] = []

    for child in doc.element.body:
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag

        if tag == "p":
            # Paragraph
            from docx.text.paragraph import Paragraph
            para = Paragraph(child, doc)
            text = para.text.strip()
            if text:
                style = para.style.name if para.style else ""
                prefix = "# " if "Heading 1" in style else "## " if "Heading 2" in style else ""
                parts.append(f"{prefix}{text}")

        elif tag == "tbl":
            # Table — extract row by row in order
            from docx.table import Table
            table = Table(child, doc)
            for row in table.rows:
                cells = " | ".join(c.text.strip() for c in row.cells if c.text.strip())
                if cells:
                    parts.append(cells)

    return "\n\n".join(parts)
