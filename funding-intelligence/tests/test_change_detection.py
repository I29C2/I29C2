"""Change detection — cazul critic: schimbările cosmetice NU declanșează diff.

Acesta e testul care apără credibilitatea notificărilor (vezi feedback-ul pe document).
"""

from app.scraping.base import RawCallData
from app.scraping.change_detection import diff_fields, field_hashes


def _call(**kw) -> RawCallData:
    base = dict(
        source_id="example",
        external_id="A1",
        title="Apel digitalizare IMM",
        url_official="https://example.gov.ro/a1",
    )
    base.update(kw)
    return RawCallData(**base)


def test_cosmetic_change_does_not_trigger_diff() -> None:
    old = field_hashes(_call(title="Apel digitalizare IMM"))
    # Spații în plus + altă capitalizare = aceeași informație.
    new = field_hashes(_call(title="  apel   DIGITALIZARE  imm "))
    assert diff_fields(old, new) == []


def test_real_change_triggers_diff() -> None:
    old = field_hashes(_call(title="Apel digitalizare IMM"))
    new = field_hashes(_call(title="Apel digitalizare ONG"))
    assert "title" in diff_fields(old, new)
