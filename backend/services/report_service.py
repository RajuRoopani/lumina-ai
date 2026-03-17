import anthropic
from models import DocumentORM
from prompts.report_prompt import get_report_prompt, SIGNATURE_COLORS
from config import ANTHROPIC_API_KEY


def pick_signature_color(report_index: int) -> str:
    return SIGNATURE_COLORS[report_index % len(SIGNATURE_COLORS)]


def build_document_context(docs: list[DocumentORM]) -> str:
    parts: list[str] = []
    for i, doc in enumerate(docs, start=1):
        parts.append(f"[DOCUMENT {i}: {doc.filename}]\n{doc.extracted_text}")
    return "\n\n---\n\n".join(parts)


def generate_report_html(docs: list[DocumentORM], signature_color: str) -> str:
    if not docs:
        raise ValueError("Need at least one document to generate a report")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    doc_context = build_document_context(docs)
    is_multi = len(docs) > 1
    multi_instruction = (
        "\n\nThis is a MULTI-DOCUMENT report. Include per-doc-analysis, "
        "comparison, and synthesis sections in addition to the standard sections."
    ) if is_multi else ""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        system=get_report_prompt(signature_color),
        messages=[{
            "role": "user",
            "content": (
                f"Generate a rich HTML report for the following document(s):"
                f"{multi_instruction}\n\n{doc_context}"
            )
        }]
    )

    if not message.content:
        raise ValueError("Claude returned an empty response for report generation")
    return message.content[0].text
