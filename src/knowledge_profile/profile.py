"""Deterministic concept evidence from accepted public problem IDs."""

from dataclasses import asdict, dataclass
from math import exp

from src.data.models import TAXONOMY_VERSION, Problem
from src.data.solved import SolvedList, validate_solved_list


@dataclass(frozen=True)
class ConceptEvidence:
    concept_id: str
    status: str
    confidence: float
    problem_ids: tuple[int, ...]


@dataclass(frozen=True)
class KnowledgeProfile:
    username: str
    source: str
    collected_at: str
    taxonomy_version: str
    reported_solves: int
    mapped_solves: int
    unknown_problem_ids: tuple[int, ...]
    unmapped_problem_identifiers: tuple[str, ...]
    concepts: tuple[ConceptEvidence, ...]
    uncertainty: tuple[str, ...]


def build_profile(
    solved: SolvedList, catalog: tuple[Problem, ...], taxonomy_ids: frozenset[str]
) -> KnowledgeProfile:
    """Build transparent bounded evidence from recency, difficulty and frequency.

    Each mapped solve contributes a difficulty weight (Easy .40, Medium .50,
    Hard .60) multiplied by a recency factor in [0.5, 1]. Contributions combine
    as noisy-OR; status is covered only with >=2 solves and score >=.55. These
    are heuristic evidence scores, not calibrated mastery or solve probabilities.
    """
    validate_solved_list(solved)
    by_id = {problem.problem_id: problem for problem in catalog}
    if len(by_id) != len(catalog) or any(
        set(p.concepts) - taxonomy_ids for p in catalog
    ):
        raise ValueError("Invalid catalog for profile taxonomy")
    evidence: dict[str, list[tuple[int, int]]] = {
        concept: [] for concept in taxonomy_ids
    }
    unknown: list[int] = []
    ranks = solved.recency_ranks or tuple(range(len(solved.problem_ids)))
    difficulty_weight = {"Easy": 0.40, "Medium": 0.50, "Hard": 0.60}
    for problem_id, rank in zip(solved.problem_ids, ranks, strict=True):
        problem = by_id.get(problem_id)
        if problem is None:
            unknown.append(problem_id)
        else:
            for concept in problem.concepts:
                evidence[concept].append((problem_id, rank))
    rows = []
    for concept, items in sorted(evidence.items()):
        contributions = [
            difficulty_weight[by_id[problem_id].difficulty]
            * (0.5 + 0.5 * exp(-rank / 10))
            for problem_id, rank in items
        ]
        confidence = 1.0
        for contribution in contributions:
            confidence *= 1.0 - contribution
        confidence = round(1.0 - confidence, 4)
        ids = tuple(sorted(problem_id for problem_id, _ in items))
        status = (
            "covered"
            if len(items) >= 2 and confidence >= 0.55
            else "emerging"
            if items
            else "unobserved"
        )
        rows.append(ConceptEvidence(concept, status, confidence, ids))
    concepts = tuple(rows)
    uncertainty = [
        "Public accepted status shows a solve, not how independently it was completed.",
        "Confidence is a heuristic weighted by difficulty, recent-list order, and mapped solve count; it is not calibrated mastery.",
        "No observed solve is not evidence that a concept is unknown.",
    ]
    if unknown or solved.unmapped_ids:
        uncertainty.append("Some solved problems have no mapped catalog concepts.")
    if len(solved.problem_ids) + len(solved.unmapped_ids) < solved.total_reported:
        uncertainty.append(
            "Solved-list input is incomplete relative to its reported total."
        )
    return KnowledgeProfile(
        solved.username,
        solved.source,
        solved.collected_at,
        TAXONOMY_VERSION,
        solved.total_reported,
        len(solved.problem_ids) - len(unknown),
        tuple(sorted(unknown)),
        solved.unmapped_ids,
        concepts,
        tuple(uncertainty),
    )


def profile_dict(profile: KnowledgeProfile) -> dict:
    """JSON-ready representation for CLI and later API transport."""
    return asdict(profile)
