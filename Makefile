.PHONY: catalog api ui test lint eval docker

PYTHON ?= python

catalog:
	$(PYTHON) -m scripts.rebuild_catalog

api:
	$(PYTHON) -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000

ui:
	$(PYTHON) -m streamlit run streamlit_app/app.py --server.address 127.0.0.1 --server.port 8501

lint:
	$(PYTHON) -m ruff check src tests scripts streamlit_app

test: lint
	$(PYTHON) -m pytest -q

eval:
	$(PYTHON) -m scripts.evaluate_ranking
	$(PYTHON) -m scripts.evaluate_guardrails

docker:
	docker compose up --build -d
