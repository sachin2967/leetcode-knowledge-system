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
python -m scripts.rebuild_catalog
python -m pytest
python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000
# In a second terminal using the same environment:
python -m streamlit run streamlit_app/app.py --server.address 127.0.0.1 --server.port 8501
```

M6 entry points are `src.api.app:app` and `streamlit_app/app.py`. The UI calls the API; keep domain logic in the existing packages. `/docs` exposes the request/response contracts. Demo mode is offline; public mode makes an explicit public recent-accept request without persisting history. Tests must mock that boundary.

Bind both services to loopback. Personal import and retrieval require explicit owner acknowledgement, but this is a trusted local tool, not authenticated multi-user hosting. Import sources are relative to ignored `data/raw/`; no arbitrary absolute server paths or code uploads are accepted. Never add real personal-code fixtures.

Commit and push each completed milestone and major change to the configured GitHub remote after applicable local checks. Preserve user changes, use normal pushes, and never force-push or amend without explicit authorization.

## Shared Codex and Claude GitHub workflow

Owner-approved on 24 November 2026. GitHub is the handoff source of truth for these
independent repositories. The owner authorizes normal commits and pushes of work
within the requested task; repeat permission is not needed for routine publication.

1. Before editing, inspect local status, fetch origin, and read open PRs, their head
   commits, comments and CI. Preserve all existing local and remote work. Do not
   assume that a default branch or a previous agent's summary is current.
2. Use one task branch per repository: `codex/<task>` or `claude/<task>`. Keep one
   active writer per branch. When agents share a machine, use a separate Git
   worktree or clone for each agent; never switch the other agent's checkout or
   change its index, files or uncommitted work.
3. The implementing agent owns the PR. Create one draft PR per task/repository and
   update it with normal commits. The other agent reviews that PR rather than
   opening a duplicate PR for the same branch. Write access changes only after an
   explicit handoff; before taking over, fetch and verify the latest PR head.
4. Run the checks appropriate to each change. Inspect the staged diff for other
   agents' edits, secrets, raw data, model binaries and runtime state. Do not commit
   credentials or private submissions. Keep frozen evaluation inputs and measured
   limitations intact; never describe offline/scripted checks as live quality.
5. Commit and push every meaningful tested milestone, and publish any remaining
   intended changes before ending a turn. Report the PR URL, pushed commit, actual
   check results and unresolved issues. If a push is blocked, state that explicitly;
   never report local-only changes as available to the other agent on GitHub.
6. Fetch immediately before pushing. If the remote moved, preserve both histories;
   merge non-rewriting updates when appropriate, inspect conflicts and rerun checks
   affected by the integration. Never force-push, amend, reset, drop another agent's
   commits or bypass hooks/signing without explicit owner authorization.
7. Keep the default branch as the integration branch. Do not push routine task
   changes directly to it or merge PRs automatically. The owner decides merges
   unless a particular merge is explicitly authorized.
8. Handoffs must state scope, base/head commit, validation, known failures, external
   inputs and the next action. Verify CI against the latest pushed head; pending,
   failed and passed are distinct. A started workflow is not a successful check.
