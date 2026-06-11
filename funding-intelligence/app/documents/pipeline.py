"""Pipeline de parsare documente (Docling).

document descărcat → sha256 → storage → Docling parse → JSON structurat (text+layout+tabele)
  → detectare tip conținut:
       text nativ  → chunking pe secțiuni logice
       scan/imagine → flag needs_manual (OCR e decizie ulterioară, NU în MVP)

ATENȚIE PERFORMANȚĂ (feedback): Docling pe CPU e lent. Rulează doar în worker
Celery (job de noapte), niciodată sincron în request. concurrency=1 în compose.

La MVP NU facem chunking/embeddings (RAG amânat) — doar text + layout + tabele
ca input pentru extracția structurată LLM.
"""

from dataclasses import dataclass


@dataclass
class ParsedDocument:
    """Rezultatul Docling, normalizat pentru extracție."""

    full_text: str
    pages: list[str]          # text per pagină — sursa pentru source_page
    has_text_layer: bool      # False = probabil scan → needs_manual
    tables: list[dict]        # tabele extrase (structură păstrată)


def parse(content: bytes) -> ParsedDocument:
    """Rulează Docling pe conținutul PDF.

    TODO (implementare):
    - inițializează DocumentConverter (Docling) o singură dată per proces (e scump)
    - convert din bytes
    - extrage text per pagină (pentru source_page la extracție)
    - detectează has_text_layer; dacă False → caller marchează needs_manual
    """
    raise NotImplementedError("Integrare Docling — de completat în sesiunea de implementare")
