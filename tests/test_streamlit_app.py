"""Execute demo UI forms against the real local API without opening sockets."""

from pathlib import Path

import httpx
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest

from src.api.app import create_app
from src.data.solved import SolvedList, SolvedListError

ROOT = Path(__file__).resolve().parents[1]


def test_ui_demo_public_and_personal_opt_in(monkeypatch) -> None:
    calls = []

    def fetch(username, catalog):
        calls.append(username)
        if username == "unavailable":
            raise SolvedListError("mock unavailable")
        return SolvedList(username, (1,), "mock public", "2026-10-14", 20)

    with TestClient(create_app(public_fetcher=fetch)) as client:

        def request(method, url, *, json=None, **kwargs):
            return client.request(method, url, json=json)

        monkeypatch.setattr(httpx, "request", request)
        app = AppTest.from_file(
            str(ROOT / "streamlit_app/app.py"), default_timeout=20
        ).run()
        assert not app.exception
        app.selectbox[1].set_value(76)
        app.button[0].click().run()
        assert not app.exception
        assert not calls
        assert "demo_learner" in app.subheader[0].value
        assert any("Not ready" in heading.value for heading in app.subheader)
        assert len(app.dataframe) == 4

        app.radio[0].set_value("public")
        app.text_input[0].set_value("alice")
        app.button[0].click().run()
        assert not app.exception
        assert calls == ["alice"]
        assert "alice" in app.subheader[0].value
        assert any("incomplete" in item.value for item in app.warning)

        app.text_input[0].set_value("unavailable")
        app.button[0].click().run()
        assert not app.exception
        assert app.error
        assert not app.subheader  # failed request clears the old user's results

        app.text_input[2].set_value("alice")
        app.button[2].click().run()
        assert not app.exception
        assert "403" in app.error[0].value


def test_ui_reports_unavailable_api(monkeypatch) -> None:
    def offline(*args, **kwargs):
        raise httpx.ConnectError("mock API down")

    monkeypatch.setattr(httpx, "request", offline)
    app = AppTest.from_file(str(ROOT / "streamlit_app/app.py")).run()
    assert not app.exception
    assert any("API unavailable" in item.value for item in app.error)
