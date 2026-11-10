"""Evaluate fixed ranking methods against the versioned offline judgments."""

import json
from pathlib import Path

from src.data.catalog import read_json
from src.data.validation import load_taxonomy_ids
from src.evaluation.metrics import mean_average_precision, ndcg_at_k, recall_at_k
from src.ranking.ranker import popularity_score, rank_problems, tag_overlap_score


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    taxonomy = load_taxonomy_ids(ROOT / "docs/CONCEPT_TAXONOMY.md")
    problems = read_json(ROOT / "data/sample/catalog_mvp-1.0.json", taxonomy)
    dataset = json.loads((ROOT / "data/sample/ranking_judgments_mvp-1.json").read_text(encoding="utf-8"))
    by_id = {problem.problem_id: problem for problem in problems}
    output = {"dataset_version": dataset["dataset_version"], "catalog_version": dataset["catalog_version"],
              "taxonomy_version": dataset["taxonomy_version"], "candidate_count": len(problems),
              "candidate_ids": [problem.problem_id for problem in problems], "k": 10,
              "split": "test", "limitations": [
                  "Only six small hand-judged queries are included; aggregate metrics are descriptive, not generalizable.",
                  "Catalog acceptance rates are null, so the popularity baseline is a stable problem-ID fallback and is not a true popularity measure.",
                  "Tag and concept mappings are curated and may contain errors."],
              "methods": {}, "queries": {}}
    per_method = {name: [] for name in ("tag_overlap", "popularity", "concept_aware")}
    for query in dataset["queries"]:
        relevance = {int(key): value for key, value in query["relevance"].items()}
        ranked = {
            "tag_overlap": sorted(problems, key=lambda p: (-tag_overlap_score(p, query["text"]), p.problem_id)),
            "popularity": sorted(problems, key=lambda p: (-popularity_score(p), p.problem_id)),
            "concept_aware": [by_id[item.problem_id] for item in rank_problems(
                problems, query["text"], concepts=tuple(query["concept_ids"]), limit=len(problems))],
        }
        query_result = {"split": query["split"]}
        for method, items in ranked.items():
            ids = [item.problem_id for item in items]
            metrics = {"ndcg_at_10": ndcg_at_k(ids, relevance), "recall_at_10": recall_at_k(ids, relevance),
                       "map": mean_average_precision(ids, relevance)}
            query_result[method] = metrics
            if query["split"] == "test":
                per_method[method].append(metrics)
        output["queries"][query["id"]] = query_result
    for method, results in per_method.items():
        output["methods"][method] = {key: sum(item[key] for item in results) / len(results)
                                     for key in ("ndcg_at_10", "recall_at_10", "map")}
    rendered = json.dumps(output, indent=2) + "\n"
    (ROOT / "data/sample/ranking_report_mvp-1.json").write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
