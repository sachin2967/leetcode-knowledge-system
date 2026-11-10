"""Explainable prerequisite coverage and gap-closing practice paths."""

from dataclasses import dataclass

from src.data.models import Problem
from src.knowledge_profile.profile import KnowledgeProfile
from src.ranking.ranker import Recommendation, practice_path


# Compact, reviewed MVP mapping. Entries are prerequisite concepts required by
# these target problem IDs; it is intentionally not a universal concept graph.
PREREQUISITES: dict[int, tuple[str, ...]] = {
    23: ("linked_lists",),
    42: ("arrays_hashing", "two_pointers", "stack"),
    76: ("arrays_hashing", "sliding_window"),
    127: ("arrays_hashing", "graph_traversal"),
    239: ("arrays_hashing", "sliding_window", "heap_priority_queue"),
    297: ("tree_traversal",),
    312: ("dynamic_programming", "interval_dp"),
    315: ("arrays_hashing", "sorting", "binary_search"),
    332: ("graph_traversal", "heap_priority_queue"),
    480: ("arrays_hashing", "sliding_window", "heap_priority_queue"),
}


@dataclass(frozen=True)
class ConceptReadiness:
    concept_id: str
    status: str
    confidence: float
    evidence_problem_ids: tuple[int, ...]
    explanation: str


@dataclass(frozen=True)
class Diagnosis:
    target_problem_id: int
    target_title: str
    readiness: str
    taxonomy_version: str
    concepts: tuple[ConceptReadiness, ...]
    missing_concepts: tuple[str, ...]
    explanation: str
    practice_path: tuple[Recommendation, ...]
    uncertainty: tuple[str, ...]


def diagnose_target(target: Problem, profile: KnowledgeProfile,
                    catalog: tuple[Problem, ...], taxonomy_ids: frozenset[str],
                    *, path_limit: int = 10) -> Diagnosis:
    """Compare a target's curated prerequisites with observed profile evidence.

    Only `covered` evidence counts toward Ready. Emerging evidence is shown but
    remains a gap; absent evidence means unobserved, never inability.
    """
    required = PREREQUISITES.get(target.problem_id, target.concepts)
    if not required or set(required) - taxonomy_ids:
        raise ValueError(f"No valid prerequisite mapping for target {target.problem_id}")
    if target.problem_id not in {problem.problem_id for problem in catalog}:
        raise ValueError("Target must belong to the supplied catalog")
    evidence = {item.concept_id: item for item in profile.concepts}
    if set(required) - taxonomy_ids or set(evidence) - taxonomy_ids:
        raise ValueError("Profile or prerequisite mapping contains unknown concepts")
    rows = []
    missing = []
    for concept in required:
        item = evidence.get(concept)
        status = item.status if item else "unobserved"
        confidence = item.confidence if item else 0.0
        ids = item.problem_ids if item else ()
        is_covered = status == "covered"
        if not is_covered:
            missing.append(concept)
        explanation = (f"Covered by {len(ids)} solved catalog problem(s)." if is_covered else
                       f"{status.capitalize()} evidence from {len(ids)} solved catalog problem(s); coverage threshold is not met.")
        rows.append(ConceptReadiness(concept, status, confidence, ids, explanation))
    ordered_missing = tuple(missing)
    path = practice_path(catalog, ordered_missing, limit=path_limit) if ordered_missing else ()
    ready = not ordered_missing
    return Diagnosis(target.problem_id, target.title, "Ready" if ready else "Not ready",
                     profile.taxonomy_version, tuple(rows), ordered_missing,
                     "All curated prerequisites meet the covered evidence threshold." if ready else
                     "Practice the listed gaps; missing evidence is not evidence of inability.",
                     path, profile.uncertainty)
