"""Taskuri Celery pentru extracția AI."""

import logging

from app.celery_app import celery

logger = logging.getLogger(__name__)


@celery.task
def extract_fields(document_id: int) -> None:
    """Rulează extracția pe un document parsat și scrie eligibility_criteria (status=auto).

    TODO:
    - încarcă ParsedDocument (sau re-parsează din storage)
    - extraction.extract() → scrie EligibilityCriterion cu validation_status=auto
    - NICIODATĂ nu marca automat validated — asta e treaba omului în UI
    """
    logger.info("extract_fields %s — neimplementat", document_id)
