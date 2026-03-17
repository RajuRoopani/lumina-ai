import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body
from sqlalchemy.orm import Session
from werkzeug.utils import secure_filename
from database import get_db
from models import DocumentORM, DocumentSchema
from parsers import parse_document
from config import UPLOAD_DIR, ALLOWED_MIME_TYPES, MAX_UPLOAD_BYTES

router = APIRouter()


def _save_and_parse(db: Session, orm: DocumentORM, raw_content: str = "") -> DocumentORM:
    orm.extracted_text = parse_document(orm, raw_content)
    db.add(orm)
    db.commit()
    db.refresh(orm)
    return orm


@router.post("/upload", response_model=list[DocumentSchema])
async def upload_files(files: list[UploadFile] = File(...), db: Session = Depends(get_db)):
    results: list[DocumentSchema] = []
    for file in files:
        content_type = file.content_type or ""
        if content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(400, f"File type not allowed: {content_type}")
        data = await file.read()
        if len(data) > MAX_UPLOAD_BYTES:
            raise HTTPException(413, f"File too large: {file.filename}")

        doc_id = str(uuid.uuid4())
        safe_name = secure_filename(file.filename or "upload")
        ext = safe_name.rsplit(".", 1)[-1] if "." in safe_name else "bin"
        file_path = UPLOAD_DIR / f"{doc_id}.{ext}"
        file_path.write_bytes(data)

        source_type = (
            "pdf" if "pdf" in content_type else
            "docx" if "wordprocessing" in content_type else
            "image" if "image" in content_type else
            "text"
        )

        orm = DocumentORM(
            id=doc_id,
            filename=file.filename or safe_name,
            source_type=source_type,
            file_path=str(file_path),
        )
        _save_and_parse(db, orm)
        results.append(DocumentSchema.model_validate(orm))
    return results


@router.post("/fetch-url", response_model=DocumentSchema)
def fetch_url(url: str = Body(..., embed=True), db: Session = Depends(get_db)):
    doc_id = str(uuid.uuid4())
    orm = DocumentORM(id=doc_id, filename=url, source_type="url", source_url=url)
    try:
        _save_and_parse(db, orm)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return DocumentSchema.model_validate(orm)


@router.post("/paste", response_model=DocumentSchema)
def paste_text(
    content: str = Body(..., embed=True),
    filename: str = Body("pasted-text.md", embed=True),
    db: Session = Depends(get_db),
):
    doc_id = str(uuid.uuid4())
    source_type = "markdown" if filename.endswith(".md") else "text"
    orm = DocumentORM(id=doc_id, filename=filename, source_type=source_type)
    _save_and_parse(db, orm, raw_content=content)
    return DocumentSchema.model_validate(orm)


@router.get("", response_model=list[DocumentSchema])
def list_documents(db: Session = Depends(get_db)):
    docs = db.query(DocumentORM).order_by(DocumentORM.created_at.desc()).all()
    return [DocumentSchema.model_validate(d) for d in docs]


@router.get("/{doc_id}", response_model=DocumentSchema)
def get_document(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(DocumentORM).filter(DocumentORM.id == doc_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    return DocumentSchema.model_validate(doc)


@router.delete("/{doc_id}", status_code=204)
def delete_document(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(DocumentORM).filter(DocumentORM.id == doc_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    if doc.file_path:
        Path(doc.file_path).unlink(missing_ok=True)
    db.delete(doc)
    db.commit()
