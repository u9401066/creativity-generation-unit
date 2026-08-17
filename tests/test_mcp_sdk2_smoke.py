"""Protocol-level smoke tests for the official MCP Python SDK 2 runtime."""

from __future__ import annotations

import pytest
from mcp import Client

import cgu.server as cgu_server


@pytest.mark.asyncio
async def test_sdk2_server_lists_and_calls_tools_and_resources(monkeypatch) -> None:
    monkeypatch.setattr(cgu_server, "LLM_PROVIDER", "passthrough")

    async with Client(cgu_server.mcp, mode="2026-07-28") as client:
        assert client.session.protocol_version == "2026-07-28"

        tools = await client.list_tools()
        resources = await client.list_resources()
        tool_names = {tool.name for tool in tools.tools}
        resource_uris = {resource.uri for resource in resources.resources}

        assert len(tool_names) == len(tools.tools)
        assert {
            "generate_ideas",
            "spark_collision",
            "deep_think",
            "brainstorm_protocol",
            "check_novelty",
        } <= tool_names
        assert resource_uris == {
            "cgu://creativity-levels",
            "cgu://thinking-modes",
        }
        assert all("ctx" not in tool.input_schema.get("properties", {}) for tool in tools.tools)

        result = await client.call_tool("list_methods", {})

    assert result.is_error is False
    assert result.structured_content is not None
    assert result.structured_content["total_methods"] >= 15
