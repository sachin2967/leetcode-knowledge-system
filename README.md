# LeetCode Knowledge-Aware Practice System

Project 1 of the ML portfolio described in the master BRD (Version 2.0, 12 October 2026). The intended system uses a learner's public solved history to identify concept coverage, diagnose prerequisites for a target problem, and recommend an ordered practice path. If the learner imports their own accepted submissions, it can also retrieve relevant personal code templates.

**Current status:** Milestones 1–5. The repository contains a curated catalog, evidence-based profiles, explainable ranking and offline evaluation, prerequisite diagnosis, and opt-in local owner-scoped accepted-code retrieval. FastAPI and Streamlit integration remains future work.

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

The rebuild command validates the manually curated [seed](data/sample/problems_seed.psv) against the locked taxonomy, then writes the versioned [JSON export](data/sample/catalog_mvp-1.0.json) and [SQLite store](data/sample/catalog_mvp-1.0.sqlite3). SQLite is the primary local store. The seed is static: no network access or LeetCode credentials are needed. Acceptance rates are `null` because this seed has no frozen source snapshot for that changing field; tags are brief manual topic labels. `collected_at` records the manual curation date, and each note explains the concept mapping. Only `pytest` is needed so far; application dependencies will be added when those layers exist.

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

The ranker supports query-based recommendations and easier-to-harder practice paths. The evaluation uses six fixed queries, a versioned 111-problem candidate catalog, hand-graded relevance (0–2), and fixed train/test query splits. It reports NDCG@10, Recall@10, and MAP on the held-out queries in [the frozen report](data/sample/ranking_report_mvp-1.json). Consult that report's limitations before interpreting the small-split results.

## Diagnose prerequisites

`src.knowledge_profile.diagnosis.diagnose_target` compares a catalog target against a compact, reviewed prerequisite map (with target concepts as a fallback). It reports each prerequisite's evidence level and supporting problem IDs. Only `covered` evidence meets the Ready threshold; emerging or unobserved concepts appear as gaps, and an ordered Easy-to-Hard practice path is returned for those gaps. This is a coverage explanation, never a solve-probability estimate. The prerequisite map is intentionally small and should be reviewed as catalog coverage grows.

## Import and retrieve your accepted code (local only)

Place an owner-authorized JSON array in ignored `data/raw/` with fields `owner`, `problem_id`, `title`, `language`, `accepted`, and `code`. Call `import_accepted_code(owner, source, data_root, owner_authorized=True)` explicitly; it rejects imports outside `data/raw/`, mismatched owners, and non-accepted rows. The stored corpus goes under a SHA-256 owner-keyed directory in `data/raw/personal_corpora/`. `retrieve_templates` only reads that owner's corpus and returns `unavailable` (no corpus), `empty` (corpus has no accepted snippets), `available` (matches), or `no_matches`. This is a local opt-in boundary; it does not provide authentication for hosted multi-user use. Never put real personal submissions in Git or tests.

## Delivery sequence

1. Acquire and validate public problem metadata; map problems to the frozen concept IDs.
2. Build a profile from public solved history and a reproducible demo profile.
3. Freeze evaluation queries and judgments; implement tag overlap and popularity baselines before improved ranking.
4. Add prerequisite diagnosis and ordered practice paths. **Complete.**
5. Add opt-in import and retrieval for a learner's own accepted submissions. **Complete, local only.**
6. Expose the behavior through FastAPI and Streamlit; report ranking metrics and failure cases.

The local master PDF is the source for project requirements. These repository docs summarize its Project 1 scope and make implementation decisions explicit; changes to scope or taxonomy should be recorded before code changes.
