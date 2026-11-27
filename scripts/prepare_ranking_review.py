"""Prepare a blinded, ungraded candidate pool for independent human relevance review."""

import csv
import hashlib
import json
import random
from pathlib import Path

from src.data.catalog import read_json
from src.data.validation import load_taxonomy_ids
from src.evaluation.provenance import text_sha256
from src.ranking.ranker import rank_problems, tag_overlap_score

ROOT = Path(__file__).resolve().parents[1]


def main():
    path = ROOT / "data/sample/review_queries_v1.json"
    dataset = json.loads(path.read_text(encoding="utf-8"))
    taxonomy = load_taxonomy_ids(ROOT / "docs/CONCEPT_TAXONOMY.md")
    catalog = ROOT / "data/sample/catalog_mvp-1.0.json"
    problems = read_json(catalog, taxonomy)
    by_id = {p.problem_id: p for p in problems}
    rng, rows = random.Random(42), []
    for query in dataset["queries"]:
        ranked = rank_problems(problems, query["text"], limit=10)
        lexical = sorted(
            problems, key=lambda p: (-tag_overlap_score(p, query["text"]), p.problem_id)
        )[:10]
        candidates = {p.problem_id for p in (*ranked, *lexical)}
        # Random controls reduce the risk of judging only what current systems retrieve.
        candidates.update(p.problem_id for p in rng.sample(list(problems), 10))
        candidates = sorted(candidates)
        rng.shuffle(candidates)
        for problem_id in candidates:
            rows.append(
                {
                    "query_id": query["id"],
                    "split": query["split"],
                    "query": query["text"],
                    "problem_id": problem_id,
                    "title": by_id[problem_id].title,
                    "difficulty": by_id[problem_id].difficulty,
                    "grade_0_1_2": "",
                    "reviewer_notes": "",
                }
            )
    output = ROOT / "data/sample/ranking_review_v1.csv"
    if output.exists():
        raise FileExistsError(
            "Review worksheet already exists; preserve human judgments or explicitly version a new file."
        )
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    manifest = {
        "protocol": "blinded-review-v1",
        "seed": 42,
        "queries": len(dataset["queries"]),
        "rows": len(rows),
        "queries_sha256": text_sha256(path),
        "catalog_sha256": text_sha256(catalog),
        "text_hashing": "UTF-8 with universal newlines; portable across Git CRLF/LF checkouts",
        "worksheet_sha256_before_review": hashlib.sha256(
            output.read_bytes()
        ).hexdigest(),
        "rubric": "2 directly useful for the request; 1 prerequisite or partial transfer; 0 unrelated. Judge from problem understanding; use notes for ambiguity. Blank is unjudged, never zero.",
        "review_status": "unjudged",
        "required": "A human reviewer should grade without seeing method identity or scores. Do not tune on held-out test grades.",
        "limitations": "Authored queries and pooled incomplete judgments are not user-traffic evidence; no popularity comparator.",
    }
    (ROOT / "data/sample/ranking_review_manifest_v1.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
