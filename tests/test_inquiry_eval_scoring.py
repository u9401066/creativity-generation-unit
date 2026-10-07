from __future__ import annotations

import pytest

from evals.inquiry.scoring import (
    adjusted_rand_index,
    majority_label,
    precision_at_k,
    theme_recall,
    top_labels,
)


def test_ari_is_one_for_identical_partitions_regardless_of_label_names() -> None:
    assert adjusted_rand_index(["a", "a", "b", "b"], [1, 1, 2, 2]) == pytest.approx(1.0)


def test_ari_is_near_zero_for_unrelated_partitions_and_can_be_negative() -> None:
    truth = ["a", "a", "b", "b", "c", "c"]
    shuffled = [1, 2, 1, 2, 1, 2]
    assert adjusted_rand_index(truth, shuffled) <= 0.0


def test_ari_rejects_mismatched_lengths() -> None:
    with pytest.raises(ValueError):
        adjusted_rand_index([1, 2], [1])


def test_ari_of_one_big_cluster_against_two_truth_groups_is_zero() -> None:
    assert adjusted_rand_index(["a", "a", "b", "b"], [0, 0, 0, 0]) == pytest.approx(0.0)


def test_majority_and_top_labels_are_deterministic_on_ties() -> None:
    assert majority_label(["b", "a", "a", "b"]) == "a"
    assert majority_label([]) is None
    assert top_labels(["x", "y", "y", "z", "z", "z"], 2) == ["z", "y"]


def test_theme_recall_uses_the_best_matching_cluster() -> None:
    truth = {"1": "A", "2": "A", "3": "A", "4": "B"}
    clusters = {"c1": {"1", "2"}, "c2": {"3", "4"}}
    recall = theme_recall(truth, clusters)
    assert recall["A"] == pytest.approx(2 / 3)
    assert recall["B"] == pytest.approx(1.0)


def test_precision_at_k_handles_short_and_empty_lists() -> None:
    assert precision_at_k([True, False, True], 2) == pytest.approx(0.5)
    assert precision_at_k([True], 5) == pytest.approx(1.0)
    assert precision_at_k([], 3) is None
