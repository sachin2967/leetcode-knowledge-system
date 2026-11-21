"""Versioned concept prerequisite DAG over the locked MVP taxonomy."""

from collections import deque

GRAPH_VERSION = "concept-dag-1"

# Edges point from a prerequisite to the concept that builds on it. This is a
# reviewed teaching scaffold, not a claim that every problem requires every edge.
DEPENDENCIES: dict[str, tuple[str, ...]] = {
    "arrays_hashing": (),
    "two_pointers": ("arrays_hashing",),
    "sliding_window": ("arrays_hashing",),
    "prefix_sums": ("arrays_hashing",),
    "binary_search": ("arrays_hashing", "sorting"),
    "sorting": ("arrays_hashing",),
    "linked_lists": ("arrays_hashing",),
    "stack": ("arrays_hashing",),
    "monotonic_stack": ("stack",),
    "heap_priority_queue": ("arrays_hashing",),
    "intervals": ("sorting",),
    "greedy": ("sorting",),
    "backtracking": ("arrays_hashing",),
    "tree_traversal": ("arrays_hashing",),
    "binary_search_tree": ("tree_traversal", "binary_search"),
    "graph_traversal": ("arrays_hashing",),
    "topological_sort": ("graph_traversal",),
    "union_find": ("graph_traversal",),
    "shortest_paths": ("graph_traversal", "heap_priority_queue"),
    "dynamic_programming": ("arrays_hashing",),
    "knapsack_dp": ("dynamic_programming",),
    "interval_dp": ("dynamic_programming", "intervals"),
    "digit_dp": ("dynamic_programming", "math_number_theory"),
    "trie": ("arrays_hashing",),
    "segment_tree": ("arrays_hashing",),
    "lazy_propagation": ("segment_tree",),
    "bit_manipulation": ("arrays_hashing",),
    "math_number_theory": ("arrays_hashing",),
}


def validate_dag(taxonomy_ids: frozenset[str]) -> tuple[str, ...]:
    """Validate exact node coverage and return a deterministic topological order."""
    if set(DEPENDENCIES) != set(taxonomy_ids):
        raise ValueError(
            "Prerequisite DAG nodes must match the locked taxonomy exactly"
        )
    dependents = {node: [] for node in DEPENDENCIES}
    indegree = {node: len(parents) for node, parents in DEPENDENCIES.items()}
    for node, parents in DEPENDENCIES.items():
        if len(set(parents)) != len(parents) or set(parents) - set(DEPENDENCIES):
            raise ValueError(f"Invalid prerequisites for {node}")
        for parent in parents:
            dependents[parent].append(node)
    ready = deque(sorted(node for node, degree in indegree.items() if degree == 0))
    order = []
    while ready:
        node = ready.popleft()
        order.append(node)
        for child in sorted(dependents[node]):
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
    if len(order) != len(DEPENDENCIES):
        raise ValueError("Prerequisite graph contains a cycle")
    return tuple(order)


def ancestors(concept_id: str) -> tuple[str, ...]:
    """Return transitive prerequisites in deterministic topological order."""
    if concept_id not in DEPENDENCIES:
        raise ValueError(f"Unknown concept: {concept_id}")
    needed: set[str] = set()
    pending = list(DEPENDENCIES[concept_id])
    while pending:
        parent = pending.pop()
        if parent not in needed:
            needed.add(parent)
            pending.extend(DEPENDENCIES[parent])
    order = validate_dag(frozenset(DEPENDENCIES))
    return tuple(node for node in order if node in needed)
