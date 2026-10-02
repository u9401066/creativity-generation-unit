"""Adapters and CLI: settings, embeddings, local LLM, retrieval, `cgu doctor`."""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import httpx
import numpy as np
import pytest
from cgu_support import CountingTransport

import cgu.infrastructure.embedding as embedding_module
from cgu.application.ports import (
    EmbeddingUnavailableError,
    LLMUnavailableError,
    RetrievalUnavailableError,
)
from cgu.infrastructure.config import Settings
from cgu.infrastructure.embedding import (
    NGRAM_DIM,
    AutoEmbedding,
    NgramHashEmbedding,
    OllamaEmbedding,
)
from cgu.infrastructure.llm import OllamaLLM
from cgu.infrastructure.retrieval import USER_AGENT, WikipediaRetrieval
from cgu.interfaces import cli

URL = "http://ollama.test"


def json_response(payload: Any, status: int = 200) -> httpx.Response:
    return httpx.Response(status, json=payload)


def embed_ok(request: httpx.Request) -> httpx.Response:
    texts = json.loads(request.content)["input"]
    return json_response({"embeddings": [[3.0, 4.0, 0.0] for _ in texts]})


# --- settings -------------------------------------------------------------------------------


def test_settings_defaults() -> None:
    settings = Settings.from_env({})
    assert settings.provider == "passthrough"
    assert settings.embedding == "auto"
    assert settings.network is True
    assert settings.ollama_url == "http://localhost:11434"
    assert settings.data_dir == Path.home() / ".cgu"
    assert settings.db_path == Path.home() / ".cgu" / "cgu.sqlite3"


def test_settings_read_every_variable() -> None:
    settings = Settings.from_env(
        {
            "CGU_PROVIDER": " OLLAMA ",
            "CGU_EMBEDDING": "ngram",
            "CGU_NETWORK": "off",
            "CGU_DATA_DIR": "/data/cgu",
            "CGU_OLLAMA_URL": "http://box:1234/",
            "CGU_OLLAMA_MODEL": "llama3",
            "CGU_EMBED_MODEL": "bge-m3",
            "CGU_LOG_LEVEL": "debug",
        }
    )
    assert settings.provider == "ollama" and settings.embedding == "ngram"
    assert settings.network is False
    assert settings.data_dir == Path("/data/cgu")
    assert settings.ollama_url == "http://box:1234"
    assert settings.ollama_model == "llama3" and settings.embed_model == "bge-m3"
    assert settings.log_level == "DEBUG"


def test_data_dir_prefers_cgu_over_plugin_data() -> None:
    assert Settings.from_env({"PLUGIN_DATA": "/plugin"}).data_dir == Path("/plugin")
    both = {"PLUGIN_DATA": "/plugin", "CGU_DATA_DIR": "/mine"}
    assert Settings.from_env(both).data_dir == Path("/mine")
    assert Settings.from_env({"PLUGIN_DATA": "/plugin", "CGU_DATA_DIR": ""}).data_dir == Path(
        "/plugin"
    )


@pytest.mark.parametrize("raw", ["http://h:11434/v1", "http://h:11434/v1/", "http://h:11434/"])
def test_ollama_url_is_normalised_to_the_native_api_root(raw: str) -> None:
    assert Settings.from_env({"CGU_OLLAMA_URL": raw}).ollama_url == "http://h:11434"


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("CGU_PROVIDER", "openai"),
        ("CGU_EMBEDDING", "openai"),
        ("CGU_NETWORK", "maybe"),
    ],
)
def test_invalid_settings_are_rejected_with_the_variable_name(name: str, value: str) -> None:
    with pytest.raises(ValueError, match=name):
        Settings.from_env({name: value})


# --- n-gram embedding -----------------------------------------------------------------------


async def test_ngram_embedding_is_deterministic_unit_length_and_flagged_non_semantic() -> None:
    backend = NgramHashEmbedding()
    first = await backend.embed(["perioperative delirium", "預防術後譫妄"])
    second = await backend.embed(["perioperative delirium", "預防術後譫妄"])
    assert first.vectors == second.vectors
    assert first.semantic is False and first.backend == "ngram-hash"
    for row in first.vectors:
        assert len(row) == NGRAM_DIM
        assert np.linalg.norm(row) == pytest.approx(1.0)
    info = await backend.describe()
    assert info.semantic is False


async def test_ngram_embedding_orders_lexical_overlap_and_handles_edge_inputs() -> None:
    backend = NgramHashEmbedding()
    out = await backend.embed(
        [
            "early mobilisation after surgery",
            "early mobilization after surgery",
            "quarterly tax form",
        ]
    )
    a, b, c = (np.asarray(v) for v in out.vectors)
    assert float(a @ b) > float(a @ c)
    assert (await backend.embed([])).vectors == []
    blank = await backend.embed(["", "!!!", "x"])
    assert len(blank.vectors) == 3
    assert all(np.isfinite(row).all() for row in blank.vectors)


# --- Ollama embedding -----------------------------------------------------------------------


async def test_ollama_embedding_normalises_and_posts_the_documented_payload() -> None:
    transport = CountingTransport(embed_ok)
    backend = OllamaEmbedding(URL, "nomic-embed-text", client=transport.client)
    out = await backend.embed(["a", "b"])
    assert out.semantic is True and out.backend == "ollama:nomic-embed-text"
    assert out.vectors[0] == pytest.approx([0.6, 0.8, 0.0])
    request = transport.requests[0]
    assert str(request.url) == f"{URL}/api/embed"
    assert json.loads(request.content) == {"model": "nomic-embed-text", "input": ["a", "b"]}


async def test_ollama_embedding_of_nothing_makes_no_request() -> None:
    transport = CountingTransport(embed_ok)
    out = await OllamaEmbedding(URL, "m", client=transport.client).embed([])
    assert out.vectors == [] and transport.requests == []


async def test_ollama_describe_pings_the_server() -> None:
    transport = CountingTransport(embed_ok)
    info = await OllamaEmbedding(URL, "m", client=transport.client).describe()
    assert info.semantic is True and info.backend == "ollama:m"
    assert json.loads(transport.requests[0].content)["input"] == ["ping"]


@pytest.mark.parametrize(
    "responder",
    [
        lambda request: httpx.Response(500, text="boom"),
        lambda request: json_response({"error": "model not found"}),
        lambda request: json_response({"embeddings": [[1.0, 0.0]]}),
        lambda request: json_response({"embeddings": [1.0, 2.0]}),
        lambda request: httpx.Response(200, text="not json"),
    ],
    ids=["http-500", "no-embeddings-key", "wrong-count", "wrong-shape", "not-json"],
)
async def test_ollama_embedding_failures_become_embedding_unavailable(responder: Any) -> None:
    client = CountingTransport(responder).client
    with pytest.raises(EmbeddingUnavailableError):
        await OllamaEmbedding(URL, "m", client=client).embed(["a", "b"])


async def test_ollama_embedding_connection_error_becomes_embedding_unavailable() -> None:
    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    client = CountingTransport(refuse).client
    with pytest.raises(EmbeddingUnavailableError, match="refused"):
        await OllamaEmbedding(URL, "m", client=client).embed(["a"])


# --- auto embedding -------------------------------------------------------------------------


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


async def test_auto_embedding_falls_back_loudly_and_retries_after_the_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = Clock()
    monkeypatch.setattr(embedding_module.time, "monotonic", clock)
    up = False

    def responder(request: httpx.Request) -> httpx.Response:
        return embed_ok(request) if up else httpx.Response(503)

    transport = CountingTransport(responder)
    auto = AutoEmbedding(
        OllamaEmbedding(URL, "m", client=transport.client),
        NgramHashEmbedding(),
        retry_after=60.0,
    )

    first = await auto.embed(["x"])
    assert first.semantic is False and first.backend == "ngram-hash"
    assert any("ollama embedding unavailable" in w for w in first.warnings)
    assert len(transport.requests) == 1

    clock.now += 30
    again = await auto.embed(["x"])
    assert again.semantic is False and len(transport.requests) == 1
    assert (await auto.describe()).semantic is False and len(transport.requests) == 1

    up = True
    clock.now += 31
    recovered = await auto.embed(["x"])
    assert recovered.semantic is True and recovered.warnings == []
    assert recovered.backend == "ollama:m"
    assert (await auto.describe()).semantic is True


# --- Ollama LLM -----------------------------------------------------------------------------


async def test_ollama_llm_posts_a_non_streaming_json_request_with_the_seed() -> None:
    transport = CountingTransport(lambda request: json_response({"response": '{"ideas": ["a"]}'}))
    llm = OllamaLLM(URL, "qwen2.5:3b", client=transport.client)
    reply = await llm.complete("make ideas", seed=7)
    assert reply == '{"ideas": ["a"]}'
    body = json.loads(transport.requests[0].content)
    assert str(transport.requests[0].url) == f"{URL}/api/generate"
    assert body["model"] == "qwen2.5:3b" and body["stream"] is False
    assert body["format"] == "json" and body["prompt"] == "make ideas"
    assert body["options"]["seed"] == 7
    await llm.complete("again")
    assert "seed" not in json.loads(transport.requests[1].content)["options"]


@pytest.mark.parametrize(
    "responder",
    [
        lambda request: httpx.Response(500),
        lambda request: json_response({"done": True}),
        lambda request: httpx.Response(200, text="<html>"),
    ],
    ids=["http-500", "no-response-key", "not-json"],
)
async def test_ollama_llm_failures_become_llm_unavailable(responder: Any) -> None:
    llm = OllamaLLM(URL, "m", client=CountingTransport(responder).client)
    with pytest.raises(LLMUnavailableError):
        await llm.complete("x")


# --- Wikipedia retrieval --------------------------------------------------------------------

PAGES = {
    "query": {
        "pages": [
            {"pageid": 22, "index": 2, "title": "Second", "extract": "two", "fullurl": "http://s"},
            {"pageid": 11, "index": 1, "title": "First", "extract": None},
            {"pageid": 33, "index": 3, "title": "Third", "extract": "three"},
        ]
    }
}


async def test_wikipedia_results_are_ordered_limited_and_attributed() -> None:
    transport = CountingTransport(lambda request: json_response(PAGES))
    docs = await WikipediaRetrieval(client=transport.client).search("topic", lang="zh", limit=2)
    assert [d.title for d in docs] == ["First", "Second"]
    assert docs[0].text == "" and docs[0].url is None
    assert docs[1].url == "http://s" and docs[1].source_id == "wikipedia:zh:22"
    request = transport.requests[0]
    assert request.url.host == "zh.wikipedia.org"
    assert request.url.params["gsrsearch"] == "topic" and request.url.params["gsrlimit"] == "2"
    assert request.headers["user-agent"] == USER_AGENT


async def test_wikipedia_without_results_returns_an_empty_list() -> None:
    transport = CountingTransport(lambda request: json_response({"batchcomplete": True}))
    assert await WikipediaRetrieval(client=transport.client).search("q", lang="en", limit=3) == []


@pytest.mark.parametrize("lang", ["", "EN", "en.evil.com/x", "e", "english!"])
async def test_wikipedia_rejects_language_codes_that_could_redirect_the_request(lang: str) -> None:
    transport = CountingTransport(lambda request: json_response(PAGES))
    with pytest.raises(RetrievalUnavailableError, match="language"):
        await WikipediaRetrieval(client=transport.client).search("q", lang=lang, limit=3)
    assert transport.requests == []


@pytest.mark.parametrize(
    "responder",
    [lambda request: httpx.Response(503), lambda request: httpx.Response(200, text="oops")],
    ids=["http-503", "not-json"],
)
async def test_wikipedia_failures_become_retrieval_unavailable(responder: Any) -> None:
    client = CountingTransport(responder).client
    with pytest.raises(RetrievalUnavailableError):
        await WikipediaRetrieval(client=client).search("q", lang="en", limit=3)


# --- cgu doctor and cgu serve ---------------------------------------------------------------


class FakeOllama(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self._send({"models": [{"name": "nomic-embed-text:latest"}, {"name": "qwen2.5:3b"}]})

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        texts = json.loads(self.rfile.read(length))["input"]
        self._send({"embeddings": [[1.0, 0.5, 0.25] for _ in texts]})

    def _send(self, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        pass


@pytest.fixture
def fake_ollama() -> Iterator[str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), FakeOllama)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def doctor_env(monkeypatch: pytest.MonkeyPatch, data_dir: Path, **extra: str) -> None:
    env = {
        "CGU_DATA_DIR": str(data_dir),
        "CGU_EMBEDDING": "auto",
        "CGU_OLLAMA_URL": "http://127.0.0.1:9",
        **extra,
    }
    for name in ("CGU_PROVIDER", "CGU_NETWORK", "PLUGIN_DATA"):
        monkeypatch.delenv(name, raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)


def test_doctor_json_reports_a_down_ollama_and_the_degraded_embedding(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    doctor_env(monkeypatch, tmp_path / "data")
    assert cli.main(["doctor", "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["provider"] == "passthrough" and report["network"] is True
    assert report["data_dir"] == {"path": str(tmp_path / "data"), "writable": True}
    assert report["ollama"]["reachable"] is False and report["ollama"]["error"]
    assert report["embedding"] == {"mode": "auto", "backend": "ngram-hash", "semantic": False}
    assert not (tmp_path / "data" / ".cgu-write-probe").exists()


def test_doctor_text_output_names_each_fact_and_warns_about_non_semantic_embedding(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    doctor_env(monkeypatch, tmp_path / "data", CGU_EMBEDDING="ngram", CGU_NETWORK="off")
    assert cli.main(["doctor"]) == 0
    out = capsys.readouterr().out
    assert "provider:" in out and "passthrough" in out
    assert "ngram-hash (semantic=false)" in out
    assert "NOT reachable" in out and "network (search): off" in out
    assert str(tmp_path / "data") in out and "writable" in out
    assert "note: semantic=false" in out


def test_doctor_sees_a_running_ollama_and_a_semantic_embedding(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    fake_ollama: str,
) -> None:
    doctor_env(monkeypatch, tmp_path / "data", CGU_OLLAMA_URL=fake_ollama)
    assert cli.main(["doctor", "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["ollama"]["reachable"] is True
    assert report["ollama"]["models"] == ["nomic-embed-text:latest", "qwen2.5:3b"]
    assert report["embedding"] == {
        "mode": "auto",
        "backend": "ollama:nomic-embed-text",
        "semantic": True,
    }


def test_doctor_with_ollama_embedding_forced_reports_unavailable(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    doctor_env(monkeypatch, tmp_path / "data", CGU_EMBEDDING="ollama")
    assert cli.main(["doctor", "--json"]) == 0
    embedding = json.loads(capsys.readouterr().out)["embedding"]
    assert embedding["backend"] == "unavailable" and embedding["semantic"] is False
    assert embedding["error"]


def test_doctor_exits_1_when_the_data_dir_is_not_writable(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    blocker = tmp_path / "a-file"
    blocker.write_text("not a directory", encoding="utf-8")
    doctor_env(monkeypatch, blocker / "data", CGU_EMBEDDING="ngram")
    assert cli.main(["doctor", "--json"]) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["data_dir"]["writable"] is False and report["data_dir"]["error"]


def test_cli_without_a_command_prints_help_and_exits_2(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert cli.main([]) == 2
    assert "doctor" in capsys.readouterr().out


def test_cli_reports_invalid_environment_on_stderr_and_exits_2(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("CGU_PROVIDER", "openai")
    assert cli.main(["doctor"]) == 2
    captured = capsys.readouterr()
    assert "CGU_PROVIDER" in captured.err and captured.out == ""


def test_cli_serve_starts_the_stdio_server(monkeypatch: pytest.MonkeyPatch) -> None:
    started: list[bool] = []
    monkeypatch.setattr(cli, "serve_main", lambda: started.append(True))
    monkeypatch.delenv("CGU_PROVIDER", raising=False)
    assert cli.main(["serve"]) == 0
    assert started == [True]
