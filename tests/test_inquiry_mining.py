"""Inquiry memory, mining internals that the service tests cannot reach: bands and the funnel."""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta

import numpy as np

from cgu.domain.inquiry import Inquiry, SourceRecord, build_candidates, ephemeral_theme_id
from cgu.domain.mining import (
    KINDS,
    RANK_RULES,
    ThemeView,
    build_funnel,
    latest_feedback_ideas,
    make_source_id,
    mine_bridges,
)

BASE = datetime(2026, 6, 1, tzinfo=UTC)


def unit(angle_degrees: float) -> list[float]:
    angle = math.radians(angle_degrees)
    return [math.cos(angle), math.sin(angle)]


def build(
    themes: dict[str, tuple[float, list[str | None]]],
) -> tuple[list[ThemeView], dict[str, Inquiry]]:
    """Themes at given angles; each member is (session or None); distinct families and days."""
    inquiries: list[Inquiry] = []
    rows: list[list[float]] = []
    day = 0
    for name, (angle, sessions) in themes.items():
        for k, session in enumerate(sessions):
            when = (BASE + timedelta(days=day * 9)).isoformat()
            day += 1
            inquiries.append(
                Inquiry(
                    id=f"{name}{k}",
                    text=f"{name} question {k}",
                    occurred_at=when,
                    captured_at=when,
                    family_id=f"fam-{name}{k}",
                    session_id=session,
                )
            )
            rows.append(unit(angle + (k - 1) * 2.0))
    matrix = np.asarray(rows)
    candidates, _uncategorized = build_candidates(inquiries, matrix, 0.03, 3)
    views = [
        ThemeView(
            theme_id=ephemeral_theme_id(c.member_ids),
            label=None,
            labeled_by=None,
            persisted=False,
            candidate=c,
        )
        for c in candidates
    ]
    return views, {i.id: i for i in inquiries}


def pair_of(source_facts: dict[str, object], names: dict[str, str]) -> frozenset[str]:
    return frozenset({names[str(source_facts["theme_a"])], names[str(source_facts["theme_b"])]})


def test_bridges_skip_near_themes_and_rank_by_co_occurrence_then_mid_before_far() -> None:
    views, by_id = build(
        {
            "A": (0.0, ["s1", "s2", "s3"]),
            "N": (30.0, ["n1", "n2", "n3"]),
            "M": (60.0, ["s1", "m2", "m3"]),
            "F": (120.0, ["s2", "s3", "f3"]),
        }
    )
    assert len(views) == 4
    names = {v.theme_id: by_id[v.candidate.member_ids[0]].text[0] for v in views}
    found = mine_bridges(views, by_id, limit=10, safe=lambda s: s)
    pairs = [pair_of(s.facts, names) for s in found]
    assert frozenset({"A", "N"}) not in pairs and frozenset({"N", "M"}) not in pairs
    assert len(found) == 4
    assert pairs[0] == frozenset({"A", "F"}), "two shared sessions beat one"
    assert found[0].facts["co_occurrence"] == 2 and found[0].facts["shared_sessions"] == 2
    assert found[0].facts["band"] == "far"
    ties = [s for s in found if s.facts["co_occurrence"] == found[1].facts["co_occurrence"]]
    bands = [s.facts["band"] for s in ties]
    assert bands == sorted(bands, key=lambda b: 0 if b == "mid" else 1)
    for source in found:
        assert source.facts["band"] in {"mid", "far"}
        assert source.measures["centroid_distance"].value >= 0.35
        assert source.source_id.startswith("src-")


def test_bridges_respect_the_limit_and_are_deterministic() -> None:
    views, by_id = build(
        {"A": (0.0, [None] * 3), "M": (60.0, [None] * 3), "F": (120.0, [None] * 3)}
    )
    first = mine_bridges(views, by_id, limit=2, safe=lambda s: s)
    again = mine_bridges(views, by_id, limit=2, safe=lambda s: s)
    assert len(first) == 2 and [s.source_id for s in first] == [s.source_id for s in again]


def test_source_ids_are_stable_for_the_same_evidence_and_differ_otherwise() -> None:
    a = make_source_id("frame", ["i1", "i2"], extra="th-1")
    assert a == make_source_id("frame", ["i1", "i2"], extra="th-1")
    assert a.startswith("src-") and len(a) == len("src-") + 12
    assert a != make_source_id("stalled", ["i1", "i2"], extra="th-1")
    assert a != make_source_id("frame", ["i1", "i3"], extra="th-1")


def test_every_kind_discloses_its_rank_rule() -> None:
    assert set(RANK_RULES) == set(KINDS)
    assert all(rule.strip() for rule in RANK_RULES.values())


def test_latest_feedback_ideas_keeps_the_last_decision_in_order() -> None:
    rows = [
        {"idea_id": "i1", "session_id": "s", "text": "one", "decision": "adopt", "at": "t1"},
        {"idea_id": "i2", "session_id": "s", "text": "two", "decision": "abandon", "at": "t2"},
        {"idea_id": "i1", "session_id": "s", "text": "one", "decision": "modify", "at": "t3"},
        {"idea_id": "i3", "session_id": "s", "text": "", "decision": "adopt", "at": "t4"},
    ]
    ideas = latest_feedback_ideas(rows)
    assert [(i.idea_id, i.decision) for i in ideas] == [("i1", "modify"), ("i2", "abandon")]


def test_funnel_counts_by_kind_and_ignores_unknown_sources() -> None:
    sources = [
        SourceRecord(id="src-a", kind="frame", times_surfaced=2),
        SourceRecord(id="src-b", kind="frame"),
        SourceRecord(id="src-c", kind="dormant"),
    ]
    funnel = build_funnel(
        sources,
        [("i1", "src-a"), ("i2", "src-a"), ("i3", "src-c"), ("i4", "src-gone")],
        {"i1": "adopt", "i2": "abandon", "i3": "modify"},
    )
    frame = funnel["by_kind"]["frame"]
    assert frame["surfaced"] == 2 and frame["times_surfaced"] == 3
    assert frame["turned_into_ideas"] == 2 and frame["sources_with_ideas"] == 1
    assert frame["adopted"] == 1 and frame["abandoned"] == 1 and frame["surfaced_unused"] == 1
    dormant = funnel["by_kind"]["dormant"]
    assert dormant["modified"] == 1 and dormant["surfaced_unused"] == 0
    assert funnel["by_kind"]["bridge"]["surfaced"] == 0
    assert funnel["total"]["surfaced"] == 3 and funnel["total"]["turned_into_ideas"] == 3
    assert funnel["total"]["surfaced_unused"] == 1
    assert "baseline" in funnel["note"]
