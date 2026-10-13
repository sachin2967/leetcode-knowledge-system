# Locked MVP concept taxonomy

**Version:** `mvp-1` (frozen on 14 October 2026)

**Scope:** 28 algorithmic concepts used as stable labels for problem mapping, learner evidence, and prerequisite explanations. These are concepts and patterns, not LeetCode's raw tags. The list is intentionally compact enough to evaluate mapping quality.

| ID | Concept | Definition |
| --- | --- | --- |
| `arrays_hashing` | Arrays and hashing | Index contiguous data and use sets or maps for membership, counts, or direct lookup. |
| `two_pointers` | Two pointers | Move two indices through a sequence to maintain a relation or reduce a search space. |
| `sliding_window` | Sliding window | Maintain a contiguous range while incrementally updating its state as boundaries move. |
| `prefix_sums` | Prefix sums | Precompute cumulative aggregates so range aggregates can be answered by subtraction. |
| `binary_search` | Binary search | Repeatedly halve an ordered or monotonic search space, including binary search on an answer. |
| `sorting` | Sorting | Order items by a key or comparator to expose structure used by a later step. |
| `linked_lists` | Linked lists | Traverse or rewire node references while preserving list invariants. |
| `stack` | Stack | Use last-in-first-out state to process nesting, deferred work, or reversible order. |
| `monotonic_stack` | Monotonic stack | Keep stack values or indices in order to find a next/previous greater or smaller element. |
| `heap_priority_queue` | Heap / priority queue | Repeatedly access or update the current minimum or maximum candidate. |
| `intervals` | Intervals | Reason about overlap, ordering, merging, or coverage of ranges. |
| `greedy` | Greedy choice | Make locally optimal choices justified by an exchange argument or invariant. |
| `backtracking` | Backtracking | Explore a choice tree and undo choices to enumerate or search feasible states. |
| `tree_traversal` | Tree traversal | Visit nodes using DFS/BFS and propagate state along parent-child relationships. |
| `binary_search_tree` | Binary search tree | Exploit ordered left/right subtree structure for lookup, validation, or traversal. |
| `graph_traversal` | Graph traversal | Explore vertices and edges with DFS/BFS while tracking visited state. |
| `topological_sort` | Topological ordering | Order nodes in a directed acyclic graph so prerequisites precede dependents. |
| `union_find` | Disjoint set union | Maintain connected components under merges with find and union operations. |
| `shortest_paths` | Shortest paths | Compute minimum-cost reachability with BFS or weighted-path algorithms under valid assumptions. |
| `dynamic_programming` | Dynamic programming | Define reusable states and transitions over overlapping subproblems. |
| `knapsack_dp` | Knapsack DP | Optimize or count choices under a capacity or target-sum constraint. |
| `interval_dp` | Interval DP | Solve subranges by combining results of shorter ranges or split points. |
| `digit_dp` | Digit DP | Count or optimize numbers under digit-wise constraints with prefix and tightness state. |
| `trie` | Trie | Store strings by shared prefixes for incremental lookup or prefix queries. |
| `segment_tree` | Segment tree | Store hierarchical range summaries for queries and point/range updates. |
| `lazy_propagation` | Lazy propagation | Defer and compose range updates in a segment tree until affected nodes are needed. |
| `bit_manipulation` | Bit manipulation | Use bitwise operators and masks for compact state, flags, or binary arithmetic. |
| `math_number_theory` | Math and number theory | Apply arithmetic properties such as divisibility, modular operations, or combinatorics. |

## Mapping rules

- Use IDs exactly as written. A problem can require multiple concepts; raw platform tags are evidence, not ground truth.
- Assign a concept only when it is materially needed to understand a standard solution. Record the reason and source of a mapping; allow human review of ambiguous cases.
- Keep specific labels alongside general ones when both are genuinely needed (for example, `lazy_propagation` with `segment_tree`). Do not automatically infer all broad labels from a specific label.
- Do not turn this table into a universal prerequisite graph. Curate prerequisite relationships separately with examples and review them against actual problems.
- Confidence in a learner profile must be based on observed solves and documented scoring rules. A missing solve is not proof of inability.
- New IDs, renames, removals, or changed meanings require a new taxonomy version plus a migration for catalog labels, profiles, and evaluation fixtures. Editorial wording can change without changing meaning.

**Intentional granularity:** BFS and DFS are covered by `graph_traversal` or `tree_traversal`; recursion is a technique used across several concepts; strings can use the sequence concepts above or `trie`. These boundaries keep the first evaluation set tractable and can be revised only with versioning.
