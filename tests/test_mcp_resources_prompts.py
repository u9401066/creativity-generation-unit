"""Resources, prompts, and the tool/action names that every piece of text mentions."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from typing import Any

import pytest
from cgu_support import CountingTransport
from mcp import MCPError
from test_mcp_tools_contract import ACTIONS, run_everything, wiki_responder

from cgu.domain.operators import OPERATORS

NAME_RE = re.compile(r"\bcgu_[a-z_]+\b")
CALL_RE = re.compile(r"\b(cgu_[a-z_]+)\(action=\"?([a-z_]+)")


def check_mentions(label: str, text: str) -> None:
    for name in NAME_RE.findall(text):
        assert name in ACTIONS, f"{label} mentions unknown tool {name}"
    for tool, action in CALL_RE.findall(text):
        assert tool in ACTIONS, f"{label}: {tool}"
        assert action in (ACTIONS[tool] or []), f"{label} mentions {tool}(action={action})"


async def test_resources_are_listed_and_readable(open_cgu: Callable[..., Any]) -> None:
    async with open_cgu() as h:
        static = await h.client.list_resources()
        templates = await h.client.list_resource_templates()
        uris = {str(r.uri) for r in static.resources}
        assert uris == {
            "cgu://operators",
            "cgu://rubrics/question-gate",
            "cgu://rubrics/pairwise",
            "cgu://triggers",
            "cgu://methods",
        }
        assert [t.uri_template for t in templates.resource_templates] == ["cgu://methods/{name}"]
        texts: dict[str, str] = {}
        for uri in sorted(uris):
            read = await h.client.read_resource(uri)
            texts[uri] = read.contents[0].text
        scamper = await h.client.read_resource("cgu://methods/scamper")
        triz = await h.client.read_resource("cgu://methods/triz")
        hats = await h.client.read_resource("cgu://methods/six-hats")
        with pytest.raises(MCPError):
            await h.client.read_resource("cgu://methods/telepathy")
    cards = json.loads(texts["cgu://operators"])
    assert [c["name"] for c in cards] == list(OPERATORS)
    assert all(c["instruction_template"] and c["guardrails"] for c in cards)
    assert "decision_relevant" in texts["cgu://rubrics/question-gate"]
    assert (
        "Wilson" not in texts["cgu://rubrics/pairwise"] and "AB" in texts["cgu://rubrics/pairwise"]
    )
    assert set(json.loads(texts["cgu://triggers"])) == {"浮現", "澄清", "生成", "檢驗", "整合"}
    index = json.loads(texts["cgu://methods"])
    assert {m["name"] for m in index} == {
        "scamper",
        "six_hats",
        "triz",
        "5w2h",
        "reverse",
        "morphological",
    }
    assert "Substitute" in scamper.contents[0].text and "TRIZ" in triz.contents[0].text
    assert hats.contents[0].text.startswith("六頂思考帽")
    for uri, text in texts.items():
        check_mentions(uri, text)


async def test_prompts_are_listed_and_render_with_arguments(open_cgu: Callable[..., Any]) -> None:
    async with open_cgu() as h:
        listed = await h.client.list_prompts()
        names = {p.name for p in listed.prompts}
        assert names == {
            "frame_audit",
            "anti_typical_session",
            "maieutic_session",
            "pairwise_judge",
        }
        rendered = {
            "frame_audit": await h.client.get_prompt("frame_audit", {"problem": "reduce delirium"}),
            "anti_typical_session": await h.client.get_prompt(
                "anti_typical_session", {"topic": "quiet wards"}
            ),
            "maieutic_session": await h.client.get_prompt(
                "maieutic_session", {"topic": "screening"}
            ),
            "pairwise_judge": await h.client.get_prompt("pairwise_judge", {"session_id": "s-123"}),
        }
    assert "reduce delirium" in rendered["frame_audit"].messages[0].content.text
    assert "quiet wards" in rendered["anti_typical_session"].messages[0].content.text
    assert "s-123" in rendered["pairwise_judge"].messages[0].content.text
    for name, result in rendered.items():
        text = result.messages[0].content.text
        assert result.messages[0].role == "user"
        assert "護欄" in text
        check_mentions(f"prompt {name}", text)


async def test_every_tool_name_and_action_mentioned_anywhere_exists(
    open_cgu: Callable[..., Any],
) -> None:
    transport = CountingTransport(wiki_responder)
    async with open_cgu(http_client=transport.client, mode="auto") as h:
        results, _ = await run_everything(h)
        listed = await h.client.list_tools()
        instructions = h.client.instructions
    assert instructions
    check_mentions("server instructions", instructions)
    for tool in listed.tools:
        check_mentions(f"description of {tool.name}", tool.description)
        for prop in tool.input_schema.get("properties", {}).values():
            check_mentions(f"schema of {tool.name}", str(prop.get("description", "")))
    for card in OPERATORS.values():
        check_mentions(f"operator {card.name}", card.instruction_template)
    seen_kinds = set()
    for out in results:
        orders = [out["work_order"]] if out["work_order"] else []
        for order in [*orders, *out["work_orders"]]:
            check_mentions(f"work order {order['kind']}", order["instructions"])
            seen_kinds.add(order["kind"])
        for warning in out["provenance"]["warnings"]:
            check_mentions("warning", warning)
        if out["error"]:
            check_mentions("error hint", out["error"].get("hint") or "")
    assert seen_kinds == {
        "typical_set",
        "anti_typical",
        "fanout_task",
        "collide",
        "frame_operate",
        "judge",
        "question_gate",
        "evolve",
    }
