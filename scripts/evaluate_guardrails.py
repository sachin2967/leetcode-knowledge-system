"""Run a frozen local input/output guardrail challenge set."""

import json
from pathlib import Path

from src.data.catalog import read_json
from src.data.validation import load_taxonomy_ids
from src.mentor.guardrails import GuardrailError, contains_executable_solution
from src.mentor.mentor import retrieve_hint

ROOT = Path(__file__).resolve().parents[1]


def _binary_metrics(
    cases: list[dict], decisions: dict[str, bool]
) -> dict[str, float | int]:
    tp = sum(case["should_block"] and decisions[case["id"]] for case in cases)
    fp = sum(not case["should_block"] and decisions[case["id"]] for case in cases)
    fn = sum(case["should_block"] and not decisions[case["id"]] for case in cases)
    tn = sum(not case["should_block"] and not decisions[case["id"]] for case in cases)
    return {
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "true_negative": tn,
        "precision": tp / (tp + fp) if tp + fp else 0.0,
        "recall": tp / (tp + fn) if tp + fn else 0.0,
        "accuracy": (tp + tn) / len(cases) if cases else 0.0,
    }


def main() -> None:
    fixture = json.loads(
        (ROOT / "data/sample/guardrail_cases_v1.json").read_text(encoding="utf-8")
    )
    taxonomy = load_taxonomy_ids(ROOT / "docs/CONCEPT_TAXONOMY.md")
    catalog = read_json(ROOT / "data/sample/catalog_mvp-1.0.json", taxonomy)
    problem = next(
        problem for problem in catalog if problem.problem_id == fixture["problem_id"]
    )
    input_decisions = {}
    for case in fixture["input_cases"]:
        try:
            retrieve_hint(problem, case["text"], 1, taxonomy)
            input_decisions[case["id"]] = False
        except GuardrailError:
            input_decisions[case["id"]] = True
    output_decisions = {
        case["id"]: contains_executable_solution(case["text"])
        for case in fixture["output_cases"]
    }
    input_metrics = _binary_metrics(fixture["input_cases"], input_decisions)
    output_metrics = _binary_metrics(fixture["output_cases"], output_decisions)
    failures = [
        case["id"]
        for group, decisions in (
            (fixture["input_cases"], input_decisions),
            (fixture["output_cases"], output_decisions),
        )
        for case in group
        if case["should_block"] != decisions[case["id"]]
    ]
    report = {
        "dataset_version": fixture["dataset_version"],
        "problem_id": fixture["problem_id"],
        "input_cases": len(input_decisions),
        "output_cases": len(output_decisions),
        "input": input_metrics,
        "output": output_metrics,
        "limitations": [
            "Small, manually authored challenge set; it does not prove prompt-injection or code-leak prevention.",
            "Output checks are conservative Python/code-shape heuristics, not a formal safety proof.",
            "Local model behavior must be evaluated separately for each model and version.",
        ],
        "failures": failures,
        "passed": not failures,
    }
    path = ROOT / "data/sample/guardrail_report_v1.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
