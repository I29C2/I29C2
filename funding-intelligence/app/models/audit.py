"""Audit log imuabil pe toate mutațiile (Ghid Tehnic §2.6, §6.2).

La MVP nu avem multi-user, dar păstrăm tabelul de la început: trasabilitatea
validărilor e ieftină acum și imposibil de reconstituit retroactiv.
"""

from datetime import datetime

from sqlalchemy import String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor: Mapped[str] = mapped_column(String(128))     # cine
    action: Mapped[str] = mapped_column(String(64))     # ce (create/update/validate...)
    entity: Mapped[str] = mapped_column(String(64))     # tabel/resursă
    entity_id: Mapped[str] = mapped_column(String(64))
    old_value: Mapped[dict | None] = mapped_column(JSONB)
    new_value: Mapped[dict | None] = mapped_column(JSONB)
    note: Mapped[str | None] = mapped_column(Text)
    at: Mapped[datetime] = mapped_column(server_default=func.now())
