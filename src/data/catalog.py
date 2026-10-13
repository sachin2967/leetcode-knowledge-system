"""Read and write deterministic JSON and SQLite catalog snapshots."""

import csv
import json
import sqlite3
from dataclasses import asdict
from pathlib import Path

from .models import CATALOG_VERSION, TAXONOMY_VERSION, ConceptMapping, Problem
from .validation import CatalogValidationError, validate_catalog


SOURCE = "LeetCode public problem page (manual curation)"
FIELDS = frozenset(Problem.__dataclass_fields__)


def _problem_from_dict(data: dict) -> Problem:
    if not isinstance(data, dict):
        raise CatalogValidationError("Problem must be an object")
    missing = FIELDS - data.keys()
    extra = data.keys() - FIELDS
    if missing or extra:
        raise CatalogValidationError(f"Problem fields mismatch: missing={sorted(missing)}, extra={sorted(extra)}")
    if not isinstance(data["tags"], list) or not isinstance(data["concepts"], list):
        raise CatalogValidationError("Tags and concepts must be lists")
    return Problem(**{**data, "tags": tuple(data["tags"]), "concepts": tuple(data["concepts"])})


def load_seed(path: Path, taxonomy_ids: frozenset[str]) -> tuple[Problem, ...]:
    """Read a manually curated pipe-delimited seed; no network access."""
    problems = []
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="|")
        required = {"problem_id", "title", "difficulty", "tags", "concepts", "notes"}
        if not reader.fieldnames or set(reader.fieldnames) != required:
            raise CatalogValidationError("Seed columns mismatch")
        for line, row in enumerate(reader, start=2):
            try:
                problems.append(Problem(
                    problem_id=int(row["problem_id"]),
                    title=row["title"], difficulty=row["difficulty"],
                    tags=tuple(row["tags"].split(";")),
                    concepts=tuple(row["concepts"].split(";")),
                    acceptance_rate=None, source=SOURCE, collected_at="2026-10-14",
                    notes=row["notes"],
                ))
            except (TypeError, ValueError, AttributeError) as exc:
                raise CatalogValidationError(f"Invalid seed row {line}") from exc
    return validate_catalog(problems, taxonomy_ids)


def mappings_for(problem: Problem) -> tuple[ConceptMapping, ...]:
    return tuple(ConceptMapping(problem.problem_id, concept, problem.notes) for concept in problem.concepts)


def write_json(path: Path, problems: tuple[Problem, ...], taxonomy_ids: frozenset[str]) -> None:
    problems = validate_catalog(problems, taxonomy_ids)
    payload = {"catalog_version": CATALOG_VERSION, "taxonomy_version": TAXONOMY_VERSION,
               "problems": [asdict(problem) for problem in problems]}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_json(path: Path, taxonomy_ids: frozenset[str]) -> tuple[Problem, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if set(payload) != {"catalog_version", "taxonomy_version", "problems"} or (
        payload["catalog_version"] != CATALOG_VERSION or payload["taxonomy_version"] != TAXONOMY_VERSION
    ):
        raise CatalogValidationError("Catalog or taxonomy version mismatch")
    return validate_catalog((_problem_from_dict(row) for row in payload["problems"]), taxonomy_ids)


def write_sqlite(path: Path, problems: tuple[Problem, ...], taxonomy_ids: frozenset[str]) -> None:
    problems = validate_catalog(problems, taxonomy_ids)
    path.parent.mkdir(parents=True, exist_ok=True)
    # A rebuild replaces a snapshot. Never use this path for user imports.
    with sqlite3.connect(path) as db:
        db.executescript("""
            DROP TABLE IF EXISTS concept_mappings;
            DROP TABLE IF EXISTS problems;
            DROP TABLE IF EXISTS metadata;
            CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE problems (
                problem_id INTEGER PRIMARY KEY, title TEXT NOT NULL, difficulty TEXT NOT NULL,
                tags TEXT NOT NULL, acceptance_rate REAL, source TEXT NOT NULL,
                collected_at TEXT NOT NULL, notes TEXT NOT NULL
            );
            CREATE TABLE concept_mappings (
                problem_id INTEGER NOT NULL REFERENCES problems(problem_id),
                concept_id TEXT NOT NULL, reason TEXT NOT NULL,
                PRIMARY KEY (problem_id, concept_id)
            );
        """)
        db.executemany("INSERT INTO metadata VALUES (?, ?)",
                       [("catalog_version", CATALOG_VERSION), ("taxonomy_version", TAXONOMY_VERSION)])
        db.executemany("INSERT INTO problems VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [
            (p.problem_id, p.title, p.difficulty, json.dumps(p.tags), p.acceptance_rate,
             p.source, p.collected_at, p.notes) for p in problems
        ])
        db.executemany("INSERT INTO concept_mappings VALUES (?, ?, ?)", [
            (m.problem_id, m.concept_id, m.reason) for p in problems for m in mappings_for(p)
        ])


def read_sqlite(path: Path, taxonomy_ids: frozenset[str]) -> tuple[Problem, ...]:
    with sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True) as db:
        metadata = dict(db.execute("SELECT key, value FROM metadata"))
        if metadata != {"catalog_version": CATALOG_VERSION, "taxonomy_version": TAXONOMY_VERSION}:
            raise CatalogValidationError("Catalog or taxonomy version mismatch")
        rows = db.execute("SELECT problem_id, title, difficulty, tags, acceptance_rate, source, collected_at, notes FROM problems ORDER BY problem_id").fetchall()
        mapping_rows = db.execute("SELECT problem_id, concept_id, reason FROM concept_mappings ORDER BY rowid").fetchall()
    concepts: dict[int, list[str]] = {}
    for problem_id, concept_id, reason in mapping_rows:
        if not reason.strip():
            raise CatalogValidationError(f"Problem {problem_id}: missing mapping reason")
        concepts.setdefault(problem_id, []).append(concept_id)
    return validate_catalog((Problem(id_, title, difficulty, tuple(json.loads(tags)),
                                     tuple(concepts.get(id_, [])), rate, source, date_, notes)
                             for id_, title, difficulty, tags, rate, source, date_, notes in rows), taxonomy_ids)
