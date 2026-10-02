"""SQLite archive: WAL, user_version migrations, one locked connection used off the event loop."""

from __future__ import annotations

import asyncio
import functools
import json
import sqlite3
import threading
from collections.abc import Callable, Coroutine, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Concatenate, ParamSpec, TypeVar

from cgu.domain.common import Session
from cgu.domain.frame import Frame
from cgu.domain.idea import Fragment, Idea
from cgu.domain.judge import Matchup, Verdict

SCHEMA_V1 = """
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    topic TEXT NOT NULL,
    domain TEXT,
    language TEXT NOT NULL,
    seed INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    meta TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE frames (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    parent_id TEXT REFERENCES frames(id) ON DELETE CASCADE,
    operator TEXT,
    json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE ideas (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE fragments (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    source_type TEXT NOT NULL,
    json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE matchups (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE verdicts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    matchup_id TEXT NOT NULL,
    ord TEXT NOT NULL,
    judge TEXT NOT NULL,
    json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (session_id, matchup_id, ord, judge)
);
CREATE TABLE niches (
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    niche TEXT NOT NULL,
    json TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (session_id, niche)
);
CREATE TABLE questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    passed INTEGER NOT NULL,
    json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    idea_id TEXT NOT NULL,
    decision TEXT NOT NULL,
    json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX idx_frames_session ON frames(session_id);
CREATE INDEX idx_ideas_session ON ideas(session_id, kind);
CREATE INDEX idx_fragments_session ON fragments(session_id);
CREATE INDEX idx_matchups_session ON matchups(session_id);
CREATE INDEX idx_verdicts_session ON verdicts(session_id);
CREATE INDEX idx_feedback_session ON feedback(session_id);
"""
MIGRATIONS: tuple[str, ...] = (SCHEMA_V1,)
TABLES = (
    "frames",
    "ideas",
    "fragments",
    "matchups",
    "verdicts",
    "niches",
    "questions",
    "feedback",
)

P = ParamSpec("P")
R = TypeVar("R")


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def migrate(conn: sqlite3.Connection) -> int:
    version = int(conn.execute("PRAGMA user_version").fetchone()[0])
    if version > len(MIGRATIONS):
        raise RuntimeError(
            f"database schema v{version} is newer than this CGU (v{len(MIGRATIONS)})"
        )
    for number, script in enumerate(MIGRATIONS[version:], start=version + 1):
        conn.executescript(script)
        conn.execute(f"PRAGMA user_version = {number}")
        conn.commit()
    return len(MIGRATIONS)


def threaded(
    fn: Callable[Concatenate[SQLiteArchive, P], R],
) -> Callable[Concatenate[SQLiteArchive, P], Coroutine[Any, Any, R]]:
    """Run a synchronous archive method on a worker thread under the connection lock."""

    @functools.wraps(fn)
    async def wrapper(self: SQLiteArchive, *args: P.args, **kwargs: P.kwargs) -> R:
        return await asyncio.to_thread(lambda: self._locked(fn, *args, **kwargs))

    return wrapper  # type: ignore[return-value]


class SQLiteArchive:
    def __init__(self, path: Path | str) -> None:
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.execute("PRAGMA busy_timeout=5000")
        self.schema_version = migrate(self._conn)

    def _locked(self, fn: Callable[..., R], *args: Any, **kwargs: Any) -> R:
        with self._lock:
            return fn(self, *args, **kwargs)

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def _all(self, sql: str, params: Sequence[Any] = ()) -> list[sqlite3.Row | tuple[Any, ...]]:
        return list(self._conn.execute(sql, params).fetchall())

    @threaded
    def create_session(self, session: Session) -> None:
        with self._conn:
            self._conn.execute(
                "INSERT INTO sessions (id, topic, domain, language, seed, created_at, meta)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    session.id,
                    session.topic,
                    session.domain,
                    session.language,
                    session.seed,
                    session.created_at,
                    json.dumps(session.meta),
                ),
            )

    @staticmethod
    def _session(row: Sequence[Any]) -> Session:
        return Session(
            id=row[0],
            topic=row[1],
            domain=row[2],
            language=row[3],
            seed=row[4],
            created_at=row[5],
            meta=json.loads(row[6]),
        )

    @threaded
    def get_session(self, session_id: str) -> Session | None:
        rows = self._all(
            "SELECT id, topic, domain, language, seed, created_at, meta FROM sessions WHERE id = ?",
            (session_id,),
        )
        return self._session(rows[0]) if rows else None

    @threaded
    def list_sessions(self) -> list[Session]:
        rows = self._all(
            "SELECT id, topic, domain, language, seed, created_at, meta FROM sessions"
            " ORDER BY created_at DESC, rowid DESC"
        )
        return [self._session(row) for row in rows]

    @threaded
    def delete_session(self, session_id: str) -> bool:
        with self._conn:
            cursor = self._conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        return cursor.rowcount > 0

    @threaded
    def counts(self, session_id: str) -> dict[str, int]:
        return {
            table: int(
                self._conn.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE session_id = ?", (session_id,)
                ).fetchone()[0]
            )
            for table in TABLES
        }

    @threaded
    def bump_counter(self, session_id: str, name: str) -> int:
        with self._conn:
            row = self._conn.execute(
                "SELECT meta FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
            meta = json.loads(row[0])
            meta[name] = int(meta.get(name, 0)) + 1
            self._conn.execute(
                "UPDATE sessions SET meta = ? WHERE id = ?", (json.dumps(meta), session_id)
            )
        return int(meta[name])

    @threaded
    def save_frame(self, frame: Frame) -> None:
        with self._conn:
            self._conn.execute(
                "INSERT INTO frames (id, session_id, parent_id, operator, json, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (
                    frame.frame_id,
                    frame.session_id,
                    frame.parent_id,
                    frame.operator,
                    frame.model_dump_json(),
                    frame.created_at or _now(),
                ),
            )

    @threaded
    def get_frame(self, frame_id: str) -> Frame | None:
        rows = self._all("SELECT json FROM frames WHERE id = ?", (frame_id,))
        return Frame.model_validate_json(rows[0][0]) if rows else None

    @threaded
    def list_frames(self, session_id: str) -> list[Frame]:
        rows = self._all(
            "SELECT json FROM frames WHERE session_id = ? ORDER BY rowid", (session_id,)
        )
        return [Frame.model_validate_json(row[0]) for row in rows]

    @threaded
    def save_ideas(self, ideas: Sequence[Idea]) -> None:
        with self._conn:
            self._conn.executemany(
                "INSERT INTO ideas (id, session_id, kind, json, created_at) VALUES (?, ?, ?, ?, ?)",
                [
                    (i.id, i.session_id, i.kind, i.model_dump_json(), i.created_at or _now())
                    for i in ideas
                ],
            )

    @threaded
    def update_idea(self, idea: Idea) -> None:
        with self._conn:
            self._conn.execute(
                "UPDATE ideas SET kind = ?, json = ? WHERE id = ?",
                (idea.kind, idea.model_dump_json(), idea.id),
            )

    @threaded
    def list_ideas(self, session_id: str, kind: str | None = None) -> list[Idea]:
        if kind is None:
            rows = self._all(
                "SELECT json FROM ideas WHERE session_id = ? ORDER BY rowid", (session_id,)
            )
        else:
            rows = self._all(
                "SELECT json FROM ideas WHERE session_id = ? AND kind = ? ORDER BY rowid",
                (session_id, kind),
            )
        return [Idea.model_validate_json(row[0]) for row in rows]

    @threaded
    def save_fragments(self, fragments: Sequence[Fragment]) -> None:
        with self._conn:
            self._conn.executemany(
                "INSERT INTO fragments (id, session_id, source_type, json, created_at)"
                " VALUES (?, ?, ?, ?, ?)",
                [
                    (f.id, f.session_id, f.source_type, f.model_dump_json(), f.created_at or _now())
                    for f in fragments
                ],
            )

    @threaded
    def list_fragments(self, session_id: str) -> list[Fragment]:
        rows = self._all(
            "SELECT json FROM fragments WHERE session_id = ? ORDER BY rowid", (session_id,)
        )
        return [Fragment.model_validate_json(row[0]) for row in rows]

    @threaded
    def save_matchups(self, matchups: Sequence[Matchup]) -> None:
        with self._conn:
            self._conn.executemany(
                "INSERT INTO matchups (id, session_id, json, created_at) VALUES (?, ?, ?, ?)",
                [
                    (m.id, m.session_id, m.model_dump_json(), m.created_at or _now())
                    for m in matchups
                ],
            )

    @threaded
    def list_matchups(self, session_id: str) -> list[Matchup]:
        rows = self._all(
            "SELECT json FROM matchups WHERE session_id = ? ORDER BY rowid", (session_id,)
        )
        return [Matchup.model_validate_json(row[0]) for row in rows]

    @threaded
    def save_verdicts(self, session_id: str, verdicts: Sequence[Verdict]) -> None:
        with self._conn:
            self._conn.executemany(
                "INSERT INTO verdicts (session_id, matchup_id, ord, judge, json, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                [
                    (
                        session_id,
                        v.matchup_id,
                        v.order,
                        v.judge_model or "unknown",
                        v.model_dump_json(),
                        _now(),
                    )
                    for v in verdicts
                ],
            )

    @threaded
    def list_verdicts(self, session_id: str) -> list[Verdict]:
        rows = self._all(
            "SELECT json FROM verdicts WHERE session_id = ? ORDER BY id", (session_id,)
        )
        return [Verdict.model_validate_json(row[0]) for row in rows]

    @threaded
    def get_niches(self, session_id: str) -> dict[str, dict[str, Any]]:
        rows = self._all(
            "SELECT niche, json FROM niches WHERE session_id = ? ORDER BY niche", (session_id,)
        )
        return {row[0]: json.loads(row[1]) for row in rows}

    @threaded
    def put_niche(self, session_id: str, niche: str, state: dict[str, Any]) -> None:
        with self._conn:
            self._conn.execute(
                "INSERT INTO niches (session_id, niche, json, updated_at) VALUES (?, ?, ?, ?)"
                " ON CONFLICT(session_id, niche) DO UPDATE SET"
                " json = excluded.json, updated_at = excluded.updated_at",
                (session_id, niche, json.dumps(state), _now()),
            )

    @threaded
    def save_question(self, session_id: str, record: dict[str, Any]) -> None:
        with self._conn:
            self._conn.execute(
                "INSERT INTO questions (session_id, passed, json, created_at) VALUES (?, ?, ?, ?)",
                (session_id, int(bool(record.get("passed"))), json.dumps(record), _now()),
            )

    @threaded
    def list_questions(self, session_id: str) -> list[dict[str, Any]]:
        rows = self._all(
            "SELECT json FROM questions WHERE session_id = ? ORDER BY id", (session_id,)
        )
        return [json.loads(row[0]) for row in rows]

    @threaded
    def save_feedback(self, session_id: str, record: dict[str, Any]) -> None:
        with self._conn:
            self._conn.execute(
                "INSERT INTO feedback (session_id, idea_id, decision, json, created_at)"
                " VALUES (?, ?, ?, ?, ?)",
                (session_id, record["idea_id"], record["decision"], json.dumps(record), _now()),
            )

    @threaded
    def list_feedback(self, session_id: str) -> list[dict[str, Any]]:
        rows = self._all(
            "SELECT json FROM feedback WHERE session_id = ? ORDER BY id", (session_id,)
        )
        return [json.loads(row[0]) for row in rows]

    @threaded
    def delete_feedback(self, session_id: str) -> int:
        with self._conn:
            cursor = self._conn.execute("DELETE FROM feedback WHERE session_id = ?", (session_id,))
        return int(cursor.rowcount)

    @threaded
    def export_session(self, session_id: str) -> dict[str, Any]:
        session = self._session(
            self._conn.execute(
                "SELECT id, topic, domain, language, seed, created_at, meta FROM sessions"
                " WHERE id = ?",
                (session_id,),
            ).fetchone()
        )

        def rows(table: str, order: str = "rowid") -> list[Any]:
            sql = f"SELECT json FROM {table} WHERE session_id = ? ORDER BY {order}"
            return [json.loads(row[0]) for row in self._conn.execute(sql, (session_id,))]

        niches = {
            row[0]: json.loads(row[1])
            for row in self._conn.execute(
                "SELECT niche, json FROM niches WHERE session_id = ? ORDER BY niche", (session_id,)
            )
        }
        return {
            "session": session.model_dump(mode="json"),
            "frames": rows("frames"),
            "ideas": rows("ideas"),
            "fragments": rows("fragments"),
            "matchups": rows("matchups"),
            "verdicts": rows("verdicts", "id"),
            "niches": niches,
            "questions": rows("questions", "id"),
            "feedback": rows("feedback", "id"),
        }
