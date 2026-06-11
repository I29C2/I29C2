"""Dependențe comune API: auth (token static la MVP) + sesiune DB.

MVP: un singur token static (ești singurul utilizator). Înlocuit cu sesiuni
server-side / JWT + roluri când apar utilizatori multipli (Ghid Tehnic §6.2).
"""

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db

__all__ = ["get_db", "require_token"]


def require_token(authorization: str = Header(default="")) -> str:
    """Verifică `Authorization: Bearer <token>` față de tokenul static."""
    expected = f"Bearer {settings.api_static_token}"
    if authorization != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalid sau lipsă",
        )
    return "internal-user"  # actor pentru audit_log; un singur user la MVP


# Re-export tipat pentru claritate în rute.
DbSession = Depends(get_db)
Auth = Depends(require_token)


def _typing_only(db: Session) -> None:  # pragma: no cover
    """Marker ca importul Session să nu fie semnalat ca neutilizat de ruff."""
