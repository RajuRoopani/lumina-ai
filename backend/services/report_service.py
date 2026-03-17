import anthropic
from models import DocumentORM
from prompts.report_prompt import get_report_prompt, SIGNATURE_COLORS
from config import ANTHROPIC_API_KEY

# Mirror the chat service's per-document truncation ceiling
_MAX_DOC_CHARS = 6000


def pick_signature_color(report_index: int) -> str:
    return SIGNATURE_COLORS[report_index % len(SIGNATURE_COLORS)]


def build_document_context(docs: list[DocumentORM]) -> str:
    parts: list[str] = []
    for i, doc in enumerate(docs, start=1):
        text = doc.extracted_text
        truncated = len(text) > _MAX_DOC_CHARS
        if truncated:
            text = text[:_MAX_DOC_CHARS] + "\n... [truncated] ..."
        parts.append(f"[DOCUMENT {i}: {doc.filename}]\n{text}")
    return "\n\n---\n\n".join(parts)


def generate_report_html(docs: list[DocumentORM], signature_color: str) -> str:
    """Generate a rich HTML report from one or more documents using Claude.

    Raises:
        ValueError: if docs is empty, API key is missing, API call fails,
                    or Claude returns an unusable response.
    """
    if not docs:
        raise ValueError("Need at least one document to generate a report")
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY is not configured")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    doc_context = build_document_context(docs)
    is_multi = len(docs) > 1
    multi_instruction = (
        "\n\nThis is a MULTI-DOCUMENT report. Include per-doc-analysis, "
        "comparison, and synthesis sections in addition to the standard sections."
    ) if is_multi else ""

    try:
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
    except anthropic.APIError as exc:
        raise ValueError(f"Claude API error during report generation: {exc}") from exc

    if not message.content:
        raise ValueError("Claude returned an empty response for report generation")

    first_block = message.content[0]
    if not hasattr(first_block, "text") or not first_block.text:
        raise ValueError(
            f"Claude returned unexpected content type '{type(first_block).__name__}' "
            "or empty text"
        )
    return first_block.text
