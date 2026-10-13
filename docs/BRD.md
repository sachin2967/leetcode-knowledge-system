# Business Requirements — LeetCode Knowledge-Aware Practice System

**Status:** MVP scope frozen for repository foundation.

**Source:** *Final BRD & Implementation Guide | 3 ML Portfolio Projects*, Version 2.0, 12 October 2026, Project 1 (pages 2–3).

**Purpose:** Provide a concise, testable contract for implementation and interviews.

## Problem and outcome

Generic LeetCode lists and tag matching do not tell a learner whether they have the prerequisite concepts for a target problem or which practice problems will close a gap. The system should infer concept evidence from a public solved list, diagnose missing prerequisites, and rank a short, difficulty-aware practice sequence. A learner who imports their own accepted submissions should also be able to find a relevant personal template.

The goal is a useful, explainable practice recommendation, not a prediction that the learner will solve a problem. “Ready” means the defined prerequisite coverage is present; it is not a success probability.

## Users and modes

| User | Need |
| --- | --- |
| LeetCode learner with a public username | Personalized concept profile, diagnosis, and practice recommendations from their public solved list |
| Demo visitor | Immediate walkthrough using a preloaded, reproducible profile |
| Interviewer or reviewer | Inspect architecture, baselines, metrics, decisions, and failure cases |

Public solved history is sufficient for personalization. Personal code is only available after an explicit local or authorized import by its owner.

## MVP requirements

| ID | Requirement | Acceptance evidence |
| --- | --- | --- |
| M1 | Build a concept profile with confidence/evidence from a public solved list. | Given a valid username or demo fixture, show covered concepts and the solved problems supporting them. |
| M2 | Diagnose a target problem's prerequisites. | Return “Ready” or named missing concepts from the locked taxonomy, with an explanation based on coverage. |
| M3 | Rank practice recommendations for a query and for concept gaps. | Return an ordered list with relevant concepts, difficulty, and a reason for each item. |
| M4 | Order practice within a pattern family from easier to harder where appropriate. | A practice path exposes a defensible progression rather than an arbitrary list. |
| M5 | Retrieve personal code templates from accepted submissions imported by that user. | Opt-in import returns attributed snippets from that user's own corpus; no corpus means a clear unavailable state. |
| M6 | Expose core behavior through FastAPI and a simple Streamlit demo. | Demo mode and public-username mode can be exercised through the UI and API. |
| M7 | Evaluate ranking offline. | Reproducible results report NDCG@10, Recall@K, and MAP against tag-overlap and popularity baselines. |

The concept/pattern graph, polished template cleaning, and weak-area analytics are later enhancements. A compact prerequisite mapping needed for M2 is part of MVP, but a full graph is not required.

## Boundaries and non-goals

- No private submissions from other users, credential sharing, or scraping private code.
- No full solution generation or automatic code writing from retrieved templates.
- No claim that prerequisite coverage estimates a user's probability of success.
- No LLM-only core ranker. Lightweight embeddings and a simple ranking model may improve a measured baseline later.
- No Node.js or heavy React frontend for MVP; no mandatory external vector database or cloud service.
- No production-scale multi-user hosting, real-time synchronization, or browser extension in MVP.

## Success criteria and evaluation

The MVP succeeds when the public-profile and demo journeys work end to end, diagnosis names traceable concepts, recommendations include understandable reasons, and imported personal snippets remain isolated to their owner. Ranking quality must **beat both** simple tag-overlap and popularity baselines on a frozen offline judgment set, with NDCG@10 as the primary comparison and Recall@K and MAP reported alongside it. The source BRD does not specify a numeric target or dataset size; those must be set and frozen with the evaluation set before tuning.

Record query definitions, candidate set, relevance rubric, split, baseline configuration, metric implementation, and random seeds. Report cold-start, sparse-history, mislabeled-concept, and no-submission cases as limitations or failure cases. Do not present unmeasured improvements as results.

## Data strategy

| Data | Source and use | Boundary |
| --- | --- | --- |
| Problem catalog | Public metadata: ID/title, difficulty, tags/topics, company tags where available, acceptance rate, and descriptions where permitted | Track source, collection date, license/terms, missing fields, and stable IDs; do not assume every public field is freely redistributable. |
| Solved list | Public LeetCode profile for a supplied username | Store only data needed to construct concept evidence; handle unavailable profiles and limited history explicitly. |
| Personal accepted submissions | One-time or occasional owner-authorized local import | Local-only by default; never commit raw code or mix users' corpora. |
| Demo and evaluation fixtures | Small, reproducible samples with documented provenance | Keep safe sample fixtures in Git; keep raw imports and generated personal data out of Git. |

The locked taxonomy in [CONCEPT_TAXONOMY.md](CONCEPT_TAXONOMY.md) is the controlled vocabulary for problem mappings, profile evidence, and missing-concept explanations. Concept extraction and profile scoring remain implementation work.
