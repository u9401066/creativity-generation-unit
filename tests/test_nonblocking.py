"""The event loop must stay responsive while adapters (embedding, LLM, retrieval, SQLite) work."""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import httpx
from cgu_support import SlowEmbedding

from cgu.infrastructure.sqlite import SQLiteArchive

MAX_STALL = 0.1
TICK = 0.01


class Heartbeat:
    def __init__(self) -> None:
        self.worst = 0.0
        self.ticks = 0


@asynccontextmanager
async def heartbeat() -> AsyncIterator[Heartbeat]:
    beat = Heartbeat()
    running = True

    async def run() -> None:
        loop = asyncio.get_running_loop()
        while running:
            started = loop.time()
            await asyncio.sleep(TICK)
            beat.worst = max(beat.worst, loop.time() - started - TICK)
            beat.ticks += 1

    task = asyncio.create_task(run())
    await asyncio.sleep(0.05)
    beat.worst = 0.0
    try:
        yield beat
    finally:
        running = False
        await task


class SlowArchive(SQLiteArchive):
    """Every statement blocks its worker thread, as a slow disk would."""

    def _locked(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        time.sleep(0.15)
        return super()._locked(fn, *args, **kwargs)


def slow_client(handler: Callable[[httpx.Request], Any]) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


async def test_the_heartbeat_detects_a_blocked_loop() -> None:
    async with heartbeat() as beat:
        time.sleep(0.25)
        await asyncio.sleep(0.05)
    assert beat.worst > MAX_STALL


async def test_slow_blocking_sqlite_does_not_stall_the_loop(
    open_cgu: Callable[..., Any], tmp_path: Path
) -> None:
    archive = SlowArchive(tmp_path / "slow.sqlite3")
    try:
        async with open_cgu(archive=archive) as h, heartbeat() as beat:
            sid = await h.session()
            await h.ok(
                "cgu_ideas",
                action="add",
                session_id=sid,
                ideas=[{"text": "x", "kind": "human"}],
            )
    finally:
        archive.close()
    assert beat.ticks > 10
    assert beat.worst < MAX_STALL, beat.worst


async def test_slow_embedding_does_not_stall_the_loop(open_cgu: Callable[..., Any]) -> None:
    async with open_cgu(embedding=SlowEmbedding(0.4)) as h:
        sid = await h.session()
        async with heartbeat() as beat:
            await h.ok(
                "cgu_ideas",
                action="add",
                session_id=sid,
                ideas=[{"text": "alpha", "kind": "human"}],
            )
            await h.ok("cgu_ideas", action="measure", session_id=sid)
    assert beat.ticks > 20
    assert beat.worst < MAX_STALL, beat.worst


async def test_ngram_embedding_of_a_large_batch_runs_off_the_loop(
    open_cgu: Callable[..., Any],
) -> None:
    ideas = [
        {"text": f"idea {n} " + "lorem ipsum dolor sit amet " * 70, "kind": "human"}
        for n in range(100)
    ]
    async with open_cgu() as h:
        sid = await h.session()
        async with heartbeat() as beat:
            await h.ok("cgu_ideas", action="add", session_id=sid, ideas=ideas)
            await h.ok("cgu_ideas", action="measure", session_id=sid)
    assert beat.ticks > 5
    assert beat.worst < MAX_STALL, beat.worst


async def test_slow_ollama_embedding_and_llm_do_not_stall_the_loop(
    open_cgu: Callable[..., Any],
) -> None:
    async def respond(request: httpx.Request) -> httpx.Response:
        await asyncio.sleep(0.3)
        if request.url.path == "/api/embed":
            texts = json.loads(request.content)["input"]
            rows = [[1.0, float(i), 0.5] for i, _ in enumerate(texts)]
            return httpx.Response(200, json={"embeddings": rows})
        reply = json.dumps({"ideas": ["a local idea", "another local idea"]})
        return httpx.Response(200, json={"response": reply})

    async with open_cgu(
        provider="ollama", embedding_mode="ollama", http_client=slow_client(respond)
    ) as h:
        sid = await h.session()
        async with heartbeat() as beat:
            out = await h.ok("cgu_diverge", action="typical_set", session_id=sid, k=2)
            await h.ok("cgu_ideas", action="measure", session_id=sid)
    assert out["provenance"]["engine"] == "ollama"
    assert out["data"]["executed"] is True
    assert beat.ticks > 30
    assert beat.worst < MAX_STALL, beat.worst


async def test_slow_retrieval_does_not_stall_the_loop(open_cgu: Callable[..., Any]) -> None:
    async def respond(request: httpx.Request) -> httpx.Response:
        await asyncio.sleep(0.3)
        page = {"pageid": 1, "index": 1, "title": "Delirium", "extract": "A state of confusion."}
        return httpx.Response(200, json={"query": {"pages": [page]}})

    async with open_cgu(http_client=slow_client(respond)) as h:
        sid = await h.session()
        async with heartbeat() as beat:
            out = await h.ok("cgu_material", action="search", session_id=sid, query="delirium")
    assert len(out["data"]["fragments"]) == 1
    assert beat.ticks > 20
    assert beat.worst < MAX_STALL, beat.worst


async def test_concurrent_calls_overlap_instead_of_queueing(open_cgu: Callable[..., Any]) -> None:
    delay = 0.3
    async with open_cgu(embedding=SlowEmbedding(delay)) as h:
        sids = [await h.session(f"topic {n}") for n in range(4)]
        started = time.perf_counter()
        await asyncio.gather(
            *[
                h.ok(
                    "cgu_ideas",
                    action="add",
                    session_id=sid,
                    ideas=[{"text": "x", "kind": "human"}],
                )
                for sid in sids
            ]
        )
        elapsed = time.perf_counter() - started
    assert elapsed < delay * 4 * 0.75, elapsed
