# LeetCode Knowledge-Aware Practice System

Project 1 of the ML portfolio described in the master BRD (Version 2.0, 12 October 2026). The intended system uses a learner's public solved history to identify concept coverage, diagnose prerequisites for a target problem, and recommend an ordered practice path. If the learner imports their own accepted submissions, it can also retrieve relevant personal code templates.

**Current status:** Milestones 1–6 implemented locally: curated catalog, evidence profiles, explainable ranking/offline evaluation, prerequisite diagnosis and gap practice paths, owner-scoped accepted-code retrieval, and FastAPI/Streamlit integration. Ranking success criteria remain unproven; see the evaluation boundaries below.

## Read first

- [Business requirements](docs/BRD.md): users, scope, acceptance criteria, and data strategy.
- [Architecture](docs/ARCHITECTURE.md): planned data flow, component boundaries, and locked stack.
- [Concept taxonomy](docs/CONCEPT_TAXONOMY.md): the 28 stable MVP concept IDs.
- [Agent instructions](AGENTS.md): development and evaluation rules.

## Repository layout

| Path | Planned responsibility |
| --- | --- |
| `src/data/` | Public problem metadata, solved-list ingestion, and local persistence |
| `src/knowledge_profile/` | Concept evidence and prerequisite diagnosis |
| `src/ranking/` | Candidate generation, baselines, and ranking |
| `src/evaluation/` | Frozen judgments, metrics, and experiment reports |
| `src/api/` | FastAPI application and request/response models |
| `streamlit_app/` | Streamlit demo |
| `scripts/` | Explicit data import and evaluation entry points |
| `data/sample/` | Small, safe demo fixtures |
| `data/raw/` | Local source imports, excluded from Git |
| `tests/` | Automated checks |

## Set up and run the foundation checks

Use Python 3.11 or newer. In PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m scripts.rebuild_catalog
python -m pytest
```

The rebuild command validates the manually curated [seed](data/sample/problems_seed.psv) against the locked taxonomy, then writes the versioned [JSON export](data/sample/catalog_mvp-1.0.json) and [SQLite store](data/sample/catalog_mvp-1.0.sqlite3). SQLite is the primary local store. The seed is static: no network access or LeetCode credentials are needed. Acceptance rates are `null` because this seed has no frozen source snapshot for that changing field; tags are brief manual topic labels. `collected_at` records the manual curation date, and each note explains the concept mapping. [requirements.txt](requirements.txt) includes API, UI, and local testing dependencies.

## Run the local API and demo

From the repository root, with the environment activated, start the API:

```powershell
python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000
```

In a second terminal using the same environment:

```powershell
python -m streamlit run streamlit_app/app.py --server.address 127.0.0.1 --server.port 8501
```

Open http://127.0.0.1:8501 for the demo and http://127.0.0.1:8000/docs for interactive API contracts. The API validates the local SQLite catalog and taxonomy at startup; rebuild the catalog if the snapshot is absent. The UI defaults to that loopback API; set `LKS_API_URL` before starting Streamlit to override it. No credentials, external model, or private data are needed for demo mode.

Select **demo**, choose target **76: Minimum Window Substring**, and submit to see evidence, missing prerequisite coverage, and the Easy-to-Hard gap path. Query text and optional stable concept IDs produce recommendations with reasons. Difficulty is a ranking preference, not a hard filter; scores are ordering signals, not probabilities. Empty matches produce an empty list. Select **public** and enter a username to explicitly fetch bounded recent public accepts; the UI shows source, collection date, unmapped IDs, and incomplete-history uncertainty. Each submitted plan makes at most one public fetch. Profile results remain in the current UI session until replaced; the API does not persist or cache them.

| Endpoint | Contract |
| --- | --- |
| `GET /health` | Loaded service health |
| `GET /catalog`, `GET /concepts` | Validated catalog and locked concept IDs |
| `POST /profiles` | `{ "mode": "demo" }` or `{ "mode": "public", "username": "..." }` |
| `POST /practice` | Source, query, concepts, optional difficulty/target ID, and limit (1–50); returns profile, recommendations, and optional diagnosis/path |
| `POST /personal/import` | Owner, explicit `owner_authorized: true`, and JSON source path relative to ignored `data/raw/`; replaces that owner's corpus |
| `POST /personal/templates` | Owner, explicit acknowledgement, and search query; returns attributed snippets or an explicit unavailable/empty/no-match state |

Example offline request in PowerShell:

```powershell
$plan = @{ source = @{ mode = 'demo' }; query = 'window'; concepts = @('sliding_window'); target_problem_id = 76; limit = 5 } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/practice -ContentType 'application/json' -Body $plan
```

Invalid inputs return 422, missing catalog targets 404, missing owner acknowledgement 403, and unavailable public history 503 with a demo fallback suggestion. The UI reports connection errors if the API is stopped. Personal access is a separate opt-in form: public usernames never automatically open a corpus. Import uses an existing owner-created local JSON file; it does not upload or fetch submission code. Both services are for a trusted local machine and must stay on loopback; owner acknowledgement is not authentication for hosted multi-user use.

## Build a concept profile

```powershell
python -m scripts.build_profile --demo
python -m scripts.build_profile --username lee215
```

Demo mode reads the [synthetic solved fixture](data/sample/demo_solved_mvp-1.json) and requires no network. Username mode makes one public GraphQL request and prints a profile without storing the learner's history. The public endpoint currently exposes recent accepted submissions and a total count, not a full solved-problem list. When recent slugs cannot be matched to the local catalog, the output reports them and shows incomplete evidence. Each concept includes its supporting catalog problem IDs and a simple evidence level: 0 solves = `unobserved`, 1 = `emerging`, 2 or more = `covered`. The numeric score is a threshold label, not a solve probability. See [profile decisions](docs/ARCHITECTURE.md) for limitations.

## Rank recommendations and evaluate offline

```powershell
python -m scripts.evaluate_ranking
```

The ranker supports query-based recommendations and easier-to-harder practice paths. The evaluation uses six fixed queries, a versioned 111-problem candidate catalog, hand-graded relevance (0–2), and fixed train/test query splits. It reports NDCG@10, Recall@5, Recall@10, and MAP for tag overlap, the ID-order fallback, and concept-aware ranking in [the frozen report](data/sample/ranking_report_mvp-1.json). Judgments outside the candidate pool are excluded from attainable relevance and listed per query. Consult the report's limitations before interpreting the small-split results.

On the three held-out queries, concept-aware ranking scores NDCG@10 **0.9564**, Recall@5 **0.8571**, and MAP **0.9045** (tag overlap: **0.8302 / 0.6905 / 0.7917**). These metrics use only judgments in the frozen 111-problem pool; out-of-pool labels are disclosed in the report. The “popularity” comparator is an ID-order fallback because acceptance rates are unavailable, so this is not evidence of beating a genuine popularity baseline. With only three held-out queries and hand-curated labels, these results are descriptive, not a general ranking-quality claim. A larger re-judged pool and sourced, dated popularity snapshot are required before asserting the BRD's baseline success criterion.

## Diagnose prerequisites

`src.knowledge_profile.diagnosis.diagnose_target` compares a catalog target against a compact, reviewed prerequisite map (with target concepts as a fallback). It reports each prerequisite's evidence level and supporting problem IDs. Only `covered` evidence meets the Ready threshold; emerging or unobserved concepts appear as gaps, and an ordered Easy-to-Hard practice path is returned for those gaps. This is a coverage explanation, never a solve-probability estimate. The prerequisite map is intentionally small and should be reviewed as catalog coverage grows.

## Import and retrieve your accepted code (local only)

Place an owner-authorized JSON array in ignored `data/raw/` with fields `owner`, `problem_id`, `title`, `language`, `accepted`, and `code`. Call `import_accepted_code(owner, source, data_root, owner_authorized=True)` explicitly; it rejects imports outside `data/raw/`, mismatched owners, and non-accepted rows. The stored corpus goes under a SHA-256 owner-keyed directory in `data/raw/personal_corpora/`. `retrieve_templates` only reads that owner's corpus and returns `unavailable` (no corpus), `empty` (corpus has no accepted snippets), `available` (matches), or `no_matches`. This is a local opt-in boundary; it does not provide authentication for hosted multi-user use. Never put real personal submissions in Git or tests.

## Local verification

`python -m pytest` covers domain behavior, API validation/error contracts, mocked public profiles, owner isolation and import containment, and Streamlit form journeys against the local API. All personal-code test content is synthetic and temporary. No test depends on live LeetCode responses.

M6 was checked with Python 3.11.4, FastAPI 0.162.3, Streamlit 1.67.0, and HTTPX 0.28.1: **48 tests passed**. Both server entry points started on loopback, their health endpoints responded, and a running API returned the demo target-76 plan. Catalog rebuild and offline evaluation reproduced the existing snapshots/report byte-for-byte; the demo profile CLI also ran successfully. The installed Starlette test client emits an HTTPX deprecation warning; tests currently pass. Public network availability was not tested, and no private data was fetched.

## Delivery sequence

1. Acquire and validate public problem metadata; map problems to the frozen concept IDs.
2. Build a profile from public solved history and a reproducible demo profile.
3. Freeze evaluation queries and judgments; implement tag overlap and popularity baselines before improved ranking.
4. Add prerequisite diagnosis and ordered practice paths. **Complete.**
5. Add opt-in import and retrieval for a learner's own accepted submissions. **Complete, local only.**
6. Expose the behavior through FastAPI and Streamlit; report ranking metrics and failure cases. **Complete, local only.**

The local master PDF is the source for project requirements. These repository docs summarize its Project 1 scope and make implementation decisions explicit; changes to scope or taxonomy should be recorded before code changes.
