"""Offline ranking metrics independent of ranker feature construction."""

from math import log2


def ndcg_at_k(ranked_ids: list[int], relevance: dict[int, int], k: int = 10) -> float:
    gains = [relevance.get(problem_id, 0) for problem_id in ranked_ids[:k]]
    dcg = sum((2**gain - 1) / log2(index + 2) for index, gain in enumerate(gains))
    ideal = sorted(relevance.values(), reverse=True)[:k]
    idcg = sum((2**gain - 1) / log2(index + 2) for index, gain in enumerate(ideal))
    return dcg / idcg if idcg else 0.0


def recall_at_k(ranked_ids: list[int], relevance: dict[int, int], k: int = 10) -> float:
    relevant = {problem_id for problem_id, grade in relevance.items() if grade > 0}
    return len(set(ranked_ids[:k]) & relevant) / len(relevant) if relevant else 0.0


def mean_average_precision(ranked_ids: list[int], relevance: dict[int, int]) -> float:
    relevant = {problem_id for problem_id, grade in relevance.items() if grade > 0}
    if not relevant:
        return 0.0
    hits = 0
    precision_sum = 0.0
    for index, problem_id in enumerate(ranked_ids, start=1):
        if problem_id in relevant:
            hits += 1
            precision_sum += hits / index
    return precision_sum / len(relevant)
