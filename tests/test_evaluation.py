from src.evaluation.metrics import recall_at_k


def test_recall_at_five_uses_only_first_five_results() -> None:
    ranked = [1, 2, 3, 4, 5, 6]
    relevance = {5: 2, 6: 1}

    assert recall_at_k(ranked, relevance, k=5) == 0.5
    assert recall_at_k(ranked, relevance, k=10) == 1.0
