"""Profile evidence and public input boundary tests; no live requests."""

from dataclasses import replace
from pathlib import Path

import pytest

from src.data.catalog import read_json
from src.data.solved import (
    SolvedList,
    SolvedListError,
    fetch_public_solved,
    read_solved_fixture,
    validate_solved_list,
)
from src.data.validation import load_taxonomy_ids
from src.knowledge_profile.profile import build_profile

ROOT = Path(__file__).resolve().parents[1]
TAXONOMY = load_taxonomy_ids(ROOT / "docs/CONCEPT_TAXONOMY.md")
CATALOG = read_json(ROOT / "data/sample/catalog_mvp-1.0.json", TAXONOMY)


def test_demo_profile_has_traceable_evidence_and_uncertainty() -> None:
    solved = read_solved_fixture(ROOT / "data/sample/demo_solved_mvp-1.json")
    profile = build_profile(solved, CATALOG, TAXONOMY)
    concepts = {item.concept_id: item for item in profile.concepts}
    assert profile.mapped_solves == 12
    assert concepts["arrays_hashing"].status == "covered"
    assert concepts["arrays_hashing"].problem_ids == (1, 217)
    assert concepts["graph_traversal"].status == "emerging"
    assert concepts["graph_traversal"].problem_ids == (200,)
    assert concepts["digit_dp"].status == "unobserved"
    assert len(concepts) == 28
    assert any("not evidence" in note for note in profile.uncertainty)


def test_unknown_and_nonnumeric_ids_are_reported_without_invented_evidence() -> None:
    solved = SolvedList(
        "learner", (1, 999999), "public test", "2026-10-14", 3, ("LCR 001",)
    )
    profile = build_profile(solved, CATALOG, TAXONOMY)
    assert profile.mapped_solves == 1
    assert profile.unknown_problem_ids == (999999,)
    assert profile.unmapped_problem_identifiers == ("LCR 001",)
    assert any("no mapped catalog" in note for note in profile.uncertainty)


def test_empty_history_is_unobserved_not_failed() -> None:
    profile = build_profile(
        SolvedList("new_user", (), "public test", "2026-10-14", 0), CATALOG, TAXONOMY
    )
    assert all(item.status == "unobserved" for item in profile.concepts)
    assert profile.mapped_solves == 0


@pytest.mark.parametrize(
    "change",
    [
        {"username": "bad user"},
        {"problem_ids": (1, 1)},
        {"problem_ids": (True,)},
        {"total_reported": -1},
        {"collected_at": "yesterday"},
    ],
)
def test_invalid_solved_lists_rejected(change: dict) -> None:
    solved = SolvedList("learner", (1,), "public test", "2026-10-14", 2)
    with pytest.raises(SolvedListError):
        validate_solved_list(replace(solved, **change))


def test_public_fetch_maps_recent_slugs_and_reports_partial_history() -> None:
    def post(payload: dict) -> dict:
        assert payload["variables"] == {"username": "learner", "limit": 20}
        return {
            "data": {
                "matchedUser": {
                    "submitStats": {
                        "acSubmissionNum": [{"difficulty": "All", "count": 8}]
                    }
                },
                "recentAcSubmissionList": [
                    {"titleSlug": "two-sum"},
                    {"titleSlug": "contains-duplicate"},
                    {"titleSlug": "two-sum"},
                    {"titleSlug": "unknown-problem"},
                ],
            }
        }

    solved = fetch_public_solved(
        "learner", CATALOG, post=post, collected_at="2026-10-14"
    )
    assert solved.problem_ids == (1, 217)
    assert solved.recency_ranks == (0, 1)
    assert solved.unmapped_ids == ("unknown-problem",)
    profile = build_profile(solved, CATALOG, TAXONOMY)
    assert any("incomplete" in note for note in profile.uncertainty)


def test_profile_confidence_uses_difficulty_recent_order_and_frequency() -> None:
    easy = build_profile(
        SolvedList("learner", (1,), "test", "2026-10-14", 1), CATALOG, TAXONOMY
    )
    medium = build_profile(
        SolvedList("learner", (3,), "test", "2026-10-14", 1), CATALOG, TAXONOMY
    )
    older = build_profile(
        SolvedList("learner", (3,), "test", "2026-10-14", 1, (), (10,)),
        CATALOG,
        TAXONOMY,
    )
    get_score = lambda profile: next(
        item.confidence
        for item in profile.concepts
        if item.concept_id == "arrays_hashing"
    )
    assert get_score(medium) > get_score(easy)
    assert get_score(medium) > get_score(older)
    frequent = build_profile(
        SolvedList("learner", (1, 217), "test", "2026-10-14", 2), CATALOG, TAXONOMY
    )
    evidence = next(
        item for item in frequent.concepts if item.concept_id == "arrays_hashing"
    )
    assert evidence.status == "covered" and evidence.confidence > get_score(medium)


@pytest.mark.parametrize(
    "response",
    [
        {"errors": [{"message": "rate limited"}]},
        {"data": {"matchedUser": None, "recentAcSubmissionList": []}},
        {
            "data": {
                "matchedUser": {"submitStats": {"acSubmissionNum": []}},
                "recentAcSubmissionList": [],
            }
        },
    ],
)
def test_public_fetch_rejects_unavailable_or_partial_data(response: dict) -> None:
    with pytest.raises(SolvedListError):
        fetch_public_solved("learner", CATALOG, post=lambda _: response)
