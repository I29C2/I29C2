"""Documente oficiale (ghiduri, anexe, clarificări, corrigende).

Regulă: niciodată ștergere fizică — doar superseded_by_id. Documentele oficiale
sunt irecuperabile dacă sursa le retrage (Ghid Tehnic §5.4).
"""

import enum
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DocumentType(str, enum.Enum):
    ghid = "ghid"
    anexa = "anexa"
    clarificare = "clarificare"
    corrigendum = "corrigendum"


class ParsedStatus(str, enum.Enum):
    pending = "pending"
    parsed = "parsed"
    needs_manual = "needs_manual"  # scan/imagine fără OCR reușit
    failed = "failed"


class Document(Base):
    __tablename__ = "document"

    id: Mapped[int] = mapped_column(primary_key=True)
    funding_call_id: Mapped[int] = mapped_column(ForeignKey("funding_call.id"))
    type: Mapped[DocumentType]
    version: Mapped[int] = mapped_column(default=1)
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    # Cheia de storage pe disc (înlocuiește storage_key din S3 la MVP).
    storage_key: Mapped[str] = mapped_column(Text)
    parsed_status: Mapped[ParsedStatus] = mapped_column(default=ParsedStatus.pending)
    superseded_by_id: Mapped[int | None] = mapped_column(ForeignKey("document.id"))
    downloaded_at: Mapped[datetime | None]
