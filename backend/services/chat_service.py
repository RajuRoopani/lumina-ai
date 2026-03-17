import json
import re
from typing import Generator, Optional
import anthropic
from models import DocumentORM, ReportORM
from prompts.chat_prompt import SYSTEM_PROMPT_CHAT
from config import ANTHROPIC_API_KEY

EDIT_KEYWORDS = {"add", "insert", "update", "change", "remove", "create a diagram",
                 "expand", "modify", "rewrite", "include", "append"}
NEW_REPORT_KEYWORDS = {"propose", "proposal", "new design", "new report",
                       "compare and", "draft a new", "generate a new"}


def detect_intent(message: str) -> str:
    """Classify message intent: new_report > edit > qa (priority order)."""
    lower = message.lower()
    if any(kw in lower for kw in NEW_REPORT_KEYWORDS):
        return "new_report"
    if any(lower.startswith(kw) or f" {kw} " in lower for kw in EDIT_KEYWORDS):
        return "edit"
    return "qa"


def parse_action_from_response(response: str) -> tuple[str, Optional[dict]]:
    """Extract <ACTION>...</ACTION> block and return (text_before, action_dict).

    Captures everything between <ACTION> and </ACTION> tags (handles HTML with
    braces in JSON field values), then parses as JSON.
    """
    match = re.search(r"<ACTION>\s*(.*?)\s*</ACTION>", response, re.DOTALL)
    if not match:
        return response, None
    text = response[:match.start()].strip()
    try:
        action = json.loads(match.group(1))
    except json.JSONDecodeError:
        return response, None
    return text, action


def build_chat_context(report: ReportORM, docs: list[DocumentORM]) -> str:
    """Build the context string prepended to every chat message."""
    doc_texts = "\n\n---\n\n".join(
        f"[DOC: {d.filename}]\n{d.extracted_text[:3000]}"
        + (" [truncated]" if len(d.extracted_text) > 3000 else "")
        for d in docs
    )
    html_preview = report.html_content[:4000]
    if len(report.html_content) > 4000:
        html_preview += "\n... [truncated] ..."
    return (
        f"DOCUMENT CONTENT:\n{doc_texts}\n\n"
        f"CURRENT REPORT HTML (first 4000 chars):\n{html_preview}"
    )


def stream_chat_response(
    report: ReportORM,
    docs: list[DocumentORM],
    message: str,
    history: list[dict],
) -> Generator[str, None, None]:
    """Stream Claude chat response as SSE-formatted strings.

    Yields:
        data: {"type": "chunk", "text": "..."}  -- one per text delta
        data: {"type": "action", "action": {...}}  -- if Claude returns an ACTION block
        data: {"type": "done"}  -- always the last event, even on error
        data: {"type": "error", "message": "..."}  -- on API failure (before done)
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    context = build_chat_context(report, docs)

    # Build messages: inject context into the CURRENT user message (last position)
    messages: list[dict] = list(history[-10:]) + [{
        "role": "user",
        "content": f"{context}\n\nUser question: {message}",
    }]

    full_response = ""
    try:
        with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=SYSTEM_PROMPT_CHAT,
            messages=messages,
        ) as stream:
            for text_chunk in stream.text_stream:
                full_response += text_chunk
                yield f"data: {json.dumps({'type': 'chunk', 'text': text_chunk})}\n\n"

        _text, action = parse_action_from_response(full_response)
        if action:
            yield f"data: {json.dumps({'type': 'action', 'action': action})}\n\n"

    except anthropic.APIError as exc:
        yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"
    finally:
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
