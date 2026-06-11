"""Ecranul de validare — API. Cel mai important flux din MVP (<10 min/ghid).

Stânga: câmpurile extrase (cu confidence). Dreapta: PDF la pagina-sursă.
Acțiuni: confirmă / corectează / respinge. Fiecare mutație scrie în audit_log.

TODO:
- la 'corrected', validează corrected_value față de JSON Schema (schemas/eligibility)
- scrie audit_log (old_value/new_value)
- setează validated_by + validated_at
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_token
from app.models.eligibility import EligibilityCriterion, ValidationStatus
from app.schemas.eligibility import CriterionOut, ValidationAction

router = APIRouter()


@router.get("/{call_id}/criteria", response_model=list[CriterionOut])
def list_criteria(
    call_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_token),
) -> list[EligibilityCriterion]:
    """Toate câmpurile extrase pentru un apel, pentru split-view-ul de validare."""
    stmt = select(EligibilityCriterion).where(
        EligibilityCriterion.funding_call_id == call_id
    )
    return list(db.execute(stmt).scalars().all())


@router.post("/criteria/{criterion_id}", response_model=CriterionOut)
def validate_criterion(
    criterion_id: int,
    action: ValidationAction,
    db: Session = Depends(get_db),
    actor: str = Depends(require_token),
) -> EligibilityCriterion:
    crit = db.get(EligibilityCriterion, criterion_id)
    if crit is None:
        raise HTTPException(status_code=404, detail="Criteriu inexistent")

    # TODO: validare JSON Schema la corrected; scriere audit_log; validated_at.
    if action.action == ValidationStatus.corrected and action.corrected_value is not None:
        crit.value = action.corrected_value
    crit.validation_status = action.action
    crit.validated_by = actor
    db.commit()
    db.refresh(crit)
    return crit
