"""Score human judgments only after every frozen pooled pair is explicitly graded."""

import csv
import hashlib
import io
import json
from pathlib import Path

from src.data.catalog import read_json
from src.data.validation import load_taxonomy_ids
from src.evaluation.metrics import mean_average_precision, ndcg_at_k, recall_at_k
from src.evaluation.provenance import text_sha256
from src.ranking.ranker import rank_problems, tag_overlap_score

ROOT = Path(__file__).resolve().parents[1]


def load_review(path: Path, expected_blank_sha256: str) -> list[dict]:
    """Preserve frozen pair identity; blanks never become negative judgments."""
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames
        rows = list(reader)
    expected_fields = [
        "query_id",
        "split",
        "query",
        "problem_id",
        "title",
        "difficulty",
        "grade_0_1_2",
        "reviewer_notes",
    ]
    if fields != expected_fields or not rows:
        raise ValueError("Review schema or rows are missing.")
    frozen = io.StringIO(newline="")
    writer = csv.DictWriter(frozen, fieldnames=fields)
    writer.writeheader()
    for row in rows:
        if None in row or any(value is None for value in row.values()):
            raise ValueError("Malformed review row.")
        writer.writerow({**row, "grade_0_1_2": "", "reviewer_notes": ""})
    if hashlib.sha256(frozen.getvalue().encode()).hexdigest() != expected_blank_sha256:
        raise ValueError("Frozen pairs changed; edit only grades and reviewer notes.")
    if any(row["grade_0_1_2"] not in {"0", "1", "2"} for row in rows):
        raise ValueError(
            "Every frozen pair needs an explicit 0, 1 or 2; blanks are unjudged."
        )
    return rows


def main():
    directory = ROOT / "data/sample"
    manifest = json.loads(
        (directory / "ranking_review_manifest_v1.json").read_text(encoding="utf-8")
    )
    for filename, key in (
        ("review_queries_v1.json", "queries_sha256"),
        ("catalog_mvp-1.0.json", "catalog_sha256"),
    ):
        if text_sha256(directory / filename) != manifest[key]:
            raise ValueError("Frozen review input checksum changed.")
    rows = load_review(
        directory / "ranking_review_v1.csv", manifest["worksheet_sha256_before_review"]
    )
    taxonomy = load_taxonomy_ids(ROOT / "docs/CONCEPT_TAXONOMY.md")
    problems = read_json(directory / "catalog_mvp-1.0.json", taxonomy)
    grouped = {}
    for row in rows:
        grouped.setdefault(row["query_id"], []).append(row)
    output = []
    for query_id, pairs in grouped.items():
        query, split = pairs[0]["query"], pairs[0]["split"]
        relevance = {int(row["problem_id"]): int(row["grade_0_1_2"]) for row in pairs}
        ranked = rank_problems(problems, query, limit=len(problems))
        baseline = sorted(
            problems, key=lambda p: (-tag_overlap_score(p, query), p.problem_id)
        )
        methods = {}
        for name, items in (("text_only_product", ranked), ("tag_overlap", baseline)):
            ids = [p.problem_id for p in items if p.problem_id in relevance]
            methods[name] = {
                "ndcg_at_10_in_judged_pool": ndcg_at_k(ids, relevance),
                "recall_at_10_of_judged_positives": recall_at_k(ids, relevance),
                "map_in_judged_pool": mean_average_precision(ids, relevance),
            }
        output.append(
            {
                "query_id": query_id,
                "split": split,
                "judged_candidates": len(pairs),
                "methods": methods,
            }
        )
    report = {
        "protocol": "human-pooled-review-v1",
        "queries": output,
        "limitations": [
            "Conditional ranking within an incomplete pooled candidate set; not full-catalog recall.",
            "Human judgments are not real-user outcome data. No popularity baseline is available.",
            "No tuning or significance claim is performed by this evaluator.",
        ],
    }
    (directory / "reviewed_ranking_report_v1.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
