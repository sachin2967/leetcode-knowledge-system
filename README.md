# LeetCode Knowledge-Aware Practice System

Project 1 of the ML portfolio described in the master BRD (Version 2.0, 12 October 2026). The intended system uses a learner's public solved history to identify concept coverage, diagnose prerequisites for a target problem, and recommend an ordered practice path. If the learner imports their own accepted submissions, it can also retrieve relevant personal code templates.

**Current status:** foundation only. This repository contains decisions, a frozen MVP concept vocabulary, and an empty application skeleton. It does not yet provide ranking, diagnosis, retrieval, an API, or a UI.

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
python -m pytest
```

The API and Streamlit commands will be documented when those entry points exist. No LeetCode credentials or personal submissions are needed to run the current check.

## Delivery sequence

1. Acquire and validate public problem metadata; map problems to the frozen concept IDs.
2. Build a profile from public solved history and a reproducible demo profile.
3. Freeze evaluation queries and judgments; implement tag overlap and popularity baselines before improved ranking.
4. Add prerequisite diagnosis and ordered practice paths.
5. Add opt-in import and retrieval for a learner's own accepted submissions.
6. Expose the behavior through FastAPI and Streamlit; report ranking metrics and failure cases.

The local master PDF is the source for project requirements. These repository docs summarize its Project 1 scope and make implementation decisions explicit; changes to scope or taxonomy should be recorded before code changes.
