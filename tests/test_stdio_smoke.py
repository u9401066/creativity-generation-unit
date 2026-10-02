"""The real server over real stdio: a subprocess, JSON-RPC on stdout, logs only on stderr."""

from __future__ import annotations

import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
import tomllib
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import pytest
from mcp import Client
from mcp.client.stdio import StdioServerParameters, stdio_client

ROOT = Path(__file__).resolve().parent.parent
TOOLS = {
    "cgu_status",
    "cgu_session",
    "cgu_frame",
    "cgu_material",
    "cgu_diverge",
    "cgu_ideas",
    "cgu_judge",
    "cgu_evolve",
    "cgu_feedback",
    "cgu_question_gate",
}


def server_env(data_dir: Path) -> dict[str, str]:
    return {
        "CGU_DATA_DIR": str(data_dir),
        "CGU_EMBEDDING": "ngram",
        "CGU_NETWORK": "off",
        "CGU_LOG_LEVEL": "INFO",
        "PYTHONUTF8": "1",
    }


@asynccontextmanager
async def stdio_session(
    command: str, args: list[str], data_dir: Path, stderr_path: Path
) -> AsyncIterator[Client]:
    params = StdioServerParameters(command=command, args=args, env=server_env(data_dir))
    with stderr_path.open("a", encoding="utf-8") as errlog:
        async with Client(stdio_client(params, errlog=errlog), mode="auto") as client:
            yield client


async def call(client: Client, tool: str, **arguments: Any) -> dict[str, Any]:
    result = await client.call_tool(tool, arguments)
    assert not result.is_error, result.content
    assert result.structured_content is not None
    out: dict[str, Any] = result.structured_content
    return out


async def test_module_entry_point_speaks_mcp_over_stdio(tmp_path: Path) -> None:
    stderr_path = tmp_path / "stderr.log"
    async with stdio_session(
        sys.executable, ["-m", "cgu.interfaces.mcp.server"], tmp_path / "data", stderr_path
    ) as client:
        assert client.protocol_version == "2026-07-28"
        assert client.server_info is not None and client.server_info.version == "0.8.0"
        assert client.instructions is None or "cgu_session" in client.instructions
        listed = await client.list_tools()
        assert {tool.name for tool in listed.tools} == TOOLS
        status = await call(client, "cgu_status")
        assert status["ok"] is True
        assert status["data"]["provider"] == "passthrough"
        assert status["data"]["embedding"] == {"backend": "ngram-hash", "semantic": False}
        opened = await call(client, "cgu_session", action="open", topic="stdio smoke")
        assert opened["ok"] is True
        sid = opened["data"]["session_id"]
        frame = await call(client, "cgu_diverge", action="typical_set", session_id=sid, k=3)
        assert frame["ok"] is True and frame["work_order"]["kind"] == "typical_set"
    log = stderr_path.read_text(encoding="utf-8")
    assert "ready" in log and "provider=passthrough" in log


async def test_legacy_handshake_also_works_over_stdio(tmp_path: Path) -> None:
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "cgu.interfaces.mcp.server"],
        env=server_env(tmp_path / "data"),
    )
    with (tmp_path / "stderr.log").open("a", encoding="utf-8") as errlog:
        async with Client(stdio_client(params, errlog=errlog), mode="legacy") as client:
            listed = await client.list_tools()
            assert {tool.name for tool in listed.tools} == TOOLS
            assert client.instructions and "cgu_session" in client.instructions
            status = await call(client, "cgu_status")
            assert status["ok"] is True


async def test_sessions_persist_across_server_processes(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    args = ["-m", "cgu.interfaces.mcp.server"]
    async with stdio_session(sys.executable, args, data_dir, tmp_path / "e1.log") as first:
        opened = await call(first, "cgu_session", action="open", topic="remember me")
        sid = opened["data"]["session_id"]
        await call(
            first,
            "cgu_ideas",
            action="add",
            session_id=sid,
            ideas=[{"text": "persisted idea", "kind": "human"}],
        )
    async with stdio_session(sys.executable, args, data_dir, tmp_path / "e2.log") as second:
        listed = await call(second, "cgu_session", action="list")
        ideas = await call(second, "cgu_ideas", action="list", session_id=sid)
    assert [s["id"] for s in listed["data"]["sessions"]] == [sid]
    assert [i["text"] for i in ideas["data"]["ideas"]] == ["persisted idea"]
    assert (data_dir / "cgu.sqlite3").exists()


def test_pyproject_declares_the_console_scripts() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["version"] == "0.8.0"
    assert pyproject["project"]["scripts"] == {
        "cgu-server": "cgu.interfaces.mcp.server:main",
        "cgu": "cgu.interfaces.cli:main",
    }


async def test_console_script_starts_the_same_server(tmp_path: Path) -> None:
    entry_points = importlib.metadata.entry_points(group="console_scripts", name="cgu-server")
    if [ep.value for ep in entry_points] != ["cgu.interfaces.mcp.server:main"]:
        pytest.skip("the installed cgu metadata is missing or stale; run uv sync --locked")
    bin_dir = Path(sys.executable).parent
    script = shutil.which("cgu-server", path=str(bin_dir))
    if script is None:
        pytest.skip("cgu-server console script is not installed next to this interpreter")
    async with stdio_session(script, [], tmp_path / "data", tmp_path / "stderr.log") as client:
        listed = await client.list_tools()
        assert {tool.name for tool in listed.tools} == TOOLS


async def test_stdout_carries_nothing_but_json_rpc(tmp_path: Path) -> None:
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "raw", "version": "0"},
        },
    }
    completed = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "cgu.interfaces.mcp.server"],
        input=json.dumps(request) + "\n",
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
        env={**os.environ, **server_env(tmp_path / "data")},
        check=False,
    )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    assert lines, completed.stderr
    for line in lines:
        message = json.loads(line)
        assert message["jsonrpc"] == "2.0"
    assert "cgu" in completed.stderr


async def test_invalid_environment_exits_2_with_a_readable_error_and_clean_stdout(
    tmp_path: Path,
) -> None:
    completed = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "cgu.interfaces.mcp.server"],
        input="",
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
        env={**os.environ, **server_env(tmp_path / "data"), "CGU_PROVIDER": "openai"},
        check=False,
    )
    assert completed.returncode == 2
    assert "CGU_PROVIDER" in completed.stderr
    assert completed.stdout == ""
