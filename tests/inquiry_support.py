"""Helpers for the inquiry-memory tests: the synthetic tuning corpus, seeding it, and ARI."""

from __future__ import annotations

import json
import zlib
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from cgu_support import Harness

from cgu.application.ports import Embedded, EmbeddingInfo
from cgu.application.services.inquiry import CaptureRequest, InquiryService
from cgu.domain.capture import parse_time
from cgu.domain.common import Session
from cgu.domain.idea import Idea
from cgu.infrastructure.sqlite import SQLiteArchive

CORPUS_PATH = Path(__file__).resolve().parent / "fixtures" / "inquiry_tuning_corpus.json"
CONSENT = {"granted": True, "note": "yes, remember my questions on this machine"}

THEME_AXES = ("drug", "device", "nurse", "paper", "money")
FILLER = [
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
CLUSTER_DIM = len(THEME_AXES) + len(FILLER)


class ClusterEmbedding:
    """A 'semantic' backend with known geometry.

    A text sits on its theme keyword's axis plus a smaller axis of its own: two different
    questions on one theme have cosine ~0.74 (the same theme, not the same family), different
    themes ~0.26. A text with no keyword lies on its own axis alone.
    """

    def __init__(self, semantic: bool = True) -> None:
        self.semantic = semantic
        self.calls = 0

    @staticmethod
    def vector(text: str) -> list[float]:
        lowered = text.lower()
        row = [0.0] * CLUSTER_DIM
        theme = next((i for i, axis in enumerate(THEME_AXES) if axis in lowered), None)
        word = next((w for w in lowered.split() if w in FILLER), None)
        own = FILLER.index(word) if word else zlib.crc32(lowered.encode()) % len(FILLER)
        if theme is None:
            row[len(THEME_AXES) + own] = 1.0
        else:
            row[theme] = 1.0
            row[len(THEME_AXES) + own] = 0.6
        norm = sum(x * x for x in row) ** 0.5
        return [x / norm for x in row]

    async def describe(self) -> EmbeddingInfo:
        return EmbeddingInfo(backend="fake-clusters", semantic=self.semantic)

    async def embed(self, texts: Sequence[str]) -> Embedded:
        self.calls += 1
        return Embedded(
            vectors=[self.vector(t) for t in texts], backend="fake-clusters", semantic=self.semantic
        )


def load_corpus() -> dict[str, Any]:
    corpus: dict[str, Any] = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    return corpus


def corpus_now(corpus: dict[str, Any]) -> datetime:
    return parse_time(corpus["now"])


def adjusted_rand_index(truth: list[Any], predicted: list[Any]) -> float:
    """Adjusted Rand index of two labelings of the same items."""
    n = len(truth)
    t_codes = {label: i for i, label in enumerate(dict.fromkeys(truth))}
    p_codes = {label: i for i, label in enumerate(dict.fromkeys(predicted))}
    table = np.zeros((len(t_codes), len(p_codes)), dtype=np.int64)
    for t, p in zip(truth, predicted, strict=True):
        table[t_codes[t], p_codes[p]] += 1

    def pairs(values: np.ndarray) -> float:
        return float((values * (values - 1) / 2).sum())

    sum_cells = pairs(table.ravel())
    sum_rows = pairs(table.sum(axis=1))
    sum_cols = pairs(table.sum(axis=0))
    total = n * (n - 1) / 2
    expected = sum_rows * sum_cols / total
    maximum = (sum_rows + sum_cols) / 2
    return 1.0 if maximum == expected else (sum_cells - expected) / (maximum - expected)


async def seed_corpus(
    archive: SQLiteArchive, service: InquiryService, corpus: dict[str, Any]
) -> dict[str, str]:
    """Enable recording, then store the corpus; returns {corpus id: stored inquiry id}."""
    from cgu.domain.inquiry import InquiryConsent

    enabled = await service.settings(
        enable=True,
        consent=InquiryConsent(granted=True, note=CONSENT["note"], via="caller"),
        excluded_projects=None,
    )
    assert enabled.ok
    created = "2026-07-01T00:00:00+00:00"
    sessions = sorted({r["session"] for r in corpus["inquiries"] if r["session"]})
    for sid in sessions:
        await archive.create_session(Session(id=sid, topic=sid, seed=1, created_at=created))
    mapping: dict[str, str] = {}
    for row in corpus["inquiries"]:
        result = await service.capture(
            [
                CaptureRequest(
                    text=row["text"],
                    project=row["project"],
                    session_id=row["session"],
                    occurred_at=row["occurred_at"],
                )
            ],
            batch=False,
            embed=True,
        )
        assert result.ok and result.data["recorded"], result.data
        mapping[row["id"]] = result.data["id"]
    for idea in corpus["ideas"]:
        idea_id = idea["id"]
        await archive.save_ideas(
            [
                Idea(
                    id=idea_id,
                    session_id=idea["session"],
                    text=idea["text"],
                    kind="candidate",
                    created_at=created,
                )
            ]
        )
        await archive.save_feedback(
            idea["session"],
            {"idea_id": idea_id, "decision": idea["decision"], "reasons": [], "note": None},
        )
    return mapping


async def seed_via_tool(h: Harness, corpus: dict[str, Any]) -> dict[str, str]:
    """The same corpus through the MCP tool (batch capture), with real sessions."""
    await h.ok("cgu_inquiry", action="settings", enable=True, consent=CONSENT)
    sessions: dict[str, str] = {}
    for row in corpus["inquiries"]:
        if row["session"] and row["session"] not in sessions:
            sessions[row["session"]] = await h.session(row["session"])
    mapping: dict[str, str] = {}
    rows = corpus["inquiries"]
    for start in range(0, len(rows), 50):
        chunk = rows[start : start + 50]
        out = await h.ok(
            "cgu_inquiry",
            action="capture",
            items=[
                {
                    "text": r["text"],
                    "project": r["project"],
                    "session_id": sessions.get(r["session"]) if r["session"] else None,
                    "occurred_at": r["occurred_at"],
                }
                for r in chunk
            ],
        )
        for row, item in zip(chunk, out["data"]["items"], strict=True):
            mapping[row["id"]] = item["id"]
    for idea in corpus["ideas"]:
        sid = sessions[idea["session"]]
        added = await h.ok(
            "cgu_ideas",
            action="add",
            session_id=sid,
            ideas=[{"text": idea["text"], "kind": "candidate"}],
        )
        await h.ok(
            "cgu_feedback",
            action="record",
            session_id=sid,
            idea_id=added["data"]["ideas"][0]["idea_id"],
            decision=idea["decision"],
        )
    return mapping
