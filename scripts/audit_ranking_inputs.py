"""Measure dependence on oracle concept inputs without altering frozen judgments."""

import json
from pathlib import Path

from src.data.catalog import read_json
from src.data.validation import load_taxonomy_ids
from src.evaluation.metrics import mean_average_precision, ndcg_at_k, recall_at_k
from src.evaluation.provenance import text_sha256
from src.ranking.ranker import rank_problems, tag_overlap_score

ROOT = Path(__file__).resolve().parents[1]


def evaluate(problems, dataset) -> dict:
    pool = {p.problem_id for p in problems}
    queries = []
    for query in dataset["queries"]:
        judgments = {int(k): v for k, v in query["relevance"].items() if int(k) in pool}
        text_only = rank_problems(problems, query["text"], limit=len(problems))
        oracle = rank_problems(
            problems,
            query["text"],
            concepts=tuple(query["concept_ids"]),
            limit=len(problems),
        )
        lexical = sorted(
            problems, key=lambda p: (-tag_overlap_score(p, query["text"]), p.problem_id)
        )
        result = {"id": query["id"], "split": query["split"], "methods": {}}
        for name, ranking in (
            ("text_only_current_product", text_only),
            ("oracle_concepts", oracle),
            ("tag_overlap", lexical),
        ):
            ids = [p.problem_id for p in ranking]
            result["methods"][name] = {
                "ndcg_at_10": ndcg_at_k(ids, judgments),
                "recall_at_5": recall_at_k(ids, judgments, k=5),
                "map": mean_average_precision(ids, judgments),
                "returned_count": len(ids),
                "top_10_ids": ids[:10],
            }
        queries.append(result)
    heldout = [q for q in queries if q["split"] == "test"]
    methods = {
        name: {
            metric: sum(q["methods"][name][metric] for q in heldout) / len(heldout)
            for metric in ("ndcg_at_10", "recall_at_5", "map")
        }
        for name in heldout[0]["methods"]
    }
    return {
        "protocol": "oracle-input-ablation-v1",
        "queries": queries,
        "test_methods": methods,
        "test_query_count": len(heldout),
        "limitations": [
            "Same small concept-centric authored queries; no independently judged natural-language benchmark.",
            "Text-only ranking receives no query concept IDs; oracle condition receives them explicitly.",
            "No popularity snapshot is available. Existing BRD baseline criterion remains unproven.",
            "No inference, prompt tuning, embeddings, or learned ranker was added in this audit.",
        ],
    }


def main():
    path = ROOT / "data/sample/ranking_judgments_mvp-1.json"
    taxonomy = load_taxonomy_ids(ROOT / "docs/CONCEPT_TAXONOMY.md")
    problems = read_json(ROOT / "data/sample/catalog_mvp-1.0.json", taxonomy)
    report = evaluate(problems, json.loads(path.read_text(encoding="utf-8")))
    report["judgments_sha256"] = text_sha256(path)
    output = ROOT / "data/sample/ranking_input_audit_v1.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["test_methods"], indent=2))


if __name__ == "__main__":
    main()
