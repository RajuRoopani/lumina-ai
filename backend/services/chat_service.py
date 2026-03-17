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
    lower = message.lower()
    if any(kw in lower for kw in NEW_REPORT_KEYWORDS):
        return "new_report"
    if any(lower.startswith(kw) or f" {kw} " in lower for kw in EDIT_KEYWORDS):
        return "edit"
    return "qa"


def parse_action_from_response(response: str) -> tuple[str, Optional[dict]]:
    """Extract <ACTION>...</ACTION> block and return (text_before, action_dict)."""
    match = re.search(r"<ACTION>\s*(\{.*?\})\s*</ACTION>", response, re.DOTALL)
    if not match:
        return response, None
    text = response[:match.start()].strip()
    try:
        action = json.loads(match.group(1))
    except json.JSONDecodeError:
        return response, None
    return text, action


def build_chat_context(report: ReportORM, docs: list[DocumentORM]) -> str:
    doc_texts = "\n\n---\n\n".join(
        f"[DOC: {d.filename}]\n{d.extracted_text[:3000]}" for d in docs
    )
    return f"DOCUMENT CONTENT:\n{doc_texts}\n\nCURRENT REPORT HTML (first 4000 chars):\n{report.html_content[:4000]}"


def stream_chat_response(
    report: ReportORM,
    docs: list[DocumentORM],
    message: str,
    history: list[dict],
) -> Generator[str, None, None]:
    """Yields SSE-formatted strings."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    context = build_chat_context(report, docs)

    messages = list(history[-10:]) + [{"role": "user", "content": message}]
    # Prepend context to the first user message
    messages[0] = {
        "role": "user",
        "content": f"{context}\n\nUser question: {messages[0]['content']}"
    }

    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT_CHAT,
        messages=messages,
    ) as stream:
        full_response = ""
        for text_chunk in stream.text_stream:
            full_response += text_chunk
            yield f"data: {json.dumps({'type': 'chunk', 'text': text_chunk})}\n\n"

    text, action = parse_action_from_response(full_response)
    if action:
        yield f"data: {json.dumps({'type': 'action', 'action': action})}\n\n"

    yield f"data: {json.dumps({'type': 'done'})}\n\n"
