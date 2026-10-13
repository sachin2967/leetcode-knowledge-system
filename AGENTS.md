# Instructions for future agents

Read [docs/BRD.md](docs/BRD.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), and [docs/CONCEPT_TAXONOMY.md](docs/CONCEPT_TAXONOMY.md) before changing product behavior. The master BRD is Version 2.0, 12 October 2026; these files are the repository contract for Project 1. If they conflict, document the discrepancy and resolve it explicitly before changing scope.

## Scope and stack

- Keep the MVP in Python 3.11+ with FastAPI for the API/backend, Streamlit for the demo, pandas/NumPy/scikit-learn for core data and ranking work, and local files plus SQLite/JSON for persistence.
- Lightweight embeddings may be added only after baseline measurements justify them. Do not add Node.js, heavy React, a mandatory external vector database, or cloud infrastructure to the MVP.
- Keep transport in `src/api/`, data ingestion in `src/data/`, profile/diagnosis in `src/knowledge_profile/`, ranking in `src/ranking/`, and metrics in `src/evaluation/`. The UI calls the API and does not duplicate domain logic.
- Do not implement extra product features merely because they appear in the master BRD's “should-have” list; record scope changes first.

## Taxonomy and data

- Use only the stable IDs in [docs/CONCEPT_TAXONOMY.md](docs/CONCEPT_TAXONOMY.md) for MVP concept labels. Version the taxonomy and migrate all dependent data before changing an ID or its meaning.
- Maintain provenance, collection dates, and stable IDs for public problem metadata. Validate missing or inconsistent source fields.
- Public solved lists can support profiles. Personal accepted code requires owner-authorized import and must remain separate by user. Never commit raw personal imports, credentials, or other users' private code.
- Keep small safe fixtures in `data/sample/`; keep source imports in ignored `data/raw/`.
- “Ready” means defined prerequisite coverage, not solve probability. Provide evidence and uncertainty in profile and diagnosis outputs.

## Coding standards

- Use type hints, small functions, explicit schemas, and deterministic behavior where practical. Keep I/O at boundaries so domain logic is testable without network access.
- Document assumptions and failure modes next to the relevant design or evaluation code. Prefer simple, explainable methods before adding model complexity.
- Add focused tests for behavior and edge cases. Avoid tests that merely restate implementation. Use stable local fixtures; do not make tests depend on live LeetCode responses.
- Do not add heavyweight logic during the foundation stage. Treat the current packages as placeholders.

## Evaluation rules

1. Define and freeze a judged offline query set, candidate pool, relevance rubric, and split before tuning ranking.
2. Implement and measure tag-overlap and popularity baselines first. Compare the same queries and candidates using NDCG@10 as primary, with Recall@K and MAP also reported.
3. Record seeds, versions, configuration, dataset provenance, and failure cases. Do not claim improvements without reproducible measurements.
4. Keep evaluation code and held-out judgments separate from ranker feature construction. Prevent leakage from test labels into ranking features.

## Local commands

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest
```

The API and UI do not have runnable entry points yet. Update this file and the README when they are introduced.
