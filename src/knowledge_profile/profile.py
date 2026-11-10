"""Deterministic concept evidence from accepted public problem IDs."""

from dataclasses import asdict, dataclass

from src.data.models import Problem, TAXONOMY_VERSION
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


def build_profile(solved: SolvedList, catalog: tuple[Problem, ...],
                  taxonomy_ids: frozenset[str]) -> KnowledgeProfile:
    """Two distinct mapped solves establish coverage; one is emerging evidence.

    Scores are evidence levels (0, 0.5, 1), not probabilities. A problem with
    multiple curated concepts supports each label; solve count says nothing about
    independent mastery. Unknown IDs and unsolved concepts never imply inability.
    """
    validate_solved_list(solved)
    by_id = {problem.problem_id: problem for problem in catalog}
    if len(by_id) != len(catalog) or any(set(p.concepts) - taxonomy_ids for p in catalog):
        raise ValueError("Invalid catalog for profile taxonomy")
    evidence: dict[str, list[int]] = {concept: [] for concept in taxonomy_ids}
    unknown: list[int] = []
    for problem_id in solved.problem_ids:
        problem = by_id.get(problem_id)
        if problem is None:
            unknown.append(problem_id)
        else:
            for concept in problem.concepts:
                evidence[concept].append(problem_id)
    concepts = tuple(ConceptEvidence(concept, "covered" if len(ids) >= 2 else
                                     "emerging" if ids else "unobserved",
                                     1.0 if len(ids) >= 2 else 0.5 if ids else 0.0,
                                     tuple(sorted(ids))) for concept, ids in sorted(evidence.items()))
    uncertainty = ["Public accepted status shows a solve, not how independently it was completed.",
                   "No observed solve is not evidence that a concept is unknown."]
    if unknown or solved.unmapped_ids:
        uncertainty.append("Some solved problems have no mapped catalog concepts.")
    if len(solved.problem_ids) + len(solved.unmapped_ids) < solved.total_reported:
        uncertainty.append("Solved-list input is incomplete relative to its reported total.")
    return KnowledgeProfile(solved.username, solved.source, solved.collected_at,
                            TAXONOMY_VERSION, solved.total_reported,
                            len(solved.problem_ids) - len(unknown), tuple(sorted(unknown)),
                            solved.unmapped_ids, concepts, tuple(uncertainty))


def profile_dict(profile: KnowledgeProfile) -> dict:
    """JSON-ready representation for CLI and later API transport."""
    return asdict(profile)
