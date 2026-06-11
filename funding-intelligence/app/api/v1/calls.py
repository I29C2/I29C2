"""Apeluri de finanțare: listă (cu filtre) + detaliu + istoric versiuni.

TODO (de completat în sesiunea de implementare):
- paginare cursor-based reală (Ghid Tehnic §2.6)
- filtre status (activ/viitor/închis) + sortare deadline
- endpoint diff între două versiuni (pentru badge „modificat recent")
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_token
from app.models.funding_call import CallStatus, FundingCall
from app.schemas.funding_call import FundingCallOut, PaginatedCalls

router = APIRouter()


@router.get("", response_model=PaginatedCalls)
def list_calls(
    status: CallStatus | None = None,
    cursor: int | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    _: str = Depends(require_token),
) -> PaginatedCalls:
    # TODO: aplică filtre + cursor. Schelet minimal mai jos.
    stmt = select(FundingCall).order_by(FundingCall.id).limit(limit)
    if status is not None:
        stmt = stmt.where(FundingCall.status == status)
    if cursor is not None:
        stmt = stmt.where(FundingCall.id > cursor)
    rows = db.execute(stmt).scalars().all()
    next_cursor = rows[-1].id if len(rows) == limit else None
    return PaginatedCalls(items=rows, next_cursor=next_cursor)  # type: ignore[arg-type]


@router.get("/{call_id}", response_model=FundingCallOut)
def get_call(
    call_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_token),
) -> FundingCall:
    call = db.get(FundingCall, call_id)
    if call is None:
        raise HTTPException(status_code=404, detail="Apel inexistent")
    return call
