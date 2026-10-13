"""Guard the frozen MVP taxonomy against accidental ID drift."""

import re
from pathlib import Path


TAXONOMY = Path(__file__).resolve().parents[1] / "docs" / "CONCEPT_TAXONOMY.md"
MVP_CONCEPT_IDS = {
    "arrays_hashing",
    "two_pointers",
    "sliding_window",
    "prefix_sums",
    "binary_search",
    "sorting",
    "linked_lists",
    "stack",
    "monotonic_stack",
    "heap_priority_queue",
    "intervals",
    "greedy",
    "backtracking",
    "tree_traversal",
    "binary_search_tree",
    "graph_traversal",
    "topological_sort",
    "union_find",
    "shortest_paths",
    "dynamic_programming",
    "knapsack_dp",
    "interval_dp",
    "digit_dp",
    "trie",
    "segment_tree",
    "lazy_propagation",
    "bit_manipulation",
    "math_number_theory",
}


def test_mvp_taxonomy_has_28_unique_stable_ids() -> None:
    text = TAXONOMY.read_text(encoding="utf-8")
    ids = re.findall(r"^\| `([a-z][a-z0-9_]*)` \|", text, flags=re.MULTILINE)

    assert "**Version:** `mvp-1`" in text
    assert len(ids) == len(MVP_CONCEPT_IDS)
    assert len(set(ids)) == len(ids)
    assert set(ids) == MVP_CONCEPT_IDS
