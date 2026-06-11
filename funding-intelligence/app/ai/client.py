"""Client LLM (Anthropic). Singurul loc care vorbește cu API-ul.

Reguli (Ghid Tehnic §3.3, §6.5):
- structured output (JSON schema = schema canonică)
- conținutul documentelor e UNTRUSTED — se delimitează clar de instrucțiunile de
  sistem (prompt injection prin PDF e un vector real). Vezi extraction.py.
- logging cost per request (tokens, model, modul apelant) — bugetul din ziua 1.
"""

import logging

from anthropic import Anthropic

from app.config import settings

logger = logging.getLogger(__name__)

_client: Anthropic | None = None


def get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic(api_key=settings.anthropic_api_key)
    return _client


def log_usage(model: str, caller: str, input_tokens: int, output_tokens: int) -> None:
    """Loghează costul. TODO: scrie într-un tabel dedicat (llm_usage) pentru raportare."""
    logger.info(
        "llm_usage model=%s caller=%s in=%d out=%d",
        model,
        caller,
        input_tokens,
        output_tokens,
    )
