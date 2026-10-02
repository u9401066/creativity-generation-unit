"""Pure measurement functions: duplicates, novelty, diversity, MinHash."""

from __future__ import annotations

import numpy as np
import pytest

from cgu.domain.measure import (
    as_matrix,
    band_from_distance,
    diversity,
    jaccard,
    lexical_duplicate,
    minhash_signature,
    minhash_similarity,
    normalize,
    novelty_against,
    shingles,
    vendi_score,
)

BASE = "Replace routine benzodiazepine sedation with a nurse-led sleep protocol for older patients"


def test_normalize_ignores_case_whitespace_and_punctuation() -> None:
    assert normalize("  Hello,   World! ") == normalize("helloworld")
    assert normalize("A\u3000B") == "ab"


@pytest.mark.parametrize(
    "variant",
    [
        BASE,
        BASE.replace(" ", ""),
        BASE.upper() + "!!!",
        BASE + " today",
        "Replace routine benzodiazepine sedation with a nurse-led sleep protocol for older adults",
    ],
)
def test_exact_whitespace_and_near_duplicates_are_caught(variant: str) -> None:
    found = lexical_duplicate(variant, [("i-1", BASE)])
    assert found is not None
    assert found[0] == "i-1"
    assert 0.8 <= found[1].value <= 1.0
    assert found[1].calibrated is False
    assert found[1].n == 1


def test_unrelated_text_is_not_a_duplicate() -> None:
    other = "Install a standing desk in every ward office to reduce clerical back pain"
    assert lexical_duplicate(other, [("i-1", BASE)]) is None


def test_duplicate_threshold_is_overridable_and_named_in_method() -> None:
    found = lexical_duplicate(BASE + " in hospital", [("i-1", BASE)], threshold=0.5)
    assert found is not None
    assert "0.5" in found[1].method


def test_empty_reference_set_yields_none_not_zero() -> None:
    assert novelty_against(np.ones(4), np.empty((0, 4)), [], method="m", reference="r") is None


def test_novelty_reports_nearest_and_reference_size() -> None:
    refs = as_matrix([[1.0, 0.0], [0.0, 1.0]])
    result = novelty_against(
        as_matrix([[1.0, 0.1]])[0], refs, ["a", "b"], method="cosine", reference="typical set"
    )
    assert result is not None
    assert result.nearest_id == "a"
    assert result.reference_size == 2
    assert result.max_similarity.value > result.mean_similarity.value
    assert result.max_similarity.reference == "typical set"


def test_vendi_is_one_for_identical_and_n_for_orthogonal() -> None:
    same = np.ones((4, 4))
    assert vendi_score(same) == pytest.approx(1.0, abs=1e-6)
    assert vendi_score(np.eye(4)) == pytest.approx(4.0, abs=1e-6)


def test_vendi_between_the_extremes_for_partial_overlap() -> None:
    vectors = as_matrix([[1.0, 0.0], [1.0, 0.2], [0.0, 1.0]])
    score = vendi_score(vectors @ vectors.T)
    assert 1.0 < score < 3.0


def test_diversity_needs_two_items_and_is_a_measurement() -> None:
    assert diversity(np.ones((1, 3)), method="m", reference="r") is None
    result = diversity(np.eye(3), method="cosine", reference="set")
    assert result is not None
    assert result.n == 3
    assert result.calibrated is False
    assert result.method.startswith("Vendi score")


def test_minhash_estimates_jaccard() -> None:
    a = shingles(BASE)
    b = shingles(BASE + " and a quiet room at night")
    exact = jaccard(a, b)
    estimate = minhash_similarity(minhash_signature(a), minhash_signature(b))
    assert abs(estimate - exact) < 0.15


def test_minhash_is_deterministic_for_a_seed() -> None:
    sig1 = minhash_signature(shingles(BASE), seed=7)
    sig2 = minhash_signature(shingles(BASE), seed=7)
    assert (sig1 == sig2).all()


def test_large_pools_use_the_minhash_prefilter_and_still_find_the_duplicate() -> None:
    pool = [
        (f"i-{n}", f"completely different idea number {n} about topic {n * 7}") for n in range(300)
    ]
    pool.append(("i-target", BASE))
    found = lexical_duplicate(BASE, pool)
    assert found is not None
    assert found[0] == "i-target"


@pytest.mark.parametrize(
    ("distance", "band"), [(0.0, "near"), (0.34, "near"), (0.4, "mid"), (0.64, "mid"), (0.7, "far")]
)
def test_band_boundaries(distance: float, band: str) -> None:
    assert band_from_distance(distance) == band
