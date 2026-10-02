"""evals.copilot_cli：以實際錄製的事件固定檔驗證 JSONL 解析與 OTel 用量加總。"""

from __future__ import annotations

import json

import pytest
from test_evals_support import read_fixture

from evals.copilot_cli import is_cgu_call, parse_events, parse_otel_usage


def test_baseline_fixture() -> None:
    run = parse_events(read_fixture("copilot_events_baseline.jsonl"))
    assert run.answer == "好"
    assert run.exit_code == 0
    assert run.tool_calls == []
    assert run.cgu_calls == []
    assert run.cgu_connected is False
    assert run.premium_requests == 1
    assert run.api_duration_ms == 1601
    assert run.mcp_servers["github-mcp-server"]["status"] == "disabled"
    assert run.model_turns == 1
    assert run.bad_lines == 0


def test_plugin_mcp_fixture_counts_only_the_cgu_server() -> None:
    run = parse_events(read_fixture("copilot_events_plugin_mcp.jsonl"))
    assert run.cgu_connected is True
    assert run.mcp_servers["cgu"]["status"] == "connected"
    assert run.mcp_servers["cgu"]["source"] == "plugin"
    assert len(run.tool_calls) == 2
    assert len(run.cgu_calls) == 1
    assert run.cgu_tool_counts == {"list_methods": 1}
    assert all(c["success"] for c in run.tool_calls)
    assert "16" in run.answer
    assert "cgu-list_methods" in run.cgu_tools_available
    assert not any(t.startswith("cguadd") for t in run.cgu_tools_available)
    assert run.model_turns == 2
    assert run.premium_requests == 15


def test_skill_only_fixture_records_skill_without_mcp() -> None:
    run = parse_events(read_fixture("copilot_events_skill_only.jsonl"))
    assert run.skills_invoked == ["creative-ideation"]
    assert [c["name"] for c in run.tool_calls] == ["skill"]
    assert run.cgu_calls == []
    assert run.cgu_connected is False
    assert run.answer and "cgu" in run.answer


def test_final_answer_is_last_message_without_tool_requests() -> None:
    events = [
        {
            "type": "assistant.message",
            "data": {"content": "我先查一下", "toolRequests": [{"x": 1}]},
        },
        {"type": "assistant.message", "data": {"content": "子代理的話", "parentToolCallId": "p"}},
        {"type": "assistant.message", "data": {"content": "最終答案", "toolRequests": []}},
    ]
    run = parse_events("\n".join(json.dumps(e) for e in events))
    assert run.answer == "最終答案"


def test_answer_falls_back_to_deltas_and_tolerates_garbage() -> None:
    lines = [
        "not json",
        json.dumps(
            {"type": "assistant.message_delta", "data": {"messageId": "m", "deltaContent": "你"}}
        ),
        json.dumps(
            {"type": "assistant.message_delta", "data": {"messageId": "m", "deltaContent": "好"}}
        ),
        "[1, 2]",
        "",
    ]
    run = parse_events("\n".join(lines))
    assert run.answer == "你好"
    assert run.bad_lines == 2


def test_empty_stream_gives_empty_run() -> None:
    run = parse_events("")
    assert run.answer == ""
    assert run.exit_code is None
    assert run.cgu_connected is False


@pytest.mark.parametrize(
    ("call", "expected"),
    [
        ({"name": "cgu-spark", "mcp_server": "cgu"}, True),
        ({"name": "whatever", "mcp_server": "CGU"}, True),
        ({"name": "cguadd-x", "mcp_server": "cguadd"}, False),
        ({"name": "cgu_ideate"}, True),
        ({"name": "cgu-ideate"}, True),
        ({"name": "powershell"}, False),
        ({"name": "skill"}, False),
    ],
)
def test_is_cgu_call(call: dict, expected: bool) -> None:
    assert is_cgu_call(call) is expected


def test_otel_usage_sums_only_chat_spans() -> None:
    usage = parse_otel_usage(read_fixture("otel_spans.jsonl"))
    assert usage is not None
    assert usage.chat_calls == 2
    assert usage.input_tokens > 30000
    assert usage.output_tokens > 0
    assert usage.cost == pytest.approx(30.0)
    assert usage.as_dict()["chat_calls"] == 2


def test_otel_usage_missing_or_invalid() -> None:
    assert parse_otel_usage(None) is None
    assert parse_otel_usage("") is None
    assert parse_otel_usage("garbage\n{}") is None
