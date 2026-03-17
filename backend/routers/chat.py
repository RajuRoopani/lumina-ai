import json
import re
import uuid
from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database import get_db
from models import DocumentORM, ReportORM, ChatMessageORM, ChatMessageSchema
from services.chat_service import stream_chat_response
from services.report_service import generate_report_html, pick_signature_color

router = APIRouter()


@router.post("/{report_id}/stream")
def chat_stream(
    report_id: str,
    message: str = Body(..., embed=True),
    db: Session = Depends(get_db),
):
    report = db.query(ReportORM).filter(ReportORM.id == report_id).first()
    if not report:
        raise HTTPException(404, "Report not found")

    doc_ids = json.loads(report.document_ids_json)
    docs = [
        db.query(DocumentORM).filter(DocumentORM.id == did).first()
        for did in doc_ids
    ]
    docs = [d for d in docs if d is not None]

    history_orms = (
        db.query(ChatMessageORM)
        .filter(ChatMessageORM.report_id == report_id)
        .order_by(ChatMessageORM.created_at)
        .limit(20)
        .all()
    )
    history = [{"role": m.role, "content": m.content} for m in history_orms]

    # Save user message before streaming
    user_msg = ChatMessageORM(
        id=str(uuid.uuid4()),
        report_id=report_id,
        role="user",
        content=message,
    )
    db.add(user_msg)
    db.commit()

    collected_text: list[str] = []
    collected_action: list[dict] = []

    def event_stream():
        for chunk in stream_chat_response(report, docs, message, history):
            yield chunk
            if chunk.startswith("data: "):
                try:
                    payload = json.loads(chunk[6:].strip())
                    if payload.get("type") == "chunk":
                        collected_text.append(payload["text"])
                    if payload.get("type") == "action":
                        collected_action.append(payload["action"])
                except Exception:
                    pass
        # Save assistant response after stream completes
        ai_text = "".join(collected_text)
        action_data = collected_action[0] if collected_action else None
        assistant_msg = ChatMessageORM(
            id=str(uuid.uuid4()),
            report_id=report_id,
            role="assistant",
            content=ai_text,
            action=action_data["action"] if action_data else None,
            action_data_json=json.dumps(action_data) if action_data else "{}",
        )
        db.add(assistant_msg)
        db.commit()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/{report_id}/messages", response_model=list[ChatMessageSchema])
def get_messages(report_id: str, db: Session = Depends(get_db)):
    messages = (
        db.query(ChatMessageORM)
        .filter(ChatMessageORM.report_id == report_id)
        .order_by(ChatMessageORM.created_at)
        .all()
    )
    return [ChatMessageSchema.from_orm_model(m) for m in messages]


@router.post("/compare")
def compare_docs(
    document_ids: list[str] = Body(..., embed=True),
    prompt: str = Body(..., embed=True),
    db: Session = Depends(get_db),
):
    docs = [
        db.query(DocumentORM).filter(DocumentORM.id == did).first()
        for did in document_ids
    ]
    docs = [d for d in docs if d is not None]
    if len(docs) < 2:
        raise HTTPException(400, "Need at least 2 valid documents to compare")

    report_index = db.query(ReportORM).count()
    color = pick_signature_color(report_index)

    def event_stream():
        yield f"data: {{\"event\":\"progress\",\"data\":\"Comparing {len(docs)} documents...\"}}\n\n"
        try:
            html = generate_report_html(docs, signature_color=color)
            report_id = str(uuid.uuid4())
            title_m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
            title = (
                re.sub(r"<[^>]+>", "", title_m.group(1)).strip()
                if title_m
                else "Comparison Report"
            )
            orm = ReportORM(
                id=report_id,
                title=title,
                document_ids_json=json.dumps(document_ids),
                html_content=html,
                signature_color=color,
            )
            db.add(orm)
            db.commit()
            yield f"data: {{\"event\":\"done\",\"data\":{{\"id\":\"{report_id}\",\"title\":\"{title}\"}}}}\n\n"
        except Exception as e:
            yield f"data: {{\"event\":\"error\",\"data\":\"{str(e)}\"}}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
