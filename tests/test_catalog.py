"""Local contract tests for curated catalog validation and storage."""

import json
import sqlite3
from dataclasses import replace
from pathlib import Path

import pytest

from src.data.catalog import load_seed, read_json, read_sqlite, write_json, write_sqlite
from src.data.validation import (
    CatalogValidationError,
    load_taxonomy_ids,
    validate_catalog,
    validate_problem,
)

ROOT = Path(__file__).resolve().parents[1]
TAXONOMY = load_taxonomy_ids(ROOT / "docs/CONCEPT_TAXONOMY.md")


@pytest.fixture(scope="module")
def problems():
    return load_seed(ROOT / "data/sample/problems_seed.psv", TAXONOMY)


def test_seed_size_coverage_and_known_mappings(problems) -> None:
    assert 80 <= len(problems) <= 120
    assert set().union(*(p.concepts for p in problems)) == TAXONOMY
    by_id = {p.problem_id: p for p in problems}
    assert by_id[1].title == "Two Sum"
    assert by_id[1].concepts == ("arrays_hashing",)
    assert by_id[20].concepts == ("stack",)
    assert by_id[146].concepts == ("arrays_hashing", "linked_lists")
    assert by_id[200].concepts == ("graph_traversal",)
    assert by_id[322].concepts == ("knapsack_dp", "dynamic_programming")
    assert by_id[2276].concepts == ("segment_tree", "lazy_propagation", "intervals")


@pytest.mark.parametrize(
    "changes",
    [
        {"problem_id": 0},
        {"title": ""},
        {"difficulty": "Expert"},
        {"tags": ()},
        {"concepts": ("unknown_id",)},
        {"source": ""},
        {"collected_at": "yesterday"},
        {"acceptance_rate": 101.0},
        {"notes": ""},
    ],
)
def test_invalid_problem_fields_rejected(problems, changes) -> None:
    with pytest.raises(CatalogValidationError):
        validate_problem(replace(problems[0], **changes), TAXONOMY)


def test_duplicate_id_rejected(problems) -> None:
    with pytest.raises(CatalogValidationError, match="Duplicate problem_id"):
        validate_catalog((problems[0], problems[0]), TAXONOMY)


def test_json_and_sqlite_round_trip(tmp_path: Path, problems) -> None:
    json_path = tmp_path / "catalog.json"
    sqlite_path = tmp_path / "catalog.sqlite3"
    write_json(json_path, problems, TAXONOMY)
    write_sqlite(sqlite_path, problems, TAXONOMY)
    assert read_json(json_path, TAXONOMY) == problems
    assert read_sqlite(sqlite_path, TAXONOMY) == problems
    first_snapshot = sqlite_path.read_bytes()
    write_sqlite(sqlite_path, problems, TAXONOMY)
    assert sqlite_path.read_bytes() == first_snapshot
    with sqlite3.connect(sqlite_path) as db:
        reason = db.execute(
            "SELECT reason FROM concept_mappings WHERE problem_id=1"
        ).fetchone()[0]
    assert "complement" in reason


def test_committed_catalog_exports_match_seed(problems) -> None:
    sample = ROOT / "data/sample"
    assert read_json(sample / "catalog_mvp-1.0.json", TAXONOMY) == problems
    assert read_sqlite(sample / "catalog_mvp-1.0.sqlite3", TAXONOMY) == problems


def test_json_rejects_missing_fields_and_wrong_version(
    tmp_path: Path, problems
) -> None:
    path = tmp_path / "catalog.json"
    write_json(path, problems, TAXONOMY)
    payload = json.loads(path.read_text(encoding="utf-8"))
    del payload["problems"][0]["source"]
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(CatalogValidationError, match="missing"):
        read_json(path, TAXONOMY)
    payload["catalog_version"] = "mvp-2.0"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(CatalogValidationError, match="version"):
        read_json(path, TAXONOMY)


def test_seed_rejects_unknown_concept(tmp_path: Path) -> None:
    path = tmp_path / "seed.psv"
    path.write_text(
        "problem_id|title|difficulty|tags|concepts|notes\n"
        "1|Two Sum|Easy|Array|made_up|Unknown mapping\n",
        encoding="utf-8",
    )
    with pytest.raises(CatalogValidationError, match="unknown concepts"):
        load_seed(path, TAXONOMY)
