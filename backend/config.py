import os
from pathlib import Path

ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "")
UPLOAD_DIR: Path = Path(os.environ.get("UPLOAD_DIR", "uploads"))
PUBLIC_BASE_URL: str = os.environ.get("PUBLIC_BASE_URL", "http://localhost:5173")
DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite:///./docviz.db")

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/markdown",
    "text/plain",
    "image/png",
    "image/jpeg",
    "image/gif",
    "image/webp",
}
MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB
