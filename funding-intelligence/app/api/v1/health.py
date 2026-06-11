"""Health detaliat: verifică DB și Redis (DevOps §5.3).

Endpoint-ul simplu /health din main.py rămâne pentru liveness; ăsta e readiness.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db

router = APIRouter()


@router.get("/health/ready")
def readiness(db: Session = Depends(get_db)) -> dict[str, object]:
    checks: dict[str, object] = {}
    try:
        db.execute(text("SELECT 1"))
        checks["db"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["db"] = f"error: {exc}"
    # TODO: ping Redis. Și expune ultima rulare reușită per scraper (metrici §5.3).
    checks["status"] = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return checks
