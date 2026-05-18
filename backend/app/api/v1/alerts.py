# backend/app/api/v1/alerts.py
from __future__ import annotations

from typing import List

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.alert import Alert, AlertType
from app.models.user import User
from app.schemas.alert import AlertCreate, AlertResponse

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", response_model=List[AlertResponse])
def get_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    unsent_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> list:
    """Return the authenticated user's alerts."""
    query = db.query(Alert).filter(Alert.user_id == current_user.id)
    if unsent_only:
        query = query.filter(Alert.is_sent == False)  # noqa: E712
    items = (
        query.order_by(Alert.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items


@router.post("/subscribe", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
def subscribe_to_alert(
    body: AlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Alert:
    """Subscribe to a specific alert type (e.g., value_bet, daily_summary)."""
    try:
        alert_type = AlertType(body.alert_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid alert_type: {body.alert_type}",
        )

    message = body.message or _default_message(alert_type, body)

    alert = Alert(
        user_id=current_user.id,
        match_id=body.match_id,
        prediction_id=body.prediction_id,
        alert_type=alert_type,
        message=message,
        is_sent=False,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    logger.info(
        "alert_created",
        alert_id=alert.id,
        user_id=current_user.id,
        alert_type=alert_type.value,
    )
    return alert


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Delete an alert owned by the current user."""
    alert = db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    if alert.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your alert")
    db.delete(alert)
    db.commit()


def _default_message(alert_type: AlertType, body: AlertCreate) -> str:
    messages = {
        AlertType.value_bet: "You will be notified when a new value bet is detected.",
        AlertType.daily_summary: "You will receive a daily summary of value bets.",
        AlertType.risk_warning: "You will be alerted when a match has a high integrity risk.",
        AlertType.custom: "Custom alert created.",
    }
    return messages.get(alert_type, "Alert created.")
