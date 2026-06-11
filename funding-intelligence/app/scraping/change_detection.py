"""Change detection: normalizare → hash per câmp → diff → versiune nouă.

PARTEA GREA (Ghid Tehnic, feedback): NORMALIZAREA. Schimbări cosmetice
(whitespace, reordonări, markup) NU trebuie să producă evenimente `call.changed`
false — altfel notificările își pierd credibilitatea. Vezi tests/test_change_detection.py.
"""

import hashlib
from dataclasses import asdict

from app.scraping.base import RawCallData

# Câmpurile semnificative pentru diff. Restul (raw_fields) nu declanșează „modificat".
SIGNIFICANT_FIELDS = (
    "title",
    "program",
    "axis",
    "status",
    "budget_total",
    "deadline_submission",
    "url_official",
)


def _normalize(value: object) -> str:
    """Normalizare anti-zgomot: trim, spații colapsate, lowercase pe text liber.

    TODO: extinde cu reguli per câmp (date → ISO, sume → fără separatori de mii etc.).
    """
    if value is None:
        return ""
    s = str(value).strip().lower()
    return " ".join(s.split())


def field_hashes(data: RawCallData) -> dict[str, str]:
    """Hash per câmp semnificativ, după normalizare."""
    d = asdict(data)
    out: dict[str, str] = {}
    for f in SIGNIFICANT_FIELDS:
        norm = _normalize(d.get(f))
        out[f] = hashlib.sha256(norm.encode("utf-8")).hexdigest()
    return out


def diff_fields(old: dict[str, str], new: dict[str, str]) -> list[str]:
    """Câmpurile efectiv schimbate între două seturi de hash-uri."""
    changed = []
    for f in SIGNIFICANT_FIELDS:
        if old.get(f) != new.get(f):
            changed.append(f)
    return changed
