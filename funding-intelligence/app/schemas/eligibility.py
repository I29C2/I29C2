"""Contracte API pentru ecranul de validare — cel mai important UI din produs."""

from typing import Any

from pydantic import BaseModel

from app.models.eligibility import ValidationStatus


class CriterionOut(BaseModel):
    id: int
    field_name: str
    value: Any
    confidence: float | None
    source_document_id: int | None
    source_page: int | None
    source_quote: str | None
    validation_status: ValidationStatus

    class Config:
        from_attributes = True


class ValidationAction(BaseModel):
    """Confirmă / corectează / respinge un câmp extras."""

    action: ValidationStatus  # validated | corrected | rejected
    # Prezent doar la 'corrected': noua valoare introdusă de consultant.
    corrected_value: Any | None = None
    note: str | None = None
