"""The fixture-only pilot must not expose local private-code functionality."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.app import create_app

ROOT = Path(__file__).resolve().parents[1]


def test_demo_profile_blocks_private_routes_and_public_fetch(monkeypatch):
    monkeypatch.setenv("LKS_SERVING_MODE", "demo_only")
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.delenv("LKS_API_KEY", raising=False)
    monkeypatch.setenv("LKS_OLLAMA_MODEL", "must-not-call-a-local-model")

    def forbidden_fetch(*args):
        raise AssertionError("Hosted demo must never fetch a user's profile")

    with TestClient(create_app(ROOT, public_fetcher=forbidden_fetch)) as client:
        assert client.post("/personal/import", json={}).status_code == 404
        assert client.post("/personal/templates", json={}).status_code == 404
        paths = client.get("/openapi.json").json()["paths"]
        assert not any(path.startswith("/personal/") for path in paths)
        assert (
            client.post(
                "/profiles", json={"mode": "public", "username": "example"}
            ).status_code
            == 403
        )
        hint = client.post(
            "/mentor",
            json={"problem_id": 76, "question": "How should I start?", "level": 1},
        )
        assert hint.status_code == 200
        assert hint.json()["generation_mode"] == "deterministic"
        assert client.get("/ready").json()["serving_mode"] == "demo_only"


def test_production_refuses_trusted_local_profile(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("LKS_SERVING_MODE", "trusted_local")
    monkeypatch.setenv("LKS_API_KEY", "x" * 32)
    with TestClient(create_app(ROOT)) as client:
        assert client.get("/live").status_code == 200
        assert client.get("/ready").status_code == 503
        assert (
            client.get("/catalog", headers={"X-API-Key": "x" * 32}).status_code == 503
        )


def test_demo_private_boundary_survives_mount_prefix(monkeypatch):
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv("LKS_SERVING_MODE", "demo_only")
    monkeypatch.delenv("LKS_API_KEY", raising=False)
    parent = FastAPI()
    parent.mount("/demo", create_app(ROOT))
    with TestClient(parent) as client:
        response = client.post(
            "/demo/personal/import",
            json={
                "owner": "example",
                "owner_authorized": True,
                "source": "anything.json",
            },
        )
        assert response.status_code == 404


def test_demo_key_and_body_limit(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("LKS_SERVING_MODE", "demo_only")
    monkeypatch.setenv("LKS_API_KEY", "x" * 32)
    with TestClient(create_app(ROOT)) as client:
        assert client.get("/catalog").status_code == 401
        assert client.get("/docs").status_code == 401
        assert (
            client.get("/catalog", headers={"X-API-Key": "x" * 32}).status_code == 200
        )
        assert (
            client.post(
                "/mentor", content=b" " * 65537, headers={"X-API-Key": "x" * 32}
            ).status_code
            == 413
        )
