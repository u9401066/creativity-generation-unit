"""SQLiteArchive: migrations, cascade, export/delete without residue, isolation, concurrency."""

from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path

import pytest

from cgu.domain.common import Session
from cgu.domain.frame import Assumption, build_frame
from cgu.domain.idea import Fragment, Idea
from cgu.domain.judge import Matchup, Verdict
from cgu.infrastructure.sqlite import MIGRATIONS, TABLES, SQLiteArchive

NOW = "2026-10-02T00:00:00+00:00"


def session(sid: str, seed: int = 1) -> Session:
    return Session(id=sid, topic=f"topic {sid}", seed=seed, created_at=NOW)


async def populate(archive: SQLiteArchive, sid: str) -> None:
    await archive.create_session(session(sid))
    frame = build_frame(
        frame_id=f"f-{sid}",
        session_id=sid,
        problem="p",
        created_at=NOW,
        elements={"assumption": [Assumption(text="a")]},
    )
    await archive.save_frame(frame)
    child = frame.model_copy(update={"frame_id": f"f-{sid}-child", "parent_id": frame.frame_id})
    await archive.save_frame(child)
    await archive.save_ideas(
        [
            Idea(id=f"i-{sid}-1", session_id=sid, text="one", kind="typical", created_at=NOW),
            Idea(id=f"i-{sid}-2", session_id=sid, text="two", kind="candidate", created_at=NOW),
        ]
    )
    await archive.save_fragments(
        [
            Fragment(
                id=f"fr-{sid}",
                session_id=sid,
                text="t",
                fenced_text="<untrusted_data>t</untrusted_data>",
                source_type="web",
                created_at=NOW,
            )
        ]
    )
    matchup = Matchup(
        id=f"m-{sid}",
        session_id=sid,
        idea_a=f"i-{sid}-1",
        idea_b=f"i-{sid}-2",
        criteria=["c"],
        created_at=NOW,
    )
    await archive.save_matchups([matchup])
    await archive.save_verdicts(sid, [Verdict(matchup_id=matchup.id, order="AB", winner="tie")])
    await archive.put_niche(sid, "assumption|unknown", {"idea_id": f"i-{sid}-2"})
    await archive.save_question(sid, {"question": "q", "passed": True})
    await archive.save_feedback(sid, {"idea_id": f"i-{sid}-2", "decision": "adopt"})


def raw_counts(path: Path) -> dict[str, int]:
    conn = sqlite3.connect(path)
    try:
        result = {
            table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("sessions", *TABLES)
        }
    finally:
        conn.close()
    return result


async def test_fresh_database_is_migrated_and_uses_wal(tmp_path: Path) -> None:
    path = tmp_path / "cgu.sqlite3"
    archive = SQLiteArchive(path)
    try:
        assert archive.schema_version == len(MIGRATIONS)
        conn = sqlite3.connect(path)
        assert conn.execute("PRAGMA user_version").fetchone()[0] == len(MIGRATIONS)
        assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        conn.close()
        assert {"sessions", *TABLES} <= names
    finally:
        archive.close()


async def test_reopening_keeps_data_and_does_not_remigrate(tmp_path: Path) -> None:
    path = tmp_path / "cgu.sqlite3"
    first = SQLiteArchive(path)
    await first.create_session(session("s-1"))
    first.close()
    second = SQLiteArchive(path)
    try:
        assert [s.id for s in await second.list_sessions()] == ["s-1"]
        assert second.schema_version == len(MIGRATIONS)
    finally:
        second.close()


async def test_a_newer_database_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "cgu.sqlite3"
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA user_version = 99")
    conn.commit()
    conn.close()
    with pytest.raises(RuntimeError, match="newer"):
        SQLiteArchive(path)


async def test_delete_cascades_and_leaves_no_residue(tmp_path: Path) -> None:
    path = tmp_path / "cgu.sqlite3"
    archive = SQLiteArchive(path)
    try:
        await populate(archive, "s-1")
        await populate(archive, "s-2")
        assert all(raw_counts(path)[table] > 0 for table in TABLES)
        assert await archive.delete_session("s-1") is True
        assert await archive.delete_session("s-1") is False
        after = raw_counts(path)
        assert after["sessions"] == 1
        remaining = await archive.counts("s-2")
        assert after["frames"] == remaining["frames"] == 2
        assert after["ideas"] == remaining["ideas"] == 2
        for table in TABLES:
            assert after[table] == remaining[table]
        assert await archive.counts("s-1") == dict.fromkeys(TABLES, 0)
        await archive.delete_session("s-2")
        assert set(raw_counts(path).values()) == {0}
    finally:
        archive.close()


async def test_export_contains_everything_and_is_session_scoped(tmp_path: Path) -> None:
    archive = SQLiteArchive(tmp_path / "cgu.sqlite3")
    try:
        await populate(archive, "s-1")
        await populate(archive, "s-2")
        dump = await archive.export_session("s-1")
        assert dump["session"]["id"] == "s-1"
        assert len(dump["frames"]) == 2
        assert {i["id"] for i in dump["ideas"]} == {"i-s-1-1", "i-s-1-2"}
        assert len(dump["fragments"]) == len(dump["matchups"]) == len(dump["verdicts"]) == 1
        assert list(dump["niches"]) == ["assumption|unknown"]
        assert len(dump["questions"]) == len(dump["feedback"]) == 1
        assert "s-2" not in str(dump)
    finally:
        archive.close()


async def test_sessions_are_isolated(tmp_path: Path) -> None:
    archive = SQLiteArchive(tmp_path / "cgu.sqlite3")
    try:
        await populate(archive, "s-1")
        await archive.create_session(session("s-2"))
        assert await archive.list_ideas("s-2") == []
        assert [i.id for i in await archive.list_ideas("s-1", "typical")] == ["i-s-1-1"]
        assert await archive.get_niches("s-2") == {}
        assert await archive.list_feedback("s-2") == []
    finally:
        archive.close()


async def test_foreign_keys_are_enforced(tmp_path: Path) -> None:
    archive = SQLiteArchive(tmp_path / "cgu.sqlite3")
    try:
        with pytest.raises(sqlite3.IntegrityError):
            await archive.save_ideas(
                [Idea(id="i-x", session_id="ghost", text="x", kind="human", created_at=NOW)]
            )
    finally:
        archive.close()


async def test_a_judge_cannot_record_the_same_order_twice(tmp_path: Path) -> None:
    archive = SQLiteArchive(tmp_path / "cgu.sqlite3")
    try:
        await populate(archive, "s-1")
        with pytest.raises(sqlite3.IntegrityError):
            await archive.save_verdicts(
                "s-1", [Verdict(matchup_id="m-s-1", order="AB", winner="tie")]
            )
    finally:
        archive.close()


async def test_concurrent_writes_and_counters_are_safe(tmp_path: Path) -> None:
    archive = SQLiteArchive(tmp_path / "cgu.sqlite3")
    try:
        await archive.create_session(session("s-1"))
        await asyncio.gather(
            *[
                archive.save_ideas(
                    [Idea(id=f"i-{n}", session_id="s-1", text=str(n), kind="human", created_at=NOW)]
                )
                for n in range(25)
            ]
        )
        assert len(await archive.list_ideas("s-1")) == 25
        values = await asyncio.gather(
            *[archive.bump_counter("s-1", "evolve_next") for _ in range(20)]
        )
        assert sorted(values) == list(range(1, 21))
    finally:
        archive.close()


async def test_json_round_trip_preserves_models(tmp_path: Path) -> None:
    archive = SQLiteArchive(tmp_path / "cgu.sqlite3")
    try:
        await populate(archive, "s-1")
        frame = await archive.get_frame("f-s-1-child")
        assert frame is not None and frame.parent_id == "f-s-1"
        assert frame.assumptions[0].id == "a1"
        assert await archive.get_frame("nope") is None
        stored = (await archive.list_verdicts("s-1"))[0]
        assert stored.winner == "tie"
    finally:
        archive.close()
