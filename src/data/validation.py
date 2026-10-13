"""Validation at the seed and catalog boundaries."""

import re
from datetime import date
from pathlib import Path
from typing import Iterable

from .models import Problem, TAXONOMY_VERSION


class CatalogValidationError(ValueError):
    """Catalog data violates the frozen MVP schema or taxonomy."""


def load_taxonomy_ids(path: Path) -> frozenset[str]:
    text = path.read_text(encoding="utf-8")
    if f"**Version:** `{TAXONOMY_VERSION}`" not in text:
        raise CatalogValidationError("Taxonomy version mismatch")
    ids = re.findall(r"^\| `([a-z][a-z0-9_]*)` \|", text, re.MULTILINE)
    if len(ids) != 28 or len(set(ids)) != len(ids):
        raise CatalogValidationError("Expected 28 unique taxonomy IDs")
    return frozenset(ids)


def validate_problem(problem: Problem, taxonomy_ids: frozenset[str]) -> None:
    if isinstance(problem.problem_id, bool) or not isinstance(problem.problem_id, int) or problem.problem_id <= 0:
        raise CatalogValidationError("problem_id must be a positive LeetCode number")
    if any(not isinstance(value, str) or not value.strip()
           for value in (problem.title, problem.source, problem.notes)):
        raise CatalogValidationError(f"Problem {problem.problem_id}: title, source, and notes are required")
    if problem.difficulty not in {"Easy", "Medium", "Hard"}:
        raise CatalogValidationError(f"Problem {problem.problem_id}: invalid difficulty")
    if not isinstance(problem.tags, tuple) or not problem.tags or any(
        not isinstance(tag, str) or not tag.strip() for tag in problem.tags
    ):
        raise CatalogValidationError(f"Problem {problem.problem_id}: tags are required")
    if not isinstance(problem.concepts, tuple) or not problem.concepts or any(
        not isinstance(concept, str) for concept in problem.concepts
    ) or len(set(problem.concepts)) != len(problem.concepts):
        raise CatalogValidationError(f"Problem {problem.problem_id}: concepts must be nonempty and unique")
    unknown = set(problem.concepts) - taxonomy_ids
    if unknown:
        raise CatalogValidationError(f"Problem {problem.problem_id}: unknown concepts {sorted(unknown)}")
    if problem.acceptance_rate is not None and (
        isinstance(problem.acceptance_rate, bool)
        or not isinstance(problem.acceptance_rate, (int, float))
        or not 0 <= problem.acceptance_rate <= 100
    ):
        raise CatalogValidationError(f"Problem {problem.problem_id}: invalid acceptance_rate")
    try:
        if not isinstance(problem.collected_at, str):
            raise ValueError("Expected ISO date string")
        date.fromisoformat(problem.collected_at)
    except ValueError as exc:
        raise CatalogValidationError(f"Problem {problem.problem_id}: invalid collected_at") from exc
    if problem.source != "LeetCode public problem page (manual curation)":
        raise CatalogValidationError(f"Problem {problem.problem_id}: unexpected source")


def validate_catalog(problems: Iterable[Problem], taxonomy_ids: frozenset[str]) -> tuple[Problem, ...]:
    result = tuple(problems)
    seen: set[int] = set()
    for problem in result:
        validate_problem(problem, taxonomy_ids)
        if problem.problem_id in seen:
            raise CatalogValidationError(f"Duplicate problem_id: {problem.problem_id}")
        seen.add(problem.problem_id)
    if not result:
        raise CatalogValidationError("Catalog is empty")
    return tuple(sorted(result, key=lambda problem: problem.problem_id))
