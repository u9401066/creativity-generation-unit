"""Inquiry memory, domain layer: redaction, stems, families, clustering, theme identity."""

from __future__ import annotations

import itertools
import random

import numpy as np
import pytest

from cgu.domain.capture import (
    REASON_DISABLED,
    REASON_EXCLUDED,
    REASON_NOT_ASKED,
    capture_gate,
    clean_project,
    iso_from_epoch_ms,
    parse_time,
)
from cgu.domain.common import Measurement
from cgu.domain.inquiry import (
    FamilyIndex,
    Inquiry,
    ThemeRecord,
    average_linkage,
    co_occurrence,
    ephemeral_theme_id,
    match_identities,
    question_stem,
    stem_share,
)
from cgu.domain.lexical import best_lexical_match, jaccard, shingles
from cgu.domain.redaction import (
    MAX_INQUIRY_CHARS,
    NOT_DETECTED_NOTE,
    REDACTION_KEYS,
    merge_counts,
    prepare_text,
    redact,
)

# --- redaction: spec section 3 item 3, rule by rule -------------------------------------------


def test_every_redaction_key_is_always_reported_even_when_zero() -> None:
    cleaned, counts = redact("nothing to hide here")
    assert cleaned == "nothing to hide here"
    assert set(counts) == set(REDACTION_KEYS) and sum(counts.values()) == 0


def test_email_is_replaced() -> None:
    cleaned, counts = redact("寄給 dr.chen+icu@hospital.example.org 好嗎")
    assert cleaned == "寄給 [email] 好嗎" and counts["email"] == 1


@pytest.mark.parametrize(
    "phone",
    ["0912-345-678", "0912345678", "0912 345 678", "+886 912 345 678", "+886-912-345-678"],
)
def test_taiwan_mobile_and_international_numbers_are_replaced(phone: str) -> None:
    cleaned, counts = redact(f"打給我 {phone} 謝謝")
    assert cleaned == "打給我 [phone] 謝謝", cleaned
    assert counts["phone"] == 1


@pytest.mark.parametrize("phone", ["02-2345-6789", "(02) 2345 6789", "04-2345-6789", "037-123456"])
def test_taiwan_landlines_are_replaced(phone: str) -> None:
    cleaned, counts = redact(f"分機 {phone} 轉 12")
    assert "[phone]" in cleaned and counts["phone"] == 1, cleaned


def test_a_us_style_international_number_is_replaced() -> None:
    cleaned, counts = redact("call +1 (415) 555-2671 today")
    assert cleaned == "call [phone] today" and counts["phone"] == 1


def test_short_digit_groups_are_not_phones() -> None:
    cleaned, counts = redact("ward 12 bed 3, 2024-10-02, 120/80 mmHg, 85 kg")
    assert cleaned == "ward 12 bed 3, 2024-10-02, 120/80 mmHg, 85 kg"
    assert sum(counts.values()) == 0


def test_taiwan_national_id_is_replaced() -> None:
    cleaned, counts = redact("病人 A123456789 與 F234567890 的比較")
    assert cleaned == "病人 [id] 與 [id] 的比較" and counts["id"] == 2


def test_a_national_id_inside_a_longer_token_is_not_an_id() -> None:
    cleaned, counts = redact("code XA123456789 stays")
    assert counts["id"] == 0
    assert "[number]" in cleaned and counts["number"] == 1


def test_digit_runs_of_seven_or_more_are_replaced_and_six_are_kept() -> None:
    cleaned, counts = redact("病歷號 12345678 與 123456 以及 1234567")
    assert cleaned == "病歷號 [number] 與 123456 以及 [number]"
    assert counts["number"] == 2


def test_url_query_and_fragment_are_stripped_but_host_and_path_stay() -> None:
    cleaned, counts = redact("看 https://example.org/a/b?token=abc&u=1#frag 這篇")
    assert cleaned == "看 https://example.org/a/b 這篇" and counts["url"] == 1
    cleaned, counts = redact("https://example.org/a#only-fragment")
    assert cleaned == "https://example.org/a" and counts["url"] == 1
    cleaned, counts = redact("https://example.org/plain/path")
    assert cleaned == "https://example.org/plain/path" and counts["url"] == 0


def test_a_phone_number_inside_a_url_query_is_removed_with_the_query() -> None:
    cleaned, counts = redact("https://x.test/p?tel=0912345678")
    assert cleaned == "https://x.test/p" and counts["url"] == 1 and counts["phone"] == 0


def test_redaction_is_deterministic_and_idempotent() -> None:
    text = "a@b.co 0912345678 A123456789 12345678 https://x.test/?q=1 ok"
    first = redact(text)
    assert redact(text) == first
    again, counts = redact(first[0])
    assert again == first[0] and sum(counts.values()) == 0


def test_names_and_clinical_details_are_not_detected_and_the_note_says_so() -> None:
    text = "王小明 78 歲，術後第三天譫妄，使用 haloperidol"
    cleaned, counts = redact(text)
    assert cleaned == text and sum(counts.values()) == 0
    assert "姓名" in NOT_DETECTED_NOTE and "臨床" in NOT_DETECTED_NOTE


def test_text_is_capped_at_2000_characters_and_flagged() -> None:
    prepared = prepare_text("問" * 2500)
    assert len(prepared.text) == MAX_INQUIRY_CHARS and prepared.truncated is True
    short = prepare_text("  短問題  ")
    assert short.text == "短問題" and short.truncated is False
    exact = prepare_text("問" * 2000)
    assert len(exact.text) == 2000 and exact.truncated is False


def test_redaction_happens_before_the_cap_so_a_cut_cannot_leave_half_an_identifier() -> None:
    prepared = prepare_text("x" * 1995 + " A123456789")
    assert "A12345" not in prepared.text and prepared.redactions["id"] == 1
    assert prepared.text.endswith("[id]") or prepared.truncated


def test_counts_merge_across_parts() -> None:
    merged = merge_counts({"email": 1, "phone": 2}, {"email": 2, "number": 1})
    assert merged["email"] == 3 and merged["phone"] == 2 and merged["number"] == 1
    assert set(merged) >= set(REDACTION_KEYS)


# --- capture helpers ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("D:\\workspace\\proj-a", "proj-a"),
        ("D:\\workspace\\proj-a\\", "proj-a"),
        ("/home/me/work/proj-b", "proj-b"),
        ("C:/Users/me/proj-c/", "proj-c"),
        ("plain", "plain"),
        ("C:\\", None),
        ("", None),
        (None, None),
    ],
)
def test_project_is_only_the_last_path_segment(raw: str | None, expected: str | None) -> None:
    assert clean_project(raw) == expected


def test_capture_gate_reasons() -> None:
    assert capture_gate(None, [], "p") == REASON_NOT_ASKED
    assert capture_gate(False, [], "p") == REASON_DISABLED
    assert capture_gate(True, ["Secret"], "secret") == REASON_EXCLUDED
    assert capture_gate(True, ["secret"], "other") is None
    assert capture_gate(True, ["secret"], None) is None


def test_time_helpers_treat_naive_as_utc_and_convert_epoch_milliseconds() -> None:
    assert parse_time("2026-10-02T08:00:00").isoformat() == "2026-10-02T08:00:00+00:00"
    assert parse_time("2026-10-02T16:00:00+08:00").isoformat() == "2026-10-02T08:00:00+00:00"
    assert iso_from_epoch_ms(1_780_000_000_000).startswith("2026-")
    with pytest.raises(ValueError):
        parse_time("yesterday")


# --- stems, lexical families -------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "stem"),
    [
        ("有沒有辦法預測譫妄？", "有沒"),
        ("  「為什麼」會這樣", "為什"),
        ("How can we reduce delirium", "how can"),
        ("remimazolam vs propofol", "remimazolam vs"),
        ("", ""),
        ("???", ""),
    ],
)
def test_question_stem(text: str, stem: str) -> None:
    assert question_stem(text) == stem


def test_lexical_jaccard_and_best_match_use_the_threshold() -> None:
    a = "術前認知篩檢可以預測術後譫妄嗎"
    assert jaccard(shingles(a), shingles(a)) == 1.0
    assert jaccard(shingles(a), shingles("完全不相干的另一個問題在這裡")) < 0.2
    candidates = [("x", "術前認知篩檢可以預測術後譫妄嗎？"), ("y", "病歷申請流程")]
    match = best_lexical_match(a, candidates, 0.8)
    assert match is not None and match[0] == "x" and match[1] >= 0.8
    assert best_lexical_match("病歷申請流程怎麼線上化", candidates, 0.8) is None
    assert best_lexical_match("!!!", candidates, 0.5) is None


def vec(*values: float) -> np.ndarray:
    array = np.asarray(values, dtype=np.float32)
    return array / np.linalg.norm(array)


def test_family_index_groups_by_lexical_jaccard_then_semantic_cosine() -> None:
    rows = [
        ("q1", "fam-1", "術前認知篩檢可以預測術後譫妄嗎", "2026-10-01T00:00:00+00:00"),
        ("q2", "fam-2", "病歷申請流程怎麼線上化", "2026-10-02T00:00:00+00:00"),
    ]
    index = FamilyIndex(rows, {"q1": vec(1, 0, 0), "q2": vec(0, 1, 0)})
    lexical = index.match("術前認知篩檢可以預測術後譫妄嗎？", None)
    assert lexical is not None and lexical.family_id == "fam-1" and lexical.method == "lexical"
    semantic = index.match("totally different words", vec(0.0, 1.0, 0.1))
    assert semantic is not None and semantic.family_id == "fam-2" and semantic.method == "semantic"
    assert semantic.similarity >= 0.92
    assert index.match("totally different words", vec(0, 0, 1)) is None
    assert index.match("totally different words", None) is None
    assert index.count("fam-1") == 1 and index.earliest("fam-1") == "q1"


def test_family_index_sees_questions_added_during_the_same_batch() -> None:
    index = FamilyIndex([], {})
    assert index.match("第一次問這個問題的措辭", None) is None
    index.add("q1", "fam-1", "第一次問這個問題的措辭", "2026-10-01T00:00:00+00:00", vec(1, 0))
    again = index.match("第一次問這個問題的措辭啊", None)
    assert again is not None and again.family_id == "fam-1"
    assert index.match("zzz", vec(1.0, 0.05)) is not None
    index.add("q2", "fam-1", "別的說法", "2026-10-03T00:00:00+00:00", None)
    assert index.count("fam-1") == 2 and index.earliest("fam-1") == "q1"


# --- average linkage ---------------------------------------------------------------------------


def brute_force_upgma(distance: np.ndarray, threshold: float) -> list[list[int]]:
    """The textbook O(n^3) average-linkage procedure, merging while the closest pair <= threshold."""
    clusters = [[i] for i in range(distance.shape[0])]
    while len(clusters) > 1:
        best: tuple[float, int, int] | None = None
        for i, j in itertools.combinations(range(len(clusters)), 2):
            mean = float(np.mean([distance[a, b] for a in clusters[i] for b in clusters[j]]))
            if best is None or mean < best[0]:
                best = (mean, i, j)
        assert best is not None
        if best[0] > threshold:
            break
        _score, i, j = best
        clusters[i] = sorted(clusters[i] + clusters[j])
        del clusters[j]
    return sorted(sorted(c) for c in clusters)


def random_distance(rng: random.Random, n: int) -> np.ndarray:
    points = np.asarray([[rng.gauss(0, 1) for _ in range(5)] for _ in range(n)])
    points /= np.linalg.norm(points, axis=1, keepdims=True)
    return np.clip(1.0 - points @ points.T, 0.0, 2.0)


@pytest.mark.parametrize("seed", range(8))
def test_average_linkage_matches_the_brute_force_definition(seed: int) -> None:
    rng = random.Random(seed)
    distance = random_distance(rng, rng.randint(2, 24))
    for threshold in (0.3, 0.7, 1.0, 1.3):
        fast = sorted(sorted(c) for c in average_linkage(distance, threshold))
        assert fast == brute_force_upgma(distance, threshold), (seed, threshold)


def test_average_linkage_edge_cases() -> None:
    assert average_linkage(np.zeros((0, 0)), 0.5) == []
    assert average_linkage(np.zeros((1, 1)), 0.5) == [[0]]
    far = np.array([[0.0, 1.5], [1.5, 0.0]])
    assert average_linkage(far, 0.5) == [[0], [1]]
    assert average_linkage(far, 1.6) == [[0, 1]]


def test_average_linkage_is_deterministic_and_covers_every_index_once() -> None:
    distance = random_distance(random.Random(99), 40)
    first = average_linkage(distance, 0.8)
    assert first == average_linkage(distance, 0.8)
    assert sorted(i for cluster in first for i in cluster) == list(range(40))


# --- theme identity ----------------------------------------------------------------------------


def record(theme_id: str, members: list[str], label: str | None = None) -> ThemeRecord:
    return ThemeRecord(
        id=theme_id,
        label=label,
        labeled_by="caller" if label else None,
        member_ids=members,
        backend="ngram-hash",
    )


def test_identity_keeps_the_theme_when_member_overlap_is_at_least_half() -> None:
    old = [record("th-a", ["1", "2", "3", "4"], "A"), record("th-b", ["7", "8", "9"], "B")]
    new = [["2", "3", "4", "5"], ["7", "8", "9", "10"], ["20", "21", "22"]]
    matched = match_identities(old, new, {str(i) for i in range(1, 30)})
    assert [m.id if m else None for m in matched] == ["th-a", "th-b", None]
    assert matched[0] is not None and matched[0].label == "A"


def test_identity_below_half_is_a_new_theme_and_pairs_are_one_to_one() -> None:
    old = [record("th-a", ["1", "2", "3", "4"])]
    assert match_identities(old, [["1", "10", "11", "12"]], {"1", "10", "11", "12"}) == [None]
    split = match_identities(old, [["1", "2", "3"], ["4", "5"]], {"1", "2", "3", "4", "5"})
    assert [m.id if m else None for m in split] == ["th-a", None]


def test_identity_ignores_stored_members_outside_the_current_scope() -> None:
    old = [record("th-a", ["1", "2", "3", "4", "5", "6"])]
    matched = match_identities(old, [["1", "2", "3"]], {"1", "2", "3"})
    assert matched[0] is not None and matched[0].id == "th-a"


def test_ephemeral_theme_ids_depend_only_on_the_member_set() -> None:
    assert ephemeral_theme_id(["b", "a", "c"]) == ephemeral_theme_id(["c", "a", "b"])
    assert ephemeral_theme_id(["a", "b"]) != ephemeral_theme_id(["a", "c"])
    assert ephemeral_theme_id(["a"]).startswith("th-")


# --- co-occurrence -----------------------------------------------------------------------------


def make_inquiry(
    ident: str,
    occurred_at: str,
    *,
    session: str | None = None,
    client: str | None = None,
) -> Inquiry:
    return Inquiry(
        id=ident,
        text=ident,
        occurred_at=occurred_at,
        captured_at=occurred_at,
        family_id=f"fam-{ident}",
        session_id=session,
        meta={"client_session": client} if client else {},
    )


def test_co_occurrence_counts_same_session_pairs_and_shared_sessions() -> None:
    a = [make_inquiry("a1", "2026-09-01T00:00:00+00:00", session="s1")]
    a.append(make_inquiry("a2", "2026-09-02T00:00:00+00:00", session="s2"))
    b = [make_inquiry("b1", "2026-09-20T00:00:00+00:00", session="s1")]
    b.append(make_inquiry("b2", "2026-09-21T00:00:00+00:00", session="s3"))
    assert co_occurrence(a, b) == (1, 1)


def test_co_occurrence_without_sessions_uses_the_seven_day_window() -> None:
    a = [make_inquiry("a1", "2026-09-10T00:00:00+00:00")]
    near = [make_inquiry("b1", "2026-09-17T00:00:00+00:00")]
    far = [make_inquiry("b2", "2026-09-18T00:00:01+00:00")]
    assert co_occurrence(a, near) == (1, 0)
    assert co_occurrence(a, far) == (0, 0)


def test_co_occurrence_uses_the_client_session_when_there_is_no_cgu_session() -> None:
    a = [make_inquiry("a1", "2026-01-01T00:00:00+00:00", client="cli-1")]
    b = [make_inquiry("b1", "2026-03-01T00:00:00+00:00", client="cli-1")]
    other = [make_inquiry("b2", "2026-01-01T00:00:00+00:00", client="cli-2")]
    assert co_occurrence(a, b) == (1, 1)
    assert co_occurrence(a, other) == (0, 0)


def test_stem_share_is_a_measurement() -> None:
    share = stem_share(3, 12)
    assert isinstance(share, Measurement)
    assert share.value == pytest.approx(0.25) and share.n == 12 and share.calibrated is False
