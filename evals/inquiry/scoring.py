"""Pure scoring helpers for the inquiry-memory evaluation (no CGU imports, easy to unit test)."""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Hashable, Sequence


def _comb2(n: int) -> float:
    return n * (n - 1) / 2


def adjusted_rand_index(truth: Sequence[Hashable], predicted: Sequence[Hashable]) -> float:
    """ARI between two labelings of the same items (1.0 = identical, ~0 = chance)."""
    if len(truth) != len(predicted):
        raise ValueError("labelings must have the same length")
    n = len(truth)
    if n < 2:
        return 1.0
    table: Counter[tuple[Hashable, Hashable]] = Counter(zip(truth, predicted, strict=True))
    sum_cells = sum(_comb2(c) for c in table.values())
    sum_rows = sum(_comb2(c) for c in Counter(truth).values())
    sum_cols = sum(_comb2(c) for c in Counter(predicted).values())
    expected = sum_rows * sum_cols / _comb2(n)
    maximum = (sum_rows + sum_cols) / 2
    if math.isclose(maximum, expected):
        return 1.0
    return (sum_cells - expected) / (maximum - expected)


def majority_label(labels: Sequence[str]) -> str | None:
    counts = Counter(labels)
    if not counts:
        return None
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]


def top_labels(labels: Sequence[str], k: int = 2) -> list[str]:
    counts = Counter(labels)
    return [label for label, _ in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:k]]


def theme_recall(truth: dict[str, str], clusters: dict[str, set[str]]) -> dict[str, float]:
    """For each true theme: the share of its items found together in its best predicted cluster."""
    members: dict[str, set[str]] = {}
    for item, label in truth.items():
        members.setdefault(label, set()).add(item)
    out: dict[str, float] = {}
    for label, items in members.items():
        best = max((len(items & cluster) for cluster in clusters.values()), default=0)
        out[label] = best / len(items)
    return out


def precision_at_k(flags: Sequence[bool], k: int) -> float | None:
    head = list(flags)[:k]
    return sum(head) / len(head) if head else None
