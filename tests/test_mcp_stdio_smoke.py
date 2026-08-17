"""Subprocess stdio smoke for the packaged CGU MCP entrypoint."""

from __future__ import annotations

import os
import sys

import pytest
from mcp import Client
from mcp.client.stdio import StdioServerParameters, stdio_client


@pytest.mark.asyncio
async def test_stdio_server_lists_and_calls_sdk2_tools() -> None:
    env = os.environ.copy()
    env["CGU_LLM_PROVIDER"] = "passthrough"
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "cgu.server"],
        env=env,
    )

    async with Client(stdio_client(params), mode="auto") as client:
        tools = await client.list_tools()
        result = await client.call_tool("list_methods", {})

        assert client.session.protocol_version == "2026-07-28"
    assert len(tools.tools) == 24
    assert result.is_error is False
    assert result.structured_content is not None
    assert result.structured_content["total_methods"] >= 15
