import json
import re
import uuid
from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
from database import get_db
from models import DocumentORM, ReportORM, ReportSchema, ReportMetaSchema
from services.report_service import generate_report_html, pick_signature_color

router = APIRouter()


def _get_report_or_404(report_id: str, db: Session) -> ReportORM:
    r = db.query(ReportORM).filter(ReportORM.id == report_id).first()
    if not r:
        raise HTTPException(404, "Report not found")
    return r


@router.post("/generate")
def generate_report(
    document_ids: list[str] = Body(..., embed=True),
    db: Session = Depends(get_db),
):
    docs = [
        db.query(DocumentORM).filter(DocumentORM.id == did).first()
        for did in document_ids
    ]
    docs = [d for d in docs if d is not None]
    if not docs:
        raise HTTPException(400, "No valid documents found for given IDs")

    def event_stream():
        yield f"data: {{\"event\":\"progress\",\"data\":\"Analyzing {len(docs)} document(s)...\"}}\n\n"
        try:
            report_index = db.query(ReportORM).count()
            color = pick_signature_color(report_index)
            yield f"data: {{\"event\":\"progress\",\"data\":\"Generating rich HTML report...\"}}\n\n"
            html = generate_report_html(docs, signature_color=color)

            report_id = str(uuid.uuid4())
            title_match = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
            title = (
                re.sub(r"<[^>]+>", "", title_match.group(1)).strip()
                if title_match
                else docs[0].filename
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


@router.get("", response_model=list[ReportMetaSchema])
def list_reports(db: Session = Depends(get_db)):
    reports = db.query(ReportORM).order_by(ReportORM.created_at.desc()).all()
    return [
        ReportMetaSchema(
            id=r.id,
            title=r.title,
            document_ids=json.loads(r.document_ids_json),
            signature_color=r.signature_color,
            created_at=r.created_at,
        )
        for r in reports
    ]


@router.get("/{report_id}", response_model=ReportSchema)
def get_report(report_id: str, db: Session = Depends(get_db)):
    r = _get_report_or_404(report_id, db)
    return ReportSchema.from_orm_model(r)


@router.delete("/{report_id}", status_code=204)
def delete_report(report_id: str, db: Session = Depends(get_db)):
    r = _get_report_or_404(report_id, db)
    db.delete(r)
    db.commit()


@router.get("/{report_id}/export")
def export_report(report_id: str, db: Session = Depends(get_db)):
    r = _get_report_or_404(report_id, db)
    filename = r.title.replace(" ", "-").lower()[:50] + ".html"
    return Response(
        content=r.html_content,
        media_type="text/html",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.patch("/{report_id}/section")
def update_section(
    report_id: str,
    section_id: str = Body(..., embed=True),
    html: str = Body(..., embed=True),
    db: Session = Depends(get_db),
):
    r = _get_report_or_404(report_id, db)
    pattern = re.compile(
        r'<section[^>]+data-section-id="' + re.escape(section_id) + r'".*?</section>',
        re.DOTALL,
    )
    if not pattern.search(r.html_content):
        raise HTTPException(404, f"Section '{section_id}' not found in report HTML")
    r.html_content = pattern.sub(html, r.html_content, count=1)
    db.commit()
    db.refresh(r)
    return ReportSchema.from_orm_model(r)
