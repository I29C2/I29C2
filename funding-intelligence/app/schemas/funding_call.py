"""Contracte API pentru apeluri. Din astea se generează tipurile TS în frontend."""

from datetime import date, datetime

from pydantic import BaseModel

from app.models.funding_call import CallStatus


class FundingCallOut(BaseModel):
    id: int
    source_id: str
    program: str | None
    axis: str | None
    title: str
    slug: str | None
    status: CallStatus
    budget_total: float | None
    deadline_submission: date | None
    url_official: str | None
    last_changed_at: datetime | None

    class Config:
        from_attributes = True


class FundingCallListItem(BaseModel):
    """Variantă slabă pentru listă (dashboard)."""

    id: int
    title: str
    program: str | None
    status: CallStatus
    deadline_submission: date | None
    # Badge „modificat recent" în UI se calculează din asta.
    last_changed_at: datetime | None

    class Config:
        from_attributes = True


class PaginatedCalls(BaseModel):
    items: list[FundingCallListItem]
    next_cursor: int | None = None
