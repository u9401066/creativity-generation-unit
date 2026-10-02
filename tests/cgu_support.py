"""Helpers shared by the CGU tests."""

from __future__ import annotations

import ast
import asyncio
from collections.abc import AsyncIterator, Callable, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from mcp import Client

from cgu.application.ports import Embedded, EmbeddingInfo
from cgu.infrastructure.config import Settings
from cgu.interfaces.mcp.server import create_server

SRC = Path(__file__).resolve().parent.parent / "src" / "cgu"
MEASUREMENT_KEYS = {"value", "method", "reference", "calibrated", "n"}


def stray_floats(obj: Any, path: str = "$") -> list[str]:
    """Paths of floats that are not the `value` of a Measurement-shaped dict."""
    found: list[str] = []
    if isinstance(obj, float):
        found.append(path)
    elif isinstance(obj, dict):
        is_measurement = set(obj) == MEASUREMENT_KEYS
        for key, value in obj.items():
            if is_measurement and key == "value":
                assert isinstance(value, float), f"{path}.value must be a float"
                continue
            found.extend(stray_floats(value, f"{path}.{key}"))
    elif isinstance(obj, list | tuple):
        for index, value in enumerate(obj):
            found.extend(stray_floats(value, f"{path}[{index}]"))
    return found


def measurements(obj: Any) -> list[dict[str, Any]]:
    """Every Measurement-shaped dict inside obj."""
    found: list[dict[str, Any]] = []
    if isinstance(obj, dict):
        if set(obj) == MEASUREMENT_KEYS:
            found.append(obj)
        for value in obj.values():
            found.extend(measurements(value))
    elif isinstance(obj, list | tuple):
        for value in obj:
            found.extend(measurements(value))
    return found


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module)
    return names


@dataclass
class Harness:
    client: Client
    settings: Settings

    async def call(self, tool: str, **arguments: Any) -> dict[str, Any]:
        result = await self.client.call_tool(tool, arguments)
        assert not result.is_error, result.content
        assert result.structured_content is not None
        data: dict[str, Any] = result.structured_content
        return data

    async def ok(self, tool: str, **arguments: Any) -> dict[str, Any]:
        out = await self.call(tool, **arguments)
        assert out["ok"], out["error"]
        return out

    async def session(self, topic: str = "periop delirium", **extra: Any) -> str:
        out = await self.ok("cgu_session", action="open", topic=topic, **extra)
        return str(out["data"]["session_id"])


def make_open_cgu(tmp_path: Path) -> Callable[..., Any]:
    @asynccontextmanager
    async def open_cgu(
        *,
        provider: str = "passthrough",
        embedding_mode: str = "ngram",
        network: bool = True,
        mode: str = "2026-07-28",
        client_kwargs: dict[str, Any] | None = None,
        **server_kwargs: Any,
    ) -> AsyncIterator[Harness]:
        settings = Settings(
            data_dir=tmp_path / "data",
            provider=provider,  # type: ignore[arg-type]
            embedding=embedding_mode,  # type: ignore[arg-type]
            network=network,
            log_level="WARNING",
        )
        server = create_server(settings, **server_kwargs)
        async with Client(server, mode=mode, **(client_kwargs or {})) as client:  # type: ignore[arg-type]
            yield Harness(client=client, settings=settings)

    return open_cgu


def mock_client(handler: Callable[[httpx.Request], httpx.Response]) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


class CountingTransport:
    """An httpx client that records every request and answers with a canned response."""

    def __init__(self, responder: Callable[[httpx.Request], httpx.Response] | None = None) -> None:
        self.requests: list[httpx.Request] = []
        self._responder = responder or (lambda request: httpx.Response(404))
        self.client = mock_client(self._handle)

    def _handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return self._responder(request)


class FakeLLM:
    def __init__(self, reply: str = '{"ideas": ["local idea one", "local idea two"]}') -> None:
        self.model = "fake-local"
        self.reply = reply
        self.calls: list[str] = []

    async def complete(self, prompt: str, *, seed: int | None = None) -> str:
        self.calls.append(prompt)
        return self.reply


AXES = ("drug", "nurse", "device", "paper", "money")


class KeywordSemanticEmbedding:
    """A deterministic 'semantic' backend: texts are points on keyword axes."""

    def __init__(self, semantic: bool = True) -> None:
        self.semantic = semantic
        self.calls = 0

    async def describe(self) -> EmbeddingInfo:
        return EmbeddingInfo(backend="fake-keywords", semantic=self.semantic)

    async def embed(self, texts: Sequence[str]) -> Embedded:
        self.calls += 1
        vectors: list[list[float]] = []
        for text in texts:
            lowered = text.lower()
            row = [float(lowered.count(axis)) for axis in AXES]
            row.append(0.05)
            norm = sum(x * x for x in row) ** 0.5
            vectors.append([x / norm for x in row])
        return Embedded(vectors=vectors, backend="fake-keywords", semantic=self.semantic)


class SlowEmbedding:
    """Blocks the calling thread like a badly written adapter would, inside the port."""

    def __init__(self, seconds: float) -> None:
        self.seconds = seconds

    async def describe(self) -> EmbeddingInfo:
        return EmbeddingInfo(backend="slow", semantic=False)

    async def embed(self, texts: Sequence[str]) -> Embedded:
        await asyncio.sleep(self.seconds)
        return Embedded(vectors=[[1.0, 0.0] for _ in texts], backend="slow", semantic=False)
