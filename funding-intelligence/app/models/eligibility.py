"""Criterii de eligibilitate — populate de AI, validate de om.

REGULĂ DE SISTEM (Ghid Tehnic §3.3): doar câmpurile cu validation_status IN
(validated, corrected) pot alimenta vreodată matching-ul. Se aplică în query.
"""

import enum

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class ValidationStatus(str, enum.Enum):
    auto = "auto"          # propus de AI, nevalidat — NU intră în matching
    validated = "validated"
    corrected = "corrected"
    rejected = "rejected"


class EligibilityCriterion(Base, TimestampMixin):
    __tablename__ = "eligibility_criteria"

    id: Mapped[int] = mapped_column(primary_key=True)
    funding_call_id: Mapped[int] = mapped_column(ForeignKey("funding_call.id"))
    field_name: Mapped[str] = mapped_column(String(128), index=True)
    # JSONB pentru flexibilitate, dar fiecare field_name are JSON Schema în
    # schemas/eligibility/*.json — validat la scriere (vezi schemas/registry).
    value: Mapped[dict] = mapped_column(JSONB)

    confidence: Mapped[float | None] = mapped_column(Numeric(4, 3))
    source_document_id: Mapped[int | None] = mapped_column(ForeignKey("document.id"))
    source_page: Mapped[int | None] = mapped_column(Integer)
    # Citatul-suport (span-ul de text din document). Fără sursă → confidence scăzut.
    source_quote: Mapped[str | None]

    validation_status: Mapped[ValidationStatus] = mapped_column(
        default=ValidationStatus.auto
    )
    validated_by: Mapped[str | None] = mapped_column(String(128))
    validated_at: Mapped[str | None]
