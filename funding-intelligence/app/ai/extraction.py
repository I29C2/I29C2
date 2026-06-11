"""Extracție structurată a câmpurilor de eligibilitate din textul ghidului.

Per câmp extras (Ghid Tehnic §3.3): value + confidence + source_page + source_quote.
Fără sursă identificabilă → validation_status=auto, confidence scăzut, NICIODATĂ
direct în matching.

Promptul e fișier versionat în repo (prompts/extraction/v1.md), NU string inline.
Conținutul documentului se pune într-un bloc delimitat, tratat ca untrusted.
"""

from dataclasses import dataclass
from pathlib import Path

PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "extraction" / "v1.md"


@dataclass
class ExtractedField:
    field_name: str
    value: object
    confidence: float
    source_page: int | None
    source_quote: str | None


def load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def extract(full_text: str, pages: list[str]) -> list[ExtractedField]:
    """Cheamă LLM-ul cu structured output și întoarce câmpurile extrase.

    TODO (implementare):
    - construiește mesajul: prompt sistem + <document untrusted>...</document>
    - tool/structured output cu JSON schema = câmpurile din schemas/eligibility/*
    - mapează fiecare câmp la ExtractedField (cu source_page din `pages`)
    - log_usage() pentru cost
    """
    raise NotImplementedError("Integrare LLM — de completat în sesiunea de implementare")
