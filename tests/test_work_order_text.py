"""Every work order the server can emit is a self-contained, literal Traditional Chinese brief."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from cgu_support import CountingTransport
from test_mcp_tools_contract import run_everything, wiki_responder

EXPECTED_KINDS = {
    "anti_typical",
    "collide",
    "evolve",
    "fanout_task",
    "frame_operate",
    "inquiry_explicate",
    "inquiry_label",
    "inquiry_organize",
    "judge",
    "question_gate",
    "typical_set",
}


def collect_orders(results: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    orders: dict[str, dict[str, Any]] = {}
    for out in results:
        found = [out["work_order"]] if out.get("work_order") else []
        found.extend(out.get("work_orders") or [])
        for order in found:
            orders.setdefault(order["kind"], order)
    return orders


async def test_every_work_order_states_shape_guardrail_and_example(
    open_cgu: Callable[..., Any],
) -> None:
    async with open_cgu(http_client=CountingTransport(wiki_responder).client) as h:
        results, _ = await run_everything(h)
    orders = collect_orders(results)
    assert set(orders) == EXPECTED_KINDS
    for kind, order in orders.items():
        text = order["instructions"]
        assert len(re.findall(r"[\u4e00-\u9fff]", text)) >= 150, kind
        assert len(text) <= 1500, kind
        assert "護欄" in text and "範例" in text, kind
        assert re.search(r"cgu_\w+\(", text), kind
        assert "$" not in text, kind
        assert "\n\n\n" not in text, kind
        assert order["output_schema"], kind
        assert order["submit_with"]["tool"].startswith("cgu_"), kind
