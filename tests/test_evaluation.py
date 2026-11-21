from src.evaluation.metrics import mean_average_precision, ndcg_at_k, recall_at_k


def test_recall_at_five_uses_only_first_five_results() -> None:
    ranked = [1, 2, 3, 4, 5, 6]
    relevance = {5: 2, 6: 1}

    assert recall_at_k(ranked, relevance, k=5) == 0.5
    assert recall_at_k(ranked, relevance, k=10) == 1.0


def test_ndcg_perfect_ranking_is_one_and_worse_order_is_lower() -> None:
    relevance = {10: 2, 20: 1}
    assert ndcg_at_k([10, 20], relevance) == 1.0
    assert ndcg_at_k([20, 10], relevance) < 1.0


def test_recall_and_map_empty_relevance_are_zero() -> None:
    assert recall_at_k([1, 2], {}) == 0.0
    assert mean_average_precision([1, 2], {}) == 0.0


def test_map_uses_ranked_precision_at_each_relevant_result() -> None:
    assert mean_average_precision([2, 1, 3], {1: 1, 3: 2}) == (0.5 + 2 / 3) / 2
