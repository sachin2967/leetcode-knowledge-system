"""Transport journeys use local fixtures, mocked public I/O, and synthetic code."""

import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.data.solved import SolvedList, SolvedListError


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def local_root(tmp_path: Path) -> Path:
    for relative in ("docs/CONCEPT_TAXONOMY.md", "data/sample/catalog_mvp-1.0.sqlite3",
                     "data/sample/demo_solved_mvp-1.json"):
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, destination)
    return tmp_path


def test_demo_journey_and_openapi(local_root: Path) -> None:
    def no_network(*args):
        pytest.fail("Demo must not fetch a public profile")

    with TestClient(create_app(local_root, public_fetcher=no_network)) as client:
        assert client.get("/health").json() == {"status": "ok"}
        assert len(client.get("/concepts").json()) == 28
        catalog = client.get("/catalog").json()
        assert any(p["problem_id"] == 76 for p in catalog)
        result = client.post("/practice", json={"target_problem_id": 76,
                             "query": "window", "concepts": ["sliding_window"], "limit": 3})
        assert result.status_code == 200
        payload = result.json()
        assert payload["profile"]["uncertainty"]
        assert len(payload["recommendations"]) == 3
        assert payload["recommendations"][0]["reason"]
        assert payload["diagnosis"]["target_problem_id"] == 76
        assert payload["diagnosis"]["concepts"][0]["explanation"]
        assert client.post("/profiles", json={"mode": "demo"}).json() == payload["profile"]
        schema = client.get("/openapi.json").json()
        assert "/personal/import" in schema["paths"]


def test_public_profile_preserves_sparse_and_unmapped_evidence(local_root: Path) -> None:
    calls = []

    def fetch(username, catalog):
        calls.append(username)
        return SolvedList(username, (1,), "mock public recent accepts", "2026-10-14", 40,
                          ("outside-catalog",))

    with TestClient(create_app(local_root, public_fetcher=fetch)) as client:
        response = client.post("/practice", json={"source": {"mode": "public", "username": "alice"},
                                                  "target_problem_id": 76})
        assert response.status_code == 200
        profile = response.json()["profile"]
        assert calls == ["alice"]
        assert profile["mapped_solves"] == 1
        assert profile["reported_solves"] == 40
        assert profile["unmapped_problem_identifiers"] == ["outside-catalog"]
        assert any("incomplete" in note for note in profile["uncertainty"])
        assert response.json()["diagnosis"]["readiness"] == "Not ready"


def test_public_unavailable_has_recoverable_error(local_root: Path) -> None:
    def unavailable(*args):
        raise SolvedListError("mock upstream failure")

    with TestClient(create_app(local_root, public_fetcher=unavailable)) as client:
        result = client.post("/profiles", json={"mode": "public", "username": "alice"})
        assert result.status_code == 503
        assert "demo" in result.json()["detail"]


@pytest.mark.parametrize("payload,status", [
    ({"source": {"mode": "public"}}, 422),
    ({"source": {"username": "alice"}}, 422),
    ({"source": {"mode": "public", "username": "../alice"}}, 422),
    ({"concepts": ["invented"]}, 422),
    ({"difficulty": "Impossible"}, 422),
    ({"limit": 0}, 422),
    ({"limit": True}, 422),
    ({"target_problem_id": 999999}, 404),
    ({"unexpected": "field"}, 422),
])
def test_validation_before_public_io(local_root: Path, payload: dict, status: int) -> None:
    def no_network(*args):
        pytest.fail("Invalid requests must not fetch profiles")

    with TestClient(create_app(local_root, public_fetcher=no_network)) as client:
        assert client.post("/practice", json=payload).status_code == status


def test_personal_access_opt_in_containment_and_owner_isolation(local_root: Path) -> None:
    raw = local_root / "data/raw"
    raw.mkdir()
    # Intentionally synthetic placeholder, not a real accepted solution.
    (raw / "synthetic.json").write_text(json.dumps([{
        "owner": "alice", "problem_id": 1, "title": "Two Sum", "language": "Python",
        "accepted": True, "code": "# synthetic transport test placeholder",
    }]), encoding="utf-8")
    with TestClient(create_app(local_root)) as client:
        owner = {"owner": "alice", "owner_authorized": True}
        for endpoint, fields in (("import", {"source": "synthetic.json"}),
                                 ("templates", {"query": "arrays_hashing"})):
            assert client.post(f"/personal/{endpoint}", json={"owner": "alice", **fields}).status_code == 403
        for source in ("../sample/demo_solved_mvp-1.json", str(raw / "synthetic.json")):
            assert client.post("/personal/import", json={**owner, "source": source}).status_code == 422
        assert client.post("/personal/import", json={**owner, "source": "synthetic.json"}).json() == {"imported": 1}
        result = client.post("/personal/templates", json={**owner, "query": "arrays_hashing"}).json()
        assert result["status"] == "available"
        assert result["snippets"][0]["owner"] == "alice"
        other = client.post("/personal/templates", json={**owner, "owner": "bob", "query": "arrays_hashing"}).json()
        assert other == {"status": "unavailable", "snippets": []}
        assert client.post("/personal/templates", json={**owner, "query": "no-match"}).json()["status"] == "no_matches"
        (raw / "empty.json").write_text("[]", encoding="utf-8")
        client.post("/personal/import", json={**owner, "source": "empty.json"})
        assert client.post("/personal/templates", json={**owner, "query": "arrays_hashing"}).json()["status"] == "empty"
