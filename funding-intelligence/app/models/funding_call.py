"""Schema canonică „Apel de finanțare" — contractul central al sistemului.

Regulă (Ghid Tehnic §2.2): nimic nu se șterge fizic din funding_call — doar
soft-delete/supersede. Istoricul (corrigende) e cerință de produs.
"""

import enum
from datetime import date, datetime

from sqlalchemy import ARRAY, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class CallStatus(str, enum.Enum):
    upcoming = "upcoming"
    active = "active"
    closed = "closed"
    suspended = "suspended"


class FundingCall(Base, TimestampMixin):
    __tablename__ = "funding_call"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[str] = mapped_column(String(64), index=True)
    program: Mapped[str | None] = mapped_column(String(255))
    axis: Mapped[str | None] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(Text)
    slug: Mapped[str | None] = mapped_column(String(255), unique=True)

    status: Mapped[CallStatus] = mapped_column(default=CallStatus.upcoming)

    budget_total: Mapped[float | None] = mapped_column(Numeric(18, 2))
    budget_min: Mapped[float | None] = mapped_column(Numeric(18, 2))
    budget_max: Mapped[float | None] = mapped_column(Numeric(18, 2))

    deadline_submission: Mapped[date | None]
    deadline_clarifications: Mapped[date | None]

    url_official: Mapped[str | None] = mapped_column(Text)
    first_seen_at: Mapped[datetime | None]
    last_changed_at: Mapped[datetime | None]

    # Pre-decizie multi-tenancy (Ghid Tehnic §6.2): prezent, nefolosit acum.
    org_id: Mapped[int | None] = mapped_column(index=True)

    versions: Mapped[list["FundingCallVersion"]] = relationship(back_populates="call")


class ChangeSource(str, enum.Enum):
    scrape = "scrape"
    manual = "manual"


class FundingCallVersion(Base):
    """Istoric complet al modificărilor — un snapshot per schimbare detectată."""

    __tablename__ = "funding_call_version"

    id: Mapped[int] = mapped_column(primary_key=True)
    funding_call_id: Mapped[int] = mapped_column(ForeignKey("funding_call.id"))
    snapshot: Mapped[dict] = mapped_column(JSONB)
    changed_fields: Mapped[list[str]] = mapped_column(ARRAY(Text))
    detected_at: Mapped[datetime]
    change_source: Mapped[ChangeSource] = mapped_column(default=ChangeSource.scrape)

    call: Mapped["FundingCall"] = relationship(back_populates="versions")
