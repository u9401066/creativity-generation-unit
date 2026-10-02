"""evals.stats：Wilson 區間與 kappa。"""

from __future__ import annotations

import pytest
import test_evals_support  # noqa: F401  (設定 sys.path)

from evals.stats import cohen_kappa, median, wilson_interval


@pytest.mark.parametrize(
    ("successes", "n", "expected"),
    [
        (0, 10, (0.0, 0.2775)),
        (10, 10, (0.7225, 1.0)),
        (5, 10, (0.2366, 0.7634)),
        (50, 100, (0.4038, 0.5962)),
        (1, 4, (0.0456, 0.6994)),
    ],
)
def test_wilson_known_values(successes: int, n: int, expected: tuple[float, float]) -> None:
    lo, hi = wilson_interval(successes, n)
    assert lo == pytest.approx(expected[0], abs=1e-3)
    assert hi == pytest.approx(expected[1], abs=1e-3)


def test_wilson_empty_sample_is_none() -> None:
    assert wilson_interval(0, 0) is None


def test_wilson_rejects_impossible_counts() -> None:
    with pytest.raises(ValueError):
        wilson_interval(11, 10)
    with pytest.raises(ValueError):
        wilson_interval(-1, 10)


def test_wilson_interval_narrows_with_n_and_contains_estimate() -> None:
    lo1, hi1 = wilson_interval(6, 10)
    lo2, hi2 = wilson_interval(60, 100)
    assert (hi2 - lo2) < (hi1 - lo1)
    assert lo1 <= 0.6 <= hi1
    assert lo2 <= 0.6 <= hi2


def test_wilson_accepts_fractional_successes() -> None:
    lo, hi = wilson_interval(4.5, 9)
    assert lo < 0.5 < hi


def test_kappa_perfect_and_opposite() -> None:
    assert cohen_kappa([("a", "a"), ("b", "b")]) == pytest.approx(1.0)
    assert cohen_kappa([("a", "b"), ("b", "a")]) == pytest.approx(-1.0)


def test_kappa_degenerate_cases() -> None:
    assert cohen_kappa([]) is None
    assert cohen_kappa([("a", "a"), ("a", "a")]) is None


def test_median() -> None:
    assert median([3, 1, 2]) == 2
    assert median([1, 2, 3, 4]) == 2.5
    assert median([]) is None
