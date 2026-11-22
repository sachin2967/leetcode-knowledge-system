"""Portable text fingerprints for inputs shared between Windows and Linux."""

import hashlib
from pathlib import Path


def text_sha256(path: Path) -> str:
    """Normalize CRLF/CR through universal newline reading before hashing UTF-8."""
    return hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
