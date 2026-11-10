"""Deterministic, explainable catalog ranking and practice-path helpers."""

from dataclasses import dataclass
import re

from src.data.models import Problem
from src.knowledge_profile.profile import KnowledgeProfile


@dataclass(frozen=True)
class Recommendation:
    problem_id: int
    title: str
    difficulty: str
    score: float
    relevant_concepts: tuple[str, ...]
    reason: str


_TOKEN = re.compile(r"[a-z0-9]+")


def _tokens(value: str) -> set[str]:
    return set(_TOKEN.findall(value.lower()))


def tag_overlap_score(problem: Problem, query: str) -> float:
    """Simple lexical tag/title overlap baseline."""
    query_terms = _tokens(query)
    item_terms = set().union(*(_tokens(tag) for tag in problem.tags), _tokens(problem.title))
    return len(query_terms & item_terms) / max(1, len(query_terms))


def popularity_score(problem: Problem, _: str = "") -> float:
    """Acceptance-rate baseline; unavailable rates deterministically score zero."""
    return problem.acceptance_rate or 0.0


def rank_problems(problems: tuple[Problem, ...], query: str, *, concepts: tuple[str, ...] = (),
                  difficulty: str | None = None, profile: KnowledgeProfile | None = None,
                  limit: int = 10) -> tuple[Recommendation, ...]:
    """Rank by explicit concept match, query overlap, and optional learning need.

    Catalog acceptance rates are currently null, so popularity is not used as a
    hidden tie-breaker. Scores are ordering signals, not solve probabilities.
    """
    if limit < 1:
        raise ValueError("limit must be positive")
    target = set(concepts)
    covered = {item.concept_id for item in profile.concepts if item.status == "covered"} if profile else set()
    emerging = {item.concept_id for item in profile.concepts if item.status == "emerging"} if profile else set()
    rows = []
    for problem in problems:
        overlap = tuple(sorted(target.intersection(problem.concepts)))
        lexical = tag_overlap_score(problem, query)
        difficulty_fit = 1.0 if difficulty is None or problem.difficulty == difficulty else 0.0
        need = len(set(problem.concepts) & (emerging | target)) - len(set(problem.concepts) & covered)
        score = 3.0 * len(overlap) + lexical + 0.5 * difficulty_fit + 0.1 * max(0, need)
        if not overlap and not lexical:
            continue
        reasons = []
        if overlap:
            reasons.append("matches " + ", ".join(overlap))
        if difficulty_fit and difficulty:
            reasons.append(f"fits requested {difficulty} difficulty")
        elif lexical:
            reasons.append("matches query terms in title or tags")
        if profile and set(problem.concepts) & (emerging | target) - covered:
            reasons.append("supports concepts with emerging or requested evidence")
        rows.append(Recommendation(problem.problem_id, problem.title, problem.difficulty,
                                   score, overlap, "; ".join(reasons) or "catalog match"))
    return tuple(sorted(rows, key=lambda item: (-item.score, item.problem_id))[:limit])


def practice_path(problems: tuple[Problem, ...], concepts: tuple[str, ...], *,
                  difficulty_order: tuple[str, ...] = ("Easy", "Medium", "Hard"),
                  limit: int = 10) -> tuple[Recommendation, ...]:
    """Return relevant problems in a stable easier-to-harder learning sequence."""
    order = {value: index for index, value in enumerate(difficulty_order)}
    matching = [p for p in problems if set(p.concepts) & set(concepts)]
    matching.sort(key=lambda p: (order.get(p.difficulty, len(order)), p.problem_id))
    result = []
    for problem in matching[:limit]:
        overlap = tuple(sorted(set(problem.concepts) & set(concepts)))
        result.append(Recommendation(problem.problem_id, problem.title, problem.difficulty,
                                     float(len(overlap)), overlap,
                                     f"{problem.difficulty} practice for {', '.join(overlap)}"))
    return tuple(result)
