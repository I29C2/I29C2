"""Documente: listă per apel, descărcare/stream PDF, declanșare parsare.

TODO:
- stream fișier din storage local (FileResponse) pentru viewer-ul PDF inline
- endpoint care declanșează app.documents.tasks.parse_document
- istoric versiuni cu superseded_by_id
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_token
from app.models.document import Document

router = APIRouter()


@router.get("")
def list_documents(
    funding_call_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_token),
) -> list[dict]:
    stmt = select(Document).where(Document.funding_call_id == funding_call_id)
    docs = db.execute(stmt).scalars().all()
    return [
        {
            "id": d.id,
            "type": d.type.value,
            "version": d.version,
            "parsed_status": d.parsed_status.value,
        }
        for d in docs
    ]
