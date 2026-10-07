"""Inquiry memory, service layer: gating, consent, themes, mining, funnel, deletion, vectors."""

from __future__ import annotations

import sqlite3
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from inquiry_support import CLUSTER_DIM, ClusterEmbedding

from cgu.application.services.inquiry import CaptureRequest, InquiryService, ThemeLabel
from cgu.domain.common import CGUError, Session
from cgu.domain.idea import Idea
from cgu.domain.inquiry import InquiryConsent
from cgu.domain.mining import ECHO_CHAMBER_WARNING, LEXICAL_WARNING
from cgu.infrastructure.embedding import NgramHashEmbedding
from cgu.infrastructure.sqlite import SQLiteArchive

NOW = datetime(2026, 10, 3, tzinfo=UTC)
CONSENT = InquiryConsent(granted=True, note="yes, keep them on this machine", via="caller")
WORDS = [
    "alpha",
    "bravo",
    "charlie",
    "delta",
    "echo",
    "foxtrot",
    "golf",
    "hotel",
    "india",
    "juliet",
    "kilo",
    "lima",
    "mike",
    "november",
    "oscar",
    "papa",
]


def day(days_ago: float) -> str:
    return (NOW - timedelta(days=days_ago)).isoformat(timespec="seconds")


@dataclass
class Rig:
    archive: SQLiteArchive
    service: InquiryService
    path: Path


def questions(keyword: str, count: int, *, stem: str = "how can", start: int = 0) -> list[str]:
    """Distinct questions that sit on one keyword axis of the fake semantic embedding."""
    return [
        f"{stem} {keyword} {WORDS[(start + i) % 16]} {WORDS[(start + i * 3 + 5) % 16]} "
        f"{WORDS[(start + i * 5 + 9) % 16]} matter at our hospital"
        for i in range(count)
    ]


@pytest.fixture
async def rig(tmp_path: Path) -> AsyncIterator[Rig]:
    path = tmp_path / "cgu.sqlite3"
    archive = SQLiteArchive(path)
    service = InquiryService(archive, ClusterEmbedding(), clock=lambda: NOW)
    yield Rig(archive, service, path)
    archive.close()


@pytest.fixture
def make_rig(tmp_path: Path) -> Callable[..., Rig]:
    created: list[SQLiteArchive] = []

    def build(embedding: Any = None, name: str = "other.sqlite3") -> Rig:
        path = tmp_path / name
        archive = SQLiteArchive(path)
        created.append(archive)
        service = InquiryService(archive, embedding or NgramHashEmbedding(), clock=lambda: NOW)
        return Rig(archive, service, path)

    yield build
    for archive in created:
        archive.close()


async def enable(rig: Rig) -> None:
    result = await rig.service.settings(enable=True, consent=CONSENT, excluded_projects=None)
    assert result.ok, result.error


async def add(
    rig: Rig,
    texts: list[str],
    *,
    days_ago: float = 1.0,
    step: float = 0.0,
    session_id: str | None = None,
    project: str | None = "demo",
    source: Any = "agent",
) -> list[str]:
    """Capture texts one batch at a time; returns the new inquiry ids."""
    requests = [
        CaptureRequest(
            text=text,
            project=project,
            session_id=session_id,
            source=source,
            occurred_at=day(days_ago + step * i),
        )
        for i, text in enumerate(texts)
    ]
    result = await rig.service.capture(requests, batch=True)
    assert result.ok and result.data["recorded"], result.data
    return [row["id"] for row in result.data["items"]]


async def session(rig: Rig, sid: str, topic: str = "a topic") -> str:
    await rig.archive.create_session(Session(id=sid, topic=topic, seed=1, created_at=day(30)))
    return sid


def tables_snapshot(path: Path) -> dict[str, int]:
    with sqlite3.connect(path) as db:
        names = [
            "inquiries",
            "inquiry_vectors",
            "inquiry_themes",
            "inquiry_sources",
            "inquiry_settings",
        ]
        return {n: int(db.execute(f"SELECT count(*) FROM {n}").fetchone()[0]) for n in names}


# --- default off, consent, gating --------------------------------------------------------------


async def test_capture_defaults_to_off_and_says_why_without_an_error(rig: Rig) -> None:
    result = await rig.service.capture([CaptureRequest(text="how can we?")], batch=False)
    assert result.ok and result.data["recorded"] is False
    assert result.data["reason"] == "consent_not_asked"
    assert result.data["enabled"] is None
    assert tables_snapshot(rig.path)["inquiries"] == 0
    view = (await rig.service.settings(enable=None, consent=None, excluded_projects=None)).data
    assert view["enabled"] is None and view["disclosure"]["never_recorded"]


async def test_enable_needs_consent_and_a_caller_must_quote_the_user(rig: Rig) -> None:
    service = rig.service
    none_given = await service.settings(enable=True, consent=None, excluded_projects=None)
    assert not none_given.ok and none_given.error is not None
    assert none_given.error.code == "consent_required"
    assert none_given.data["requires_consent"] is True and none_given.data["disclosure"]
    no_note = await service.settings(
        enable=True,
        consent=InquiryConsent(granted=True, note="  ", via="caller"),
        excluded_projects=None,
    )
    assert not no_note.ok and no_note.error is not None and no_note.error.code == "consent_required"
    assert (await service.status())["enabled"] is None


async def test_a_refusal_is_remembered_as_disabled_and_a_dismissal_is_not(rig: Rig) -> None:
    service = rig.service
    dismissed = await service.settings(
        enable=True,
        consent=InquiryConsent(granted=False, note="closed", via="elicitation", final=False),
        excluded_projects=None,
    )
    assert not dismissed.ok and (await service.status())["enabled"] is None
    refused = await service.settings(
        enable=True,
        consent=InquiryConsent(granted=False, note="no", via="elicitation"),
        excluded_projects=None,
    )
    assert not refused.ok and refused.data["declined"] is True
    assert (await service.status())["enabled"] is False
    capture = await service.capture([CaptureRequest(text="a question")], batch=False)
    assert capture.ok and capture.data["recorded"] is False and capture.data["reason"] == "disabled"


async def test_enable_records_the_consent_and_disable_needs_none(rig: Rig) -> None:
    await enable(rig)
    view = (await rig.service.settings(enable=None, consent=None, excluded_projects=None)).data
    assert view["enabled"] is True
    assert view["consent"]["via"] == "caller" and view["consent"]["note"] == CONSENT.note
    off = await rig.service.settings(enable=False, consent=None, excluded_projects=None)
    assert off.ok and off.data["enabled"] is False
    again = await rig.service.capture([CaptureRequest(text="after disabling")], batch=False)
    assert again.data["recorded"] is False and again.data["reason"] == "disabled"
    turned_back = await rig.service.settings(enable=True, consent=CONSENT, excluded_projects=None)
    assert turned_back.ok and turned_back.data["enabled"] is True


async def test_excluded_projects_are_not_recorded_and_the_rest_of_a_batch_is(rig: Rig) -> None:
    await enable(rig)
    set_up = await rig.service.settings(
        enable=None, consent=None, excluded_projects=["D:\\work\\Secret", "private"]
    )
    assert set_up.data["excluded_projects"] == ["Secret", "private"]
    single = await rig.service.capture(
        [CaptureRequest(text="a question here", project="secret")], batch=False
    )
    assert single.ok and single.data["recorded"] is False
    assert single.data["reason"] == "excluded_project"
    batch = await rig.service.capture(
        [
            CaptureRequest(text="first question about money", project="private"),
            CaptureRequest(text="second question about money", project="open"),
        ],
        batch=True,
    )
    assert batch.ok and batch.data["recorded"] is True and batch.data["count"] == 1
    assert batch.data["skipped"] == [{"index": 0, "reason": "excluded_project"}]
    assert tables_snapshot(rig.path)["inquiries"] == 1


async def test_capture_redacts_truncates_and_always_states_what_is_not_detected(rig: Rig) -> None:
    await enable(rig)
    text = (
        "請聯絡 me@clinic.example 或 0912-345-678，病人 A123456789，病歷號 12345678，"
        "參考 https://x.test/p?token=1#f 。" + "後" * 2100
    )
    result = await rig.service.capture(
        [CaptureRequest(text=text, project="D:\\work\\ward-study")], batch=False
    )
    assert result.ok and result.data["recorded"] is True
    assert result.data["redactions"] == {"email": 1, "phone": 1, "id": 1, "number": 1, "url": 1}
    assert result.data["truncated"] is True and result.data["project"] == "ward-study"
    assert "姓名" in result.data["redaction_note"] and "臨床" in result.data["redaction_note"]
    stored = (await rig.archive.list_inquiries())[0]
    assert len(stored.text) <= 2000 and "me@clinic" not in stored.text
    assert "0912" not in stored.text and "A123456789" not in stored.text
    assert "12345678" not in stored.text and "token=1" not in stored.text
    assert "[email]" in stored.text and "[phone]" in stored.text and "[id]" in stored.text


async def test_capture_validates_input_and_session_links(rig: Rig) -> None:
    await enable(rig)
    with pytest.raises(CGUError) as empty:
        await rig.service.capture([CaptureRequest(text="   ")], batch=False)
    assert empty.value.code == "invalid_input"
    with pytest.raises(CGUError) as unknown:
        await rig.service.capture([CaptureRequest(text="q", session_id="s-nope")], batch=False)
    assert unknown.value.code == "not_found"
    with pytest.raises(CGUError) as late:
        await rig.service.capture([CaptureRequest(text="q", occurred_at="yesterday")], batch=False)
    assert late.value.code == "invalid_input"
    with pytest.raises(CGUError) as nothing:
        await rig.service.capture([], batch=True)
    assert nothing.value.code == "invalid_input"
    too_many = [CaptureRequest(text=f"question {i}") for i in range(201)]
    with pytest.raises(CGUError) as big:
        await rig.service.capture(too_many, batch=True)
    assert big.value.code == "invalid_input"


async def test_recurrence_is_reported_and_kept_not_discarded(rig: Rig) -> None:
    await enable(rig)
    first = await rig.service.capture(
        [CaptureRequest(text="術前認知篩檢可以預測術後譫妄嗎", occurred_at=day(5))], batch=False
    )
    second = await rig.service.capture(
        [CaptureRequest(text="術前認知篩檢可以預測術後譫妄嗎？", occurred_at=day(2))], batch=False
    )
    other = await rig.service.capture(
        [CaptureRequest(text="money 完全不同的行政流程問題", occurred_at=day(1))], batch=False
    )
    assert first.data["recurrence"] == {"of": None, "count": 1, "similarity": None}
    assert second.data["family_id"] == first.data["family_id"]
    assert second.data["recurrence"]["count"] == 2
    assert second.data["recurrence"]["of"] == first.data["id"]
    similarity = second.data["recurrence"]["similarity"]
    assert similarity["value"] >= 0.8 and similarity["calibrated"] is False
    assert other.data["family_id"] != first.data["family_id"]
    assert tables_snapshot(rig.path)["inquiries"] == 3


# --- vectors: float32 blobs keyed by backend, never mixed ----------------------------------------


async def test_vectors_are_float32_blobs_keyed_by_backend(rig: Rig) -> None:
    await enable(rig)
    ids = await add(rig, questions("drug", 2))
    with sqlite3.connect(rig.path) as db:
        rows = db.execute("SELECT inquiry_id, backend, dim, vec FROM inquiry_vectors").fetchall()
    assert sorted(r[0] for r in rows) == sorted(ids)
    assert {r[1] for r in rows} == {"fake-clusters"}
    for _id, _backend, dim, blob in rows:
        assert dim == CLUSTER_DIM and len(blob) == dim * 4
        assert np.frombuffer(blob, dtype=np.float32).shape == (CLUSTER_DIM,)


async def test_switching_backend_recomputes_instead_of_mixing(tmp_path: Path) -> None:
    path = tmp_path / "mix.sqlite3"
    archive = SQLiteArchive(path)
    try:
        semantic = InquiryService(archive, ClusterEmbedding(), clock=lambda: NOW)
        rig = Rig(archive, semantic, path)
        await enable(rig)
        await add(rig, questions("drug", 3) + questions("device", 3), step=0.5)
        await semantic.themes(min_size=None, threshold=None, project=None, since_days=None)
        lexical = InquiryService(archive, NgramHashEmbedding(), clock=lambda: NOW)
        out = await lexical.themes(min_size=None, threshold=None, project=None, since_days=None)
        assert out.ok and out.data["embedding"]["semantic"] is False
        with sqlite3.connect(path) as db:
            per_backend = dict(
                db.execute(
                    "SELECT backend, count(*) FROM inquiry_vectors GROUP BY backend"
                ).fetchall()
            )
        assert per_backend == {"fake-clusters": 6, "ngram-hash": 6}
        with sqlite3.connect(path) as db:
            dims = {r[0] for r in db.execute("SELECT DISTINCT dim FROM inquiry_vectors")}
        assert len(dims) == 2
    finally:
        archive.close()


# --- themes: stable identity, deletion ----------------------------------------------------------


async def three_themes(rig: Rig) -> dict[str, list[str]]:
    await enable(rig)
    ids = {
        "drug": await add(rig, questions("drug", 4), days_ago=10, step=0.5),
        "device": await add(rig, questions("device", 4), days_ago=9, step=0.5),
        "nurse": await add(rig, questions("nurse", 3), days_ago=8, step=0.5),
    }
    return ids


async def themes_of(rig: Rig, **kwargs: Any) -> list[dict[str, Any]]:
    args: dict[str, Any] = {"min_size": None, "threshold": None, "project": None}
    args.update({"since_days": None, **kwargs})
    result = await rig.service.themes(**args)
    assert result.ok
    return list(result.data["themes"])


async def test_themes_group_by_family_and_unnamed_themes_get_a_label_work_order(rig: Rig) -> None:
    await three_themes(rig)
    result = await rig.service.themes(min_size=None, threshold=None, project=None, since_days=None)
    assert result.ok and len(result.data["themes"]) == 3
    assert {t["families"] for t in result.data["themes"]} == {3, 4}
    assert all(t["persisted"] and t["label"] is None for t in result.data["themes"])
    assert len(result.work_orders) == 3
    assert {o.kind for o in result.work_orders} == {"inquiry_label"}
    assert result.data["threshold"]["calibrated"] is False
    assert result.data["uncategorized"] == 0
    assert result.provenance.engine == "heuristic"
    assert LEXICAL_WARNING not in result.provenance.warnings


async def test_theme_identity_label_and_membership_survive_recomputation(rig: Rig) -> None:
    ids = await three_themes(rig)
    first = await themes_of(rig)
    by_exemplar = {t["exemplars"][0]["text"].split()[2]: t for t in first}
    drug = by_exemplar["drug"]
    labeled = await rig.service.label([ThemeLabel(theme_id=drug["theme_id"], label="藥物問題")])
    assert labeled.ok and labeled.data["labeled"] == [drug["theme_id"]]
    await add(rig, questions("drug", 2, start=7), days_ago=3, step=0.5)
    await add(rig, questions("paper", 3), days_ago=2, step=0.5)
    second = await themes_of(rig)
    assert len(second) == 4
    survivors = {t["theme_id"]: t for t in second}
    for old in first:
        assert old["theme_id"] in survivors, "theme ids must be stable across recomputation"
    assert survivors[drug["theme_id"]]["label"] == "藥物問題"
    assert survivors[drug["theme_id"]]["labeled_by"] == "caller"
    assert survivors[drug["theme_id"]]["families"] == drug["families"] + 2
    new_ids = set(survivors) - {t["theme_id"] for t in first}
    assert len(new_ids) == 1
    stored = {t.id: t for t in await rig.archive.list_themes()}
    assert set(stored) == set(survivors)
    assert set(stored[drug["theme_id"]].member_ids) >= set(ids["drug"])


async def test_label_rejects_unknown_themes_and_bad_labels(rig: Rig) -> None:
    await three_themes(rig)
    theme_id = (await themes_of(rig))[0]["theme_id"]
    with pytest.raises(CGUError) as unknown:
        await rig.service.label([ThemeLabel(theme_id="th-nope", label="x")])
    assert unknown.value.code == "not_found"
    with pytest.raises(CGUError) as blank:
        await rig.service.label([ThemeLabel(theme_id=theme_id, label="   ")])
    assert blank.value.code == "invalid_input"
    with pytest.raises(CGUError) as nothing:
        await rig.service.label(None)
    assert nothing.value.code == "invalid_input"


async def test_filtered_or_custom_views_are_ephemeral_and_leave_stored_themes_alone(
    rig: Rig,
) -> None:
    await three_themes(rig)
    stored = await themes_of(rig)
    narrow = await rig.service.themes(min_size=2, threshold=None, project=None, since_days=None)
    assert narrow.ok and narrow.data["themes"]
    assert any("暫時檢視" in w for w in narrow.provenance.warnings)
    stored_ids = {t["theme_id"] for t in stored}
    assert all(order.inputs["theme_id"] in stored_ids for order in narrow.work_orders)
    scoped = await rig.service.themes(
        min_size=None, threshold=None, project="nowhere", since_days=1
    )
    assert scoped.ok and scoped.data["themes"] == []
    assert {t.id for t in await rig.archive.list_themes()} == stored_ids


async def test_deleting_inquiries_updates_theme_members_and_drops_small_themes(rig: Rig) -> None:
    ids = await three_themes(rig)
    stored = {t["theme_id"]: t for t in await themes_of(rig)}
    assert len(stored) == 3
    gone = ids["drug"][0]
    result = await rig.service.delete(
        ids=[gone], project=None, older_than_days=None, everything=False, confirm=True
    )
    assert result.ok and result.data["deleted"] == 1 and result.data["themes_removed"] == 0
    for theme in await rig.archive.list_themes():
        assert gone not in theme.member_ids
    nurse = ids["nurse"]
    shrunk = await rig.service.delete(
        ids=nurse[:1], project=None, older_than_days=None, everything=False, confirm=True
    )
    assert shrunk.data["deleted"] == 1 and shrunk.data["themes_removed"] == 1
    remaining = await rig.archive.list_themes()
    assert len(remaining) == 2
    assert not any(set(t.member_ids) & set(nurse) for t in remaining)


# --- delete: confirm, no residue, cascade ------------------------------------------------------


async def test_delete_requires_a_selector_and_confirm_true(rig: Rig) -> None:
    await three_themes(rig)
    with pytest.raises(CGUError) as no_confirm:
        await rig.service.delete(
            ids=None, project=None, older_than_days=None, everything=True, confirm=False
        )
    assert no_confirm.value.code == "invalid_input" and "confirm" in no_confirm.value.message
    with pytest.raises(CGUError) as no_selector:
        await rig.service.delete(
            ids=None, project=None, older_than_days=None, everything=False, confirm=True
        )
    assert no_selector.value.code == "invalid_input"
    with pytest.raises(CGUError) as mixed:
        await rig.service.delete(
            ids=["x"], project=None, older_than_days=None, everything=True, confirm=True
        )
    assert mixed.value.code == "invalid_input"
    assert tables_snapshot(rig.path)["inquiries"] == 11


async def test_delete_all_leaves_no_residue_in_vectors_themes_or_sources(rig: Rig) -> None:
    await three_themes(rig)
    await themes_of(rig)
    mined = await rig.service.mine(kinds=["frame", "stalled"], limit=5, project=None)
    assert mined.ok and mined.data["sources"]
    before = tables_snapshot(rig.path)
    assert before["inquiries"] == 11 and before["inquiry_vectors"] == 11
    assert before["inquiry_themes"] == 3 and before["inquiry_sources"] >= 1
    result = await rig.service.delete(
        ids=None, project=None, older_than_days=None, everything=True, confirm=True
    )
    assert result.ok and result.data["deleted"] == 11 and result.data["remaining"] == 0
    after = tables_snapshot(rig.path)
    assert after["inquiries"] == after["inquiry_vectors"] == 0
    assert after["inquiry_themes"] == after["inquiry_sources"] == 0
    assert after["inquiry_settings"] >= 1, "the user's consent choice is a setting, not a question"
    raw = rig.path.read_bytes()
    assert b"hotel" not in raw and b"matter at our hospital" not in raw


async def test_delete_by_id_removes_sources_that_cite_the_question_and_keeps_the_rest(
    rig: Rig,
) -> None:
    ids = await three_themes(rig)
    await themes_of(rig)
    mined = await rig.service.mine(kinds=["frame"], limit=5, project=None)
    sources = {s["source_id"]: s for s in mined.data["sources"]}
    assert len(sources) == 3
    cited = {e["inquiry_id"] for e in next(iter(sources.values()))["evidence"]}
    victim = sorted(cited)[0]
    result = await rig.service.delete(
        ids=[victim], project=None, older_than_days=None, everything=False, confirm=True
    )
    assert result.data["sources_removed"] >= 1
    kept = {s.id for s in await rig.archive.list_sources()}
    assert kept < set(sources)
    for source in await rig.archive.list_sources():
        assert victim not in source.data["evidence_ids"]
    assert ids["drug"]  # the fixture ids are still there for other questions


async def test_delete_by_project_and_age(rig: Rig) -> None:
    await enable(rig)
    await add(rig, questions("drug", 2), days_ago=40, project="old-project")
    await add(rig, questions("device", 2), days_ago=2, project="new-project")
    aged = await rig.service.delete(
        ids=None, project=None, older_than_days=30, everything=False, confirm=True
    )
    assert aged.data["deleted"] == 2 and aged.data["remaining"] == 2
    by_project = await rig.service.delete(
        ids=None, project="D:\\x\\new-project", older_than_days=None, everything=False, confirm=True
    )
    assert by_project.data["deleted"] == 2 and by_project.data["remaining"] == 0


async def test_deleting_a_session_removes_its_inquiries_vectors_and_theme_members(rig: Rig) -> None:
    await enable(rig)
    linked = await session(rig, "s-linked")
    await add(rig, questions("drug", 3), session_id=linked, days_ago=4, step=0.5)
    free = await add(rig, questions("device", 3), days_ago=3, step=0.5)
    await themes_of(rig)
    assert len(await rig.archive.list_themes()) == 2
    assert await rig.archive.delete_session(linked)
    snapshot = tables_snapshot(rig.path)
    assert snapshot["inquiries"] == 3 and snapshot["inquiry_vectors"] == 3
    themes = await rig.archive.list_themes()
    assert len(themes) == 1 and set(themes[0].member_ids) == set(free)
    assert await rig.archive.get_session(linked) is None


async def test_a_session_export_carries_only_its_own_inquiries(rig: Rig) -> None:
    await enable(rig)
    linked = await session(rig, "s-one")
    ids = await add(rig, questions("drug", 2), session_id=linked)
    await add(rig, questions("device", 2))
    exported = await rig.archive.export_session(linked)
    assert sorted(row["id"] for row in exported["inquiries"]) == sorted(ids)


# --- list / export -------------------------------------------------------------------------------


async def test_list_and_export_show_everything_stored(rig: Rig) -> None:
    await three_themes(rig)
    out = await rig.service.list_items(
        project=None, since_days=None, theme_id=None, limit=4, offset=0
    )
    assert out.data["count"] == 4 and out.data["total"] == 11 and out.data["has_more"] is True
    rest = await rig.service.list_items(
        project=None, since_days=None, theme_id=None, limit=50, offset=8
    )
    assert rest.data["count"] == 3 and rest.data["has_more"] is False
    recent = await rig.service.list_items(
        project=None, since_days=9, theme_id=None, limit=None, offset=0
    )
    assert recent.data["total"] == 4
    theme_id = (await themes_of(rig))[0]["theme_id"]
    by_theme = await rig.service.list_items(
        project=None, since_days=None, theme_id=theme_id, limit=None, offset=0
    )
    assert 3 <= by_theme.data["total"] <= 4
    with pytest.raises(CGUError):
        await rig.service.list_items(
            project=None, since_days=None, theme_id="th-x", limit=1, offset=0
        )
    with pytest.raises(CGUError):
        await rig.service.list_items(
            project=None, since_days=None, theme_id=None, limit=0, offset=0
        )
    exported = await rig.service.export(None)
    assert exported.data["count"] == 11 and len(exported.data["inquiries"]) == 11
    assert exported.data["settings"]["enabled"] is True
    assert {"id", "text", "occurred_at", "family_id", "redactions", "meta"} <= set(
        exported.data["inquiries"][0]
    )


# --- mine: the four kinds ------------------------------------------------------------------------


async def mined(rig: Rig, kind: str, **kwargs: Any) -> list[dict[str, Any]]:
    result = await rig.service.mine(kinds=[kind], limit=kwargs.pop("limit", 5), project=None)
    assert result.ok, result.error
    return list(result.data["sources"])


async def test_mine_always_carries_the_echo_chamber_warning_and_the_lexical_one_when_needed(
    rig: Rig, make_rig: Callable[..., Rig]
) -> None:
    empty = await rig.service.mine(kinds=None, limit=None, project=None)
    assert empty.ok and ECHO_CHAMBER_WARNING in empty.provenance.warnings
    assert empty.data["reference_size"] == 0 and empty.data["sources"] == []
    await three_themes(rig)
    full = await rig.service.mine(kinds=None, limit=None, project=None)
    assert ECHO_CHAMBER_WARNING in full.provenance.warnings
    assert LEXICAL_WARNING not in full.provenance.warnings
    assert set(full.data["rank_rules"]) == {"frame", "bridge", "stalled", "dormant"}
    lexical = make_rig()
    await enable(lexical)
    await add(lexical, questions("drug", 6), step=0.3)
    plain = await lexical.service.mine(kinds=["frame"], limit=None, project=None)
    assert ECHO_CHAMBER_WARNING in plain.provenance.warnings
    assert LEXICAL_WARNING in plain.provenance.warnings
    assert plain.data["embedding"]["semantic"] is False


async def test_mine_rejects_unknown_kinds_and_bad_limits(rig: Rig) -> None:
    with pytest.raises(CGUError):
        await rig.service.mine(kinds=["frames"], limit=None, project=None)
    with pytest.raises(CGUError):
        await rig.service.mine(kinds=["frame"], limit=0, project=None)


async def test_frame_trigger_fact_title_and_explicate_work_order(rig: Rig) -> None:
    await enable(rig)
    await add(rig, questions("drug", 4, stem="why does"), days_ago=6, step=0.5)
    await add(rig, questions("drug", 2, stem="what if", start=9), days_ago=3, step=0.5)
    result = await rig.service.mine(kinds=["frame"], limit=None, project=None)
    assert result.ok and len(result.data["sources"]) == 1
    source = result.data["sources"][0]
    assert source["kind"] == "frame" and source["source_id"].startswith("src-")
    assert source["facts"]["top_stem"] == "why does" and source["facts"]["top_stem_count"] == 4
    assert source["facts"]["families"] == 6 and source["facts"]["size"] == 6
    share = source["measures"]["top_stem_share"]
    assert share["value"] == pytest.approx(4 / 6) and share["n"] == 6
    assert share["calibrated"] is False
    assert "4/6" in source["title"] and "「why does」" in source["title"]
    assert "分數" not in source["title"] and "score" not in str(source["measures"]).lower()
    assert source["evidence"] and {"inquiry_id", "text", "occurred_at"} <= set(
        source["evidence"][0]
    )
    assert source["next"][0]["tool"] == "cgu_session"
    assert source["next"][1]["tool"] == "cgu_frame" and source["next"][1]["action"] == "create"
    assumptions = source["next"][1]["args"]["assumptions"]
    assert assumptions[0]["source"] == "abduced_from_user_questions"
    order = result.work_orders[0]
    assert order.kind == "inquiry_explicate"
    assert order.submit_with["tool"] == "cgu_frame" and order.submit_with["action"] == "create"
    assert "abduced_from_user_questions" in str(order.output_schema) + order.instructions
    assert order.inputs["source_id"] == source["source_id"]
    assert 3 <= len(order.inputs["questions"]) <= 8


async def test_frame_does_not_trigger_below_the_minimum_theme_size(rig: Rig) -> None:
    await enable(rig)
    await add(rig, questions("drug", 2), step=0.5)
    await add(rig, questions("device", 2), step=0.5)
    result = await rig.service.mine(kinds=["frame"], limit=None, project=None)
    assert result.ok and result.data["sources"] == [] and result.work_orders == []
    assert result.data["counts_by_kind"] == {"frame": 0}


async def test_frames_are_ranked_by_stem_share_and_limited(rig: Rig) -> None:
    await enable(rig)
    await add(rig, questions("drug", 4, stem="why does"), days_ago=6, step=0.5)
    await add(rig, questions("device", 3, stem="how can"), days_ago=5, step=0.5)
    await add(rig, questions("nurse", 3, stem="could we"), days_ago=4, step=0.5)
    await add(rig, questions("nurse", 1, stem="what if", start=8), days_ago=3)
    top = await mined(rig, "frame", limit=2)
    assert len(top) == 2
    shares = [s["measures"]["top_stem_share"]["value"] for s in top]
    assert shares == sorted(shares, reverse=True)
    assert top[0]["facts"]["top_stem_count"] / top[0]["facts"]["families"] == pytest.approx(1.0)


async def link_themes(rig: Rig, kinds: list[str], sessions: int) -> None:
    """One question of each kind in `sessions` shared sessions (own words avoid the base ones)."""
    for k in range(sessions):
        sid = await session(rig, f"s-bridge-{k}")
        await add(rig, questions(kinds[0], 1, start=8 + 2 * k), session_id=sid, days_ago=20 - k)
        await add(rig, questions(kinds[1], 1, start=1 + 2 * k), session_id=sid, days_ago=20 - k)


async def test_bridge_trigger_ranking_and_non_trigger(rig: Rig) -> None:
    await enable(rig)
    await add(rig, questions("drug", 4), days_ago=80, step=0.5)
    assert await mined(rig, "bridge") == [], "one theme has nothing to bridge"
    await add(rig, questions("paper", 3), days_ago=60, step=0.5)
    await link_themes(rig, ["drug", "device"], 3)
    await add(rig, questions("device", 2, start=8), days_ago=50, step=0.5)
    found = await mined(rig, "bridge")
    assert found, "distant themes that co-occur in sessions are bridge candidates"
    top = found[0]
    assert top["facts"]["band"] in {"mid", "far"}
    assert top["facts"]["co_occurrence"] >= 3 and top["facts"]["shared_sessions"] == 3
    distance = top["measures"]["centroid_distance"]
    assert distance["calibrated"] is False and distance["value"] > 0.5
    assert str(top["facts"]["co_occurrence"]) in top["title"]
    pair = {top["facts"]["theme_a"], top["facts"]["theme_b"]}
    assert len(pair) == 2 and all("theme_id" in e for e in top["evidence"])
    co = [s["facts"]["co_occurrence"] for s in found]
    assert co == sorted(co, reverse=True), "ranked by co_occurrence, descending"
    assert top["next"][-2]["tool"] == "cgu_diverge" and top["next"][-2]["action"] == "collide"


async def test_bridge_needs_two_themes_so_one_big_theme_gives_none(rig: Rig) -> None:
    await enable(rig)
    await add(rig, questions("drug", 3), step=0.5, days_ago=5)
    await add(rig, questions("drug", 3, stem="what if", start=8), step=0.5, days_ago=4)
    found = await mined(rig, "bridge")
    assert found == []


async def stalled_setup(
    rig: Rig, *, days: int = 4, sessions: bool = True, adopt: bool = False
) -> list[str]:
    await enable(rig)
    ids: list[str] = []
    for k in range(days):
        sid = await session(rig, f"s-stall-{k}") if sessions else None
        ids += await add(rig, questions("nurse", 1, start=k), session_id=sid, days_ago=10 - 2 * k)
    if adopt:
        await rig.archive.save_ideas(
            [Idea(id="i-win", session_id="s-stall-1", text="a good idea", kind="candidate")]
        )
        await rig.archive.save_feedback(
            "s-stall-1", {"idea_id": "i-win", "decision": "adopt", "reasons": [], "note": None}
        )
    return ids


async def test_stalled_trigger_with_evidence_quality(rig: Rig) -> None:
    await stalled_setup(rig)
    found = await mined(rig, "stalled")
    assert len(found) == 1
    source = found[0]
    assert source["facts"]["distinct_days"] == 4 and source["facts"]["families"] == 4
    assert source["facts"]["linked_inquiries"] == 4 and source["facts"]["weak_evidence"] is False
    quality = source["measures"]["evidence_quality"]
    assert quality["value"] == pytest.approx(1.0) and quality["calibrated"] is False
    assert "4 天" in source["title"] and "證據弱" not in source["title"]
    assert source["next"][-1]["args"]["signals"] == {"stalled_rounds": 4}


async def test_stalled_says_the_evidence_is_weak_when_few_questions_are_linked(rig: Rig) -> None:
    await enable(rig)
    sid = await session(rig, "s-one-link")
    await add(rig, questions("nurse", 1), session_id=sid, days_ago=9)
    for k in range(1, 5):
        await add(rig, questions("nurse", 1, start=k), days_ago=9 - 2 * k)
    found = await mined(rig, "stalled")
    assert len(found) == 1 and found[0]["facts"]["weak_evidence"] is True
    quality = found[0]["measures"]["evidence_quality"]["value"]
    assert quality == pytest.approx(1 / 5) and "證據弱" in found[0]["title"]


async def test_stalled_does_not_trigger_when_a_linked_session_adopted_an_idea(rig: Rig) -> None:
    await stalled_setup(rig, adopt=True)
    assert await mined(rig, "stalled") == []


async def test_stalled_does_not_trigger_on_too_few_days_or_families(rig: Rig) -> None:
    await stalled_setup(rig, days=2)
    assert await mined(rig, "stalled") == []


async def test_stalled_needs_three_distinct_days_not_just_three_questions(rig: Rig) -> None:
    await enable(rig)
    await add(rig, questions("nurse", 4), days_ago=5, step=0.01)
    assert await mined(rig, "stalled") == []


async def dormant_setup(
    rig: Rig, *, question_days_ago: float, decision: str = "abandon", same_session: bool = False
) -> None:
    await enable(rig)
    old = await session(rig, "s-old", "an older exploration")
    other = await session(rig, "s-new", "a newer chat")
    await rig.archive.save_ideas(
        [
            Idea(
                id="i-dormant",
                session_id=old,
                text="drug dosing plan for older patients",
                kind="candidate",
                created_at=day(60),
            )
        ]
    )
    await rig.archive.save_feedback(
        old, {"idea_id": "i-dormant", "decision": decision, "reasons": [], "note": None}
    )
    await add(
        rig,
        ["how do we dose a drug for older patients in the ward"],
        session_id=old if same_session else other,
        days_ago=question_days_ago,
    )


async def test_dormant_trigger_within_the_14_day_window(rig: Rig) -> None:
    await dormant_setup(rig, question_days_ago=13)
    found = await mined(rig, "dormant")
    assert len(found) == 1
    source = found[0]
    assert source["facts"]["idea_id"] == "i-dormant" and source["facts"]["days_ago"] == 13
    assert source["facts"]["idea_decision"] == "abandon"
    similarity = source["measures"]["similarity"]
    assert similarity["value"] >= 0.6 and similarity["calibrated"] is False
    assert "放棄" in source["title"] and "13 天前" in source["title"]
    assert source["next"][1]["tool"] == "cgu_ideas"
    assert source["next"][1]["args"]["ideas"][0]["kind"] == "human"


async def test_dormant_does_not_trigger_outside_the_14_day_window(rig: Rig) -> None:
    await dormant_setup(rig, question_days_ago=15)
    assert await mined(rig, "dormant") == []


async def test_dormant_covers_modified_ideas_but_never_adopted_ones(rig: Rig) -> None:
    await dormant_setup(rig, question_days_ago=2, decision="modify")
    assert len(await mined(rig, "dormant")) == 1


async def test_dormant_ignores_adopted_ideas_and_same_session_questions(
    rig: Rig, make_rig: Callable[..., Rig]
) -> None:
    await dormant_setup(rig, question_days_ago=2, decision="adopt")
    assert await mined(rig, "dormant") == []
    other = make_rig(ClusterEmbedding(), "same-session.sqlite3")
    await dormant_setup(other, question_days_ago=2, same_session=True)
    assert await mined(other, "dormant") == []


async def test_mine_records_surfaced_sources_idempotently_and_counts_surfacings(rig: Rig) -> None:
    await stalled_setup(rig)
    first = await mined(rig, "stalled")
    again = await mined(rig, "stalled")
    assert [s["source_id"] for s in first] == [s["source_id"] for s in again]
    stored = await rig.archive.list_sources()
    assert len(stored) == 1 and stored[0].id == first[0]["source_id"]
    assert stored[0].times_surfaced == 2
    assert stored[0].first_surfaced_at <= stored[0].last_surfaced_at
    assert tables_snapshot(rig.path)["inquiry_sources"] == 1


# --- funnel ---------------------------------------------------------------------------------------


async def test_funnel_counts_surfaced_turned_into_ideas_and_decisions_by_kind(rig: Rig) -> None:
    await three_themes(rig)
    result = await rig.service.mine(kinds=["frame"], limit=3, project=None)
    sources = result.data["sources"]
    assert len(sources) == 3
    funnel = (await rig.service.settings(enable=None, consent=None, excluded_projects=None)).data[
        "funnel"
    ]
    assert funnel["by_kind"]["frame"]["surfaced"] == 3
    assert funnel["by_kind"]["frame"]["turned_into_ideas"] == 0
    assert funnel["by_kind"]["frame"]["surfaced_unused"] == 3, "the baseline counts as well"
    chat = await session(rig, "s-chat")
    await rig.archive.save_ideas(
        [
            Idea(
                id=f"i-{k}",
                session_id=chat,
                text=f"idea {k}",
                kind="candidate",
                meta={"from_source": sources[k]["source_id"]},
            )
            for k in range(2)
        ]
        + [Idea(id="i-free", session_id=chat, text="no source", kind="candidate")]
    )
    for idea_id, decision in (("i-0", "adopt"), ("i-1", "abandon"), ("i-free", "adopt")):
        await rig.archive.save_feedback(
            chat, {"idea_id": idea_id, "decision": decision, "reasons": [], "note": None}
        )
    await rig.service.mine(kinds=["frame"], limit=3, project=None)
    funnel = (await rig.service.settings(enable=None, consent=None, excluded_projects=None)).data[
        "funnel"
    ]
    row = funnel["by_kind"]["frame"]
    assert row["surfaced"] == 3 and row["times_surfaced"] == 6
    assert row["turned_into_ideas"] == 2 and row["sources_with_ideas"] == 2
    assert row["adopted"] == 1 and row["abandoned"] == 1 and row["modified"] == 0
    assert row["surfaced_unused"] == 1
    assert funnel["total"]["adopted"] == 1 and funnel["by_kind"]["bridge"]["surfaced"] == 0


async def test_the_latest_decision_per_idea_is_the_one_that_counts(rig: Rig) -> None:
    await three_themes(rig)
    sources = (await rig.service.mine(kinds=["frame"], limit=1, project=None)).data["sources"]
    chat = await session(rig, "s-chat")
    await rig.archive.save_ideas(
        [
            Idea(
                id="i-flip",
                session_id=chat,
                text="an idea",
                kind="candidate",
                meta={"from_source": sources[0]["source_id"]},
            )
        ]
    )
    for decision in ("adopt", "abandon"):
        await rig.archive.save_feedback(
            chat, {"idea_id": "i-flip", "decision": decision, "reasons": [], "note": None}
        )
    funnel = (await rig.service.settings(enable=None, consent=None, excluded_projects=None)).data[
        "funnel"
    ]
    row = funnel["by_kind"]["frame"]
    assert row["abandoned"] == 1 and row["adopted"] == 0


# --- settings view, coverage ---------------------------------------------------------------------


async def test_settings_reports_counts_coverage_channels_and_never_a_creativity_score(
    rig: Rig,
) -> None:
    await three_themes(rig)
    await add(rig, questions("paper", 2), source="hook", days_ago=2, step=0.5)
    view = (await rig.service.settings(enable=None, consent=None, excluded_projects=None)).data
    assert view["counts"]["inquiries"] == 13 and view["counts"]["themes"] == 3
    assert view["sources_by_channel"] == {"agent": 11, "hook": 2, "import": 0, "manual": 0}
    coverage = view["coverage"]
    assert coverage["inquiries"] == 13 and coverage["families"] == 13
    assert coverage["projects"] == 1 and coverage["distinct_days"] >= 5
    assert set(coverage["bridge_candidates"]) == {"near", "mid", "far"}
    assert "creativity" not in str(view).lower().replace("not more creativity", "")
    assert view["funnel"]["total"]["surfaced"] == 0


# --- related -------------------------------------------------------------------------------------


async def test_related_with_no_data_is_empty_and_says_so(rig: Rig) -> None:
    result = await rig.service.related("drug dosing", None)
    assert (
        result.ok and result.data["reference_size"] == 0 and result.data["similar_inquiries"] == []
    )
    with pytest.raises(CGUError):
        await rig.service.related("   ", None)
    with pytest.raises(CGUError):
        await rig.service.related("q", 99)


async def test_related_returns_similar_questions_and_cross_session_idea_decisions(
    rig: Rig,
) -> None:
    await enable(rig)
    await add(rig, questions("drug", 3), days_ago=5, step=0.5)
    await add(rig, questions("device", 2), days_ago=4, step=0.5)
    old = await session(rig, "s-ideas", "drug exploration")
    await rig.archive.save_ideas(
        [
            Idea(id="i-yes", session_id=old, text="drug protocol", kind="candidate"),
            Idea(id="i-no", session_id=old, text="drug label redesign", kind="candidate"),
            Idea(id="i-dev", session_id=old, text="device idea", kind="candidate"),
        ]
    )
    for idea_id, decision in (("i-yes", "adopt"), ("i-no", "abandon"), ("i-dev", "adopt")):
        await rig.archive.save_feedback(
            old, {"idea_id": idea_id, "decision": decision, "reasons": [], "note": None}
        )
    result = await rig.service.related("a new drug question for the ward", 5)
    assert result.ok
    similar = result.data["similar_inquiries"]
    assert len(similar) == 3 and all("drug" in s["text"] for s in similar)
    assert similar[0]["similarity"]["calibrated"] is False and similar[0]["days_ago"] >= 4
    assert similar[0]["recurrence"]["count"] == 1
    assert [i["idea_id"] for i in result.data["adopted_ideas"]] == ["i-yes"]
    assert [i["idea_id"] for i in result.data["abandoned_ideas"]] == ["i-no"]
    assert result.data["reference_size"] == 5 and result.data["idea_reference_size"] == 3
    payload = result.data["ideas_payload"]
    assert all(p["kind"] == "human" for p in payload)
    assert any("from_inquiry" in p["meta"] for p in payload)
    assert {p["meta"]["decision"] for p in payload if "decision" in p["meta"]} == {
        "adopt",
        "abandon",
    }
