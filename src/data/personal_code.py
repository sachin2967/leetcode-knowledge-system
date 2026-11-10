"""Opt-in, owner-scoped local accepted-submission import and retrieval."""

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from src.data.models import Problem


_USER = re.compile(r"[A-Za-z0-9_-]{1,30}\Z")
_FIELDS = {"owner", "problem_id", "title", "language", "accepted", "code"}


class PersonalCodeError(ValueError):
    """Unsafe, malformed, or unauthorized personal-code operation."""


@dataclass(frozen=True)
class TemplateSnippet:
    owner: str
    problem_id: int
    title: str
    language: str
    code: str


@dataclass(frozen=True)
class TemplateSearch:
    status: str  # unavailable, empty, or available
    snippets: tuple[TemplateSnippet, ...]


def _key(owner: str) -> str:
    if not isinstance(owner, str) or not _USER.fullmatch(owner):
        raise PersonalCodeError("Invalid corpus owner")
    return hashlib.sha256(owner.casefold().encode("utf-8")).hexdigest()


def import_accepted_code(owner: str, source: Path, data_root: Path, *,
                         owner_authorized: bool = False) -> int:
    """Import a JSON array of accepted snippets; explicit owner opt-in required.

    Source must be under data/raw. Private imports are stored beneath a hashed,
    per-owner directory and remain gitignored. This is local authorization, not
    a substitute for authentication in any hosted deployment.
    """
    if owner_authorized is not True:
        raise PersonalCodeError("Owner authorization is required for import")
    owner_key = _key(owner)
    raw_root = (data_root / "raw").resolve()
    source = source.resolve()
    if not source.is_relative_to(raw_root):
        raise PersonalCodeError("Personal code source must be inside data/raw")
    try:
        rows = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PersonalCodeError("Cannot read personal code import") from exc
    if not isinstance(rows, list):
        raise PersonalCodeError("Import must be a JSON array")
    clean = []
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != _FIELDS:
            raise PersonalCodeError("Snippet fields mismatch")
        if (not isinstance(row["owner"], str) or row["owner"].casefold() != owner.casefold()
                or row["accepted"] is not True or isinstance(row["problem_id"], bool)
                or not isinstance(row["problem_id"], int) or row["problem_id"] <= 0
                or not isinstance(row["title"], str) or not row["title"].strip()
                or not isinstance(row["language"], str) or not row["language"].strip()
                or not isinstance(row["code"], str) or not row["code"].strip()):
            raise PersonalCodeError("Only complete, owner-matched accepted snippets can be imported")
        marker = (row["problem_id"], row["language"].casefold())
        if marker in seen:
            raise PersonalCodeError("Duplicate problem/language snippet")
        seen.add(marker)
        clean.append({"owner": owner, "problem_id": row["problem_id"], "title": row["title"].strip(),
                      "language": row["language"].strip(), "accepted": True, "code": row["code"]})
    destination = data_root / "raw" / "personal_corpora" / owner_key / "accepted.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = destination.with_suffix(".tmp")
    temp.write_text(json.dumps(clean, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(destination)
    return len(clean)


def retrieve_templates(owner: str, query: str, catalog: tuple[Problem, ...],
                       data_root: Path, *, taxonomy_ids: frozenset[str]) -> TemplateSearch:
    """Retrieve only from this owner's corpus by locked concept IDs or title/tags."""
    path = data_root / "raw" / "personal_corpora" / _key(owner) / "accepted.json"
    if not path.exists():
        return TemplateSearch("unavailable", ())
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PersonalCodeError("Stored personal corpus is unreadable") from exc
    if not rows:
        return TemplateSearch("empty", ())
    terms = set(re.findall(r"[a-z0-9_]+", query.casefold()))
    by_id = {problem.problem_id: problem for problem in catalog}
    if any(set(problem.concepts) - taxonomy_ids for problem in catalog):
        raise PersonalCodeError("Catalog contains concepts outside the locked taxonomy")
    matches = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != _FIELDS or row.get("accepted") is not True:
            raise PersonalCodeError("Stored corpus failed validation")
        if row.get("owner", "").casefold() != owner.casefold():
            raise PersonalCodeError("Stored corpus owner mismatch")
        problem = by_id.get(row.get("problem_id"))
        corpus_terms = set()
        if problem:
            corpus_terms.update(re.findall(r"[a-z0-9_]+", (problem.title + " " + " ".join(problem.tags)).casefold()))
            corpus_terms.update(problem.concepts)
        if terms and terms & (corpus_terms | set(row["title"].casefold().split())):
            matches.append(TemplateSnippet(row["owner"], row["problem_id"], row["title"], row["language"], row["code"]))
    return TemplateSearch("available" if matches else "no_matches", tuple(matches))
