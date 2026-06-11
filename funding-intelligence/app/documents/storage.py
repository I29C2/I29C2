"""Storage pe disc local — înlocuiește MinIO/S3 la MVP.

Layout: {STORAGE_DIR}/{sha256[:2]}/{sha256}/{filename}
Conținut adresat prin sha256 → deduplicare automată + versionare imuabilă.
La trecerea pe VPS cu utilizatori externi, se înlocuiește cu S3 fără a schimba
interfața (download/save).
"""

import hashlib
from pathlib import Path

from app.config import settings


def _root() -> Path:
    root = Path(settings.storage_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root


def compute_sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def save(content: bytes, filename: str) -> tuple[str, str]:
    """Salvează conținutul, întoarce (sha256, storage_key)."""
    digest = compute_sha256(content)
    target_dir = _root() / digest[:2] / digest
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / filename
    if not path.exists():
        path.write_bytes(content)
    storage_key = str(path.relative_to(_root()))
    return digest, storage_key


def load(storage_key: str) -> bytes:
    return (_root() / storage_key).read_bytes()


def absolute_path(storage_key: str) -> Path:
    """Pentru FileResponse / viewer PDF inline."""
    return _root() / storage_key
