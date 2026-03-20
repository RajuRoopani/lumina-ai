import json
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from database import engine, get_db, Base
from models import ReportORM
from routers import documents, reports, chat, visualize

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Lumina")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(visualize.router, prefix="/api/visualize", tags=["visualize"])

@app.get("/share/{report_id}", response_class=HTMLResponse)
def share_report(report_id: str, db: Session = Depends(get_db)):
    report = db.query(ReportORM).filter(ReportORM.id == report_id).first()
    if not report:
        return HTMLResponse("<h1>Report not found</h1>", status_code=404)
    return HTMLResponse(content=report.html_content)

@app.get("/health")
def health():
    return {"status": "ok"}

# Serve React SPA (catch-all) — must be last
try:
    app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="static")
except Exception as exc:
    import warnings
    warnings.warn(f"Frontend static files not mounted: {exc}", stacklevel=1)
