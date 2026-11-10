"""Local diagnosis and private-code isolation tests; all snippets are synthetic."""

import json
from pathlib import Path

import pytest

from src.data.catalog import read_json
from src.data.personal_code import PersonalCodeError, import_accepted_code, retrieve_templates
from src.data.solved import SolvedList
from src.data.validation import load_taxonomy_ids
from src.knowledge_profile.diagnosis import diagnose_target
from src.knowledge_profile.profile import build_profile


ROOT = Path(__file__).resolve().parents[1]
TAXONOMY = load_taxonomy_ids(ROOT / "docs/CONCEPT_TAXONOMY.md")
CATALOG = read_json(ROOT / "data/sample/catalog_mvp-1.0.json", TAXONOMY)


def test_diagnosis_explains_covered_and_missing_then_orders_gap_path() -> None:
    profile = build_profile(SolvedList("demo", (1, 217), "test", "2026-10-14", 2), CATALOG, TAXONOMY)
    target = next(problem for problem in CATALOG if problem.problem_id == 76)
    result = diagnose_target(target, profile, CATALOG, TAXONOMY)
    rows = {row.concept_id: row for row in result.concepts}
    assert result.readiness == "Not ready"
    assert rows["arrays_hashing"].status == "covered"
    assert rows["sliding_window"].status == "unobserved"
    assert result.missing_concepts == ("sliding_window",)
    assert result.practice_path
    assert all("sliding_window" in item.relevant_concepts for item in result.practice_path)
    assert "not evidence of inability" in result.explanation


def test_diagnosis_ready_requires_covered_threshold() -> None:
    ids = tuple(p.problem_id for p in CATALOG if "sliding_window" in p.concepts)
    profile = build_profile(SolvedList("demo", ids, "test", "2026-10-14", len(ids)), CATALOG, TAXONOMY)
    result = diagnose_target(next(p for p in CATALOG if p.problem_id == 76), profile, CATALOG, TAXONOMY)
    assert result.readiness == "Ready"
    assert result.missing_concepts == ()
    assert result.practice_path == ()


def test_personal_import_requires_opt_in_and_isolated_by_owner(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    source = raw / "synthetic.json"
    source.write_text(json.dumps([{"owner": "alice", "problem_id": 1, "title": "Two Sum",
                                   "language": "Python", "accepted": True,
                                   "code": "def twoSum(): return {}"}]), encoding="utf-8")
    with pytest.raises(PersonalCodeError):
        import_accepted_code("alice", source, tmp_path)
    assert import_accepted_code("alice", source, tmp_path, owner_authorized=True) == 1
    own = retrieve_templates("ALICE", "arrays_hashing", CATALOG, tmp_path, taxonomy_ids=TAXONOMY)
    other = retrieve_templates("bob", "arrays_hashing", CATALOG, tmp_path, taxonomy_ids=TAXONOMY)
    assert own.status == "available" and own.snippets[0].owner == "alice"
    assert other.status == "unavailable" and not other.snippets


def test_personal_import_rejects_other_owner_and_non_raw_source(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    source = raw / "private.json"
    source.write_text(json.dumps([{"owner": "someone-else", "problem_id": 1, "title": "Two Sum",
                                   "language": "Python", "accepted": True, "code": "private"}]), encoding="utf-8")
    with pytest.raises(PersonalCodeError):
        import_accepted_code("alice", source, tmp_path, owner_authorized=True)
    outside = tmp_path / "outside.json"
    outside.write_text("[]", encoding="utf-8")
    with pytest.raises(PersonalCodeError):
        import_accepted_code("alice", outside, tmp_path, owner_authorized=True)


def test_existing_owner_corpus_has_clear_empty_state(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    source = raw / "empty.json"
    source.write_text("[]", encoding="utf-8")
    import_accepted_code("alice", source, tmp_path, owner_authorized=True)
    result = retrieve_templates("alice", "arrays_hashing", CATALOG, tmp_path, taxonomy_ids=TAXONOMY)
    assert result.status == "empty"
