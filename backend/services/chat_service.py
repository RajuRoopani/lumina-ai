import json
import re
from typing import Generator
import anthropic
from models import DocumentORM, ReportORM
from prompts.chat_prompt import SYSTEM_PROMPT_CHAT
from config import ANTHROPIC_API_KEY
from services.learnings_service import record_chat_interaction

# ── Tool definitions passed to the API ───────────────────────────────────────
_TOOLS = [
    {
        "name": "update_section",
        "description": (
            "Update a specific section in the HTML report. "
            "Call this whenever the user asks to add, change, expand, improve, or remove content in any section. "
            "Use one of the section IDs listed in the context."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "section_id": {
                    "type": "string",
                    "description": "The data-section-id value of the section to update (must be from the available section IDs list).",
                },
                "html": {
                    "type": "string",
                    "description": (
                        "The complete replacement <section id='...' data-section-id='...'> ... </section> HTML. "
                        "Must be a full section element with all existing content preserved plus the requested changes. "
                        "Use the report CSS classes: callout, pill, table, diagram-container, box-row, box, arrow, timeline, approach-card. "
                        "Do NOT use Mermaid.js."
                    ),
                },
                "summary": {
                    "type": "string",
                    "description": "One sentence describing what was changed.",
                },
            },
            "required": ["section_id", "html", "summary"],
        },
    }
]


def build_chat_context(report: ReportORM, docs: list[DocumentORM]) -> str:
    """Build context injected as the user message prefix."""
    section_ids = re.findall(r'data-section-id="([^"]+)"', report.html_content)
    section_ids_str = ", ".join(section_ids) if section_ids else "none"

    doc_texts = "\n\n---\n\n".join(
        f"[DOC: {d.filename}]\n{d.extracted_text[:3000]}"
        + (" [truncated]" if len(d.extracted_text) > 3000 else "")
        for d in docs
    )
    # Send first 6000 chars of HTML so the model can see the section structure
    html_preview = report.html_content[:6000]
    if len(report.html_content) > 6000:
        html_preview += "\n... [truncated] ..."

    return (
        f"AVAILABLE SECTION IDs: {section_ids_str}\n\n"
        f"DOCUMENT CONTENT:\n{doc_texts}\n\n"
        f"CURRENT REPORT HTML:\n{html_preview}"
    )


def stream_chat_response(
    report: ReportORM,
    docs: list[DocumentORM],
    message: str,
    history: list[dict],
) -> Generator[str, None, None]:
    """Stream Claude chat response as SSE strings.

    Yields:
        data: {"type": "chunk", "text": "..."}       — text delta
        data: {"type": "action", "action": {...}}     — tool call result
        data: {"type": "error", "message": "..."}     — on API failure
        data: {"type": "done"}                        — always last
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    context = build_chat_context(report, docs)

    messages: list[dict] = list(history[-10:]) + [{
        "role": "user",
        "content": f"{context}\n\nUser request: {message}",
    }]

    try:
        # Non-streaming call so we can reliably inspect tool_use blocks
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=6000,
            system=SYSTEM_PROMPT_CHAT,
            tools=_TOOLS,  # type: ignore[arg-type]
            messages=messages,
        )

        # Emit text content chunks first
        text_parts: list[str] = []
        tool_call: dict | None = None

        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
                # Stream character-by-character would require streaming=True;
                # for non-streaming emit as one chunk (still fast enough)
                yield f"data: {json.dumps({'type': 'chunk', 'text': block.text})}\n\n"
            elif block.type == "tool_use" and block.name == "update_section":
                tool_call = {
                    "action": "section_update",
                    "section_id": block.input.get("section_id", ""),
                    "html": block.input.get("html", ""),
                    "summary": block.input.get("summary", ""),
                }

        if tool_call:
            # If no text explanation was given alongside the tool call, add summary
            if not text_parts:
                summary = tool_call.get("summary", "Section updated.")
                yield f"data: {json.dumps({'type': 'chunk', 'text': summary})}\n\n"
            yield f"data: {json.dumps({'type': 'action', 'action': tool_call})}\n\n"

        # Record interaction for retro loop (non-blocking)
        try:
            record_chat_interaction(
                action_taken=tool_call["action"] if tool_call else None,
                section_id=tool_call.get("section_id") if tool_call else None,
            )
        except Exception:
            pass

    except anthropic.APIError as exc:
        yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"
    finally:
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
