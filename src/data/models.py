"""Typed, dependency-free catalog records."""

from dataclasses import dataclass

CATALOG_VERSION = "mvp-1.0"
TAXONOMY_VERSION = "mvp-1"


@dataclass(frozen=True)
class ConceptMapping:
    problem_id: int
    concept_id: str
    reason: str


@dataclass(frozen=True)
class Problem:
    problem_id: int
    title: str
    difficulty: str
    tags: tuple[str, ...]
    concepts: tuple[str, ...]
    acceptance_rate: float | None
    source: str
    collected_at: str
    notes: str
