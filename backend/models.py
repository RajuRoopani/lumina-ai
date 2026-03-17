import uuid
import json
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from pydantic import BaseModel
from typing import Optional
from database import Base

def now_utc() -> datetime:
    return datetime.now(timezone.utc)

def new_uuid() -> str:
    return str(uuid.uuid4())

# --- ORM Models ---

class DocumentORM(Base):
    __tablename__ = "documents"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    filename: Mapped[str] = mapped_column(String)
    source_type: Mapped[str] = mapped_column(String)  # pdf|docx|url|markdown|text|image
    source_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    file_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    extracted_text: Mapped[str] = mapped_column(Text, default="")
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)

class ReportORM(Base):
    __tablename__ = "reports"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    title: Mapped[str] = mapped_column(String, default="Untitled Report")
    document_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    html_content: Mapped[str] = mapped_column(Text, default="")
    signature_color: Mapped[str] = mapped_column(String, default="#388bfd")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)

class ChatMessageORM(Base):
    __tablename__ = "chat_messages"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    report_id: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String)  # user|assistant|annotation
    content: Mapped[str] = mapped_column(Text)
    action: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    action_data_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)

# --- Pydantic Schemas ---

class DocumentSchema(BaseModel):
    id: str
    filename: str
    source_type: str
    source_url: Optional[str]
    extracted_text: str
    created_at: datetime
    model_config = {"from_attributes": True}

class ReportSchema(BaseModel):
    id: str
    title: str
    document_ids: list[str]
    html_content: str
    signature_color: str
    created_at: datetime
    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_model(cls, obj: ReportORM) -> "ReportSchema":
        return cls(
            id=obj.id,
            title=obj.title,
            document_ids=json.loads(obj.document_ids_json),
            html_content=obj.html_content,
            signature_color=obj.signature_color,
            created_at=obj.created_at,
        )

class ReportMetaSchema(BaseModel):
    id: str
    title: str
    document_ids: list[str]
    signature_color: str
    created_at: datetime

class ChatMessageSchema(BaseModel):
    id: str
    report_id: str
    role: str
    content: str
    action: Optional[str]
    action_data: dict
    created_at: datetime
    model_config = {"from_attributes": True}
