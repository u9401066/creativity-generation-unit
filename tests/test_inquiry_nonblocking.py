"""The event loop must stay responsive while 2000 questions are embedded, clustered and mined."""

from __future__ import annotations

import asyncio
import random
import time
import zlib
from collections.abc import Callable, Sequence
from typing import Any

import numpy as np
import pytest
from test_nonblocking import MAX_STALL, heartbeat

from cgu.application.ports import Embedded, EmbeddingInfo

QUESTION_COUNT = 2000
TOPICS = 25
OWN_DIM = 64


def synthetic_questions(count: int, seed: int = 7) -> list[dict[str, Any]]:
    """Random word salads in topic-specific vocabularies: distinct questions, no near-duplicates."""
    rng = random.Random(seed)
    vocab = [f"w{n:03d}{chr(97 + n % 26)}{chr(97 + n * 7 % 26)}" for n in range(TOPICS * 40)]
    rows: list[dict[str, Any]] = []
    for n in range(count):
        topic = n % TOPICS
        words = rng.sample(vocab[topic * 40 : topic * 40 + 40], 9)
        rows.append(
            {
                "text": " ".join(words),
                "project": f"p{topic % 4}",
                "occurred_at": f"2026-{1 + n % 9:02d}-{1 + n % 27:02d}T{n % 24:02d}:00:00+00:00",
            }
        )
    return rows


class TopicEmbedding:
    """A 'semantic' backend where the first word's topic is the theme and the rest is noise."""

    async def describe(self) -> EmbeddingInfo:
        return EmbeddingInfo(backend="fake-topics", semantic=True)

    async def embed(self, texts: Sequence[str]) -> Embedded:
        return await asyncio.to_thread(self._embed, list(texts))

    @staticmethod
    def _embed(texts: list[str]) -> Embedded:
        rows: list[list[float]] = []
        for text in texts:
            vector = np.zeros(TOPICS + OWN_DIM)
            vector[int(text.split()[0][1:4]) // 40 % TOPICS] = 1.0
            noise = np.random.default_rng(zlib.crc32(text.encode())).normal(size=OWN_DIM)
            vector[TOPICS:] = 0.6 * noise / np.linalg.norm(noise)
            rows.append((vector / np.linalg.norm(vector)).tolist())
        return Embedded(vectors=rows, backend="fake-topics", semantic=True)


@pytest.mark.parametrize("backend", ["ngram", "topics"])
async def test_two_thousand_questions_cluster_and_mine_without_stalling_the_loop(
    open_cgu: Callable[..., Any], backend: str
) -> None:
    rows = synthetic_questions(QUESTION_COUNT)
    kwargs: dict[str, Any] = {"embedding": TopicEmbedding()} if backend == "topics" else {}
    async with open_cgu(**kwargs) as h:
        await h.ok(
            "cgu_inquiry",
            action="settings",
            enable=True,
            consent={"granted": True, "note": "performance test"},
        )
        async with heartbeat() as capture_beat:
            for start in range(0, QUESTION_COUNT, 200):
                await h.ok("cgu_inquiry", action="capture", items=rows[start : start + 200])
        assert capture_beat.ticks > 10
        assert capture_beat.worst < MAX_STALL, f"capture stalled the loop: {capture_beat.worst}"

        started = time.perf_counter()
        async with heartbeat() as beat:
            themes = await h.ok("cgu_inquiry", action="themes")
            tight = await h.ok("cgu_inquiry", action="themes", threshold=0.9, min_size=3)
            mined = await h.ok("cgu_inquiry", action="mine", limit=5)
            related = await h.ok("cgu_inquiry", action="related", query="w001ab w002cd w003ef")
            settings = await h.ok("cgu_inquiry", action="settings")
        elapsed = time.perf_counter() - started
        assert themes["data"]["scope"]["inquiries"] == QUESTION_COUNT
        assert len(themes["data"]["themes"]) >= (TOPICS if backend == "topics" else 1)
        assert len(tight["data"]["themes"]) >= 1
        assert mined["data"]["reference_size"] == QUESTION_COUNT
        if backend == "topics":
            assert mined["data"]["counts_by_kind"]["frame"] == 5
            assert mined["data"]["counts_by_kind"]["bridge"] == 5
        assert related["data"]["reference_size"] == QUESTION_COUNT
        assert settings["data"]["counts"]["inquiries"] == QUESTION_COUNT
        assert beat.ticks > 5, f"the heartbeat barely ran ({beat.ticks} ticks in {elapsed:.2f}s)"
        assert beat.worst < MAX_STALL, f"the loop stalled for {beat.worst:.3f}s"

        async with heartbeat() as delete_beat:
            out = await h.ok("cgu_inquiry", action="delete", all=True, confirm=True)
        assert out["data"]["deleted"] == QUESTION_COUNT
        assert delete_beat.worst < MAX_STALL, delete_beat.worst
