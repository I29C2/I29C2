"""Taskuri Celery pentru pipeline-ul de documente."""

import logging

from app.celery_app import celery

logger = logging.getLogger(__name__)


@celery.task
def parse_document(document_id: int) -> None:
    """Descarcă (dacă e nevoie) → Docling → marchează parsed_status → declanșează extracția.

    TODO:
    - încarcă Document din DB, citește bytes din storage
    - pipeline.parse(); la has_text_layer=False → parsed_status=needs_manual, STOP
    - la succes → parsed_status=parsed → app.ai.tasks.extract_fields.delay(document_id)
    - la corrigendum: marchează versiunea veche superseded (NU șterge)
    """
    logger.info("parse_document %s — neimplementat", document_id)
