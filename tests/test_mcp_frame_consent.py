"""cgu_frame: lineage, disclosure, consent (SDK 2 Elicit through Resolve) and doubt."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from cgu_support import Harness, stray_floats
from mcp_types import ElicitResult

STAKEHOLDER_CHILD = {
    "why": "the ward nurse carries the cost and was missing",
    "checks": {"veil_of_ignorance": "a nurse would ask for a handover checklist first"},
    "stakeholders": [
        {"id": "s1", "who": "surgeon", "bears_costs": False},
        {"who": "ward nurse", "bears_costs": True},
    ],
}
NEGATE_CHILD = {
    "why": "reverse the drug assumption",
    "assumptions": [
        {"id": "a1", "text": "badly managed sedation withdrawal causes delirium"},
        {"id": "a2", "text": "only ICU patients matter"},
    ],
}


async def make_frame(h: Harness) -> tuple[str, str]:
    sid = await h.session()
    frame = await h.ok(
        "cgu_frame",
        action="create",
        session_id=sid,
        problem="reduce postoperative delirium",
        stakeholders=[{"who": "surgeon", "bears_costs": False}],
        assumptions=["sedative drugs cause delirium", "only ICU patients matter"],
        criteria=["speed of rollout"],
    )
    return sid, frame["data"]["frame_id"]


async def children_of(h: Harness, sid: str, fid: str) -> list[str]:
    out = await h.ok("cgu_frame", action="get", session_id=sid, frame_id=fid)
    return list(out["data"]["children"])


def elicit(reply: dict[str, Any] | None, action: str = "accept") -> Any:
    asked: list[str] = []

    async def callback(context: Any, params: Any) -> ElicitResult:
        asked.append(params.message)
        return ElicitResult(action=action, content=reply)  # type: ignore[arg-type]

    callback.asked = asked  # type: ignore[attr-defined]
    return callback


@pytest.mark.parametrize("mode", ["legacy", "2026-07-28"])
async def test_unrestricted_commit_needs_no_consent_and_records_a_disclosure(
    open_cgu: Callable[..., Any], mode: str
) -> None:
    async with open_cgu(mode=mode) as h:
        sid, fid = await make_frame(h)
        out = await h.ok(
            "cgu_frame",
            action="commit",
            session_id=sid,
            frame_id=fid,
            operator="negate",
            child=NEGATE_CHILD,
        )
        disclosure = out["data"]["disclosure"]
        assert disclosure["operator"] == "negate"
        assert disclosure["source"]
        assert disclosure["why"] == "reverse the drug assumption"
        assert disclosure["restricted_kinds"] == [] and disclosure["consent"] is None
        assert [(c["kind"], c["id"], c["change"]) for c in disclosure["changed"]] == [
            ("assumption", "a1", "modified")
        ]
        assert "sedative drugs cause delirium" in disclosure["changed"][0]["before"]
        assert "frame_id" in out["data"]["frame"]
        assert await children_of(h, sid, fid) == [out["data"]["child_frame_id"]]


async def test_lineage_runs_from_the_root_to_the_child(open_cgu: Callable[..., Any]) -> None:
    async with open_cgu() as h:
        sid, fid = await make_frame(h)
        first = await h.ok(
            "cgu_frame",
            action="commit",
            session_id=sid,
            frame_id=fid,
            operator="negate",
            child=NEGATE_CHILD,
        )
        child = first["data"]["child_frame_id"]
        second = await h.ok(
            "cgu_frame",
            action="commit",
            session_id=sid,
            frame_id=child,
            operator="bracket",
            child={
                "why": "bracket the ICU assumption",
                "assumptions": [NEGATE_CHILD["assumptions"][0]],
            },
        )
        got = await h.ok(
            "cgu_frame", action="get", session_id=sid, frame_id=second["data"]["child_frame_id"]
        )
        lineage = got["data"]["lineage"]
    assert [step["operator"] for step in lineage] == [None, "negate", "bracket"]
    assert [step["frame_id"] for step in lineage][0] == fid
    assert lineage[2]["changed"][0]["change"] == "removed"


async def test_restricted_rewrite_without_a_capable_client_returns_consent_required_and_writes_nothing(
    open_cgu: Callable[..., Any],
) -> None:
    async with open_cgu() as h:
        sid, fid = await make_frame(h)
        refused = await h.call(
            "cgu_frame",
            action="commit",
            session_id=sid,
            frame_id=fid,
            operator="shift_stakeholder",
            child=STAKEHOLDER_CHILD,
        )
        assert refused["ok"] is False
        assert refused["error"]["code"] == "consent_required"
        assert refused["data"]["requires_consent"] is True
        assert refused["data"]["restricted_kinds"] == ["stakeholder"]
        assert refused["data"]["changes"][0]["after"].startswith("ward nurse")
        assert await children_of(h, sid, fid) == []
        counts = (await h.ok("cgu_session", action="get", session_id=sid))["data"]["counts"]
        assert counts["frames"] == 1

        granted = await h.ok(
            "cgu_frame",
            action="commit",
            session_id=sid,
            frame_id=fid,
            operator="shift_stakeholder",
            child=STAKEHOLDER_CHILD,
            consent={"granted": True, "note": "the user agreed in chat"},
        )
        consent = granted["data"]["disclosure"]["consent"]
        assert consent == {"granted": True, "note": "the user agreed in chat", "via": "caller"}
        assert granted["data"]["disclosure"]["restricted_kinds"] == ["stakeholder"]
        assert len(await children_of(h, sid, fid)) == 1


async def test_a_caller_supplied_refusal_is_final_and_does_not_prompt(
    open_cgu: Callable[..., Any],
) -> None:
    callback = elicit({"granted": True})
    async with open_cgu(client_kwargs={"elicitation_callback": callback}) as h:
        sid, fid = await make_frame(h)
        out = await h.call(
            "cgu_frame",
            action="commit",
            session_id=sid,
            frame_id=fid,
            operator="shift_stakeholder",
            child=STAKEHOLDER_CHILD,
            consent={"granted": False, "note": "user said no"},
        )
        assert out["ok"] is False and out["error"]["code"] == "consent_required"
        assert out["data"]["declined"] is True
        assert await children_of(h, sid, fid) == []
    assert callback.asked == []


@pytest.mark.parametrize("mode", ["legacy", "2026-07-28"])
async def test_elicitation_accept_writes_with_via_elicitation(
    open_cgu: Callable[..., Any], mode: str
) -> None:
    callback = elicit({"granted": True, "note": "ok by dialog"})
    async with open_cgu(mode=mode, client_kwargs={"elicitation_callback": callback}) as h:
        sid, fid = await make_frame(h)
        out = await h.ok(
            "cgu_frame",
            action="commit",
            session_id=sid,
            frame_id=fid,
            operator="shift_stakeholder",
            child=STAKEHOLDER_CHILD,
        )
        assert out["data"]["disclosure"]["consent"] == {
            "granted": True,
            "note": "ok by dialog",
            "via": "elicitation",
        }
        assert len(await children_of(h, sid, fid)) == 1
    assert len(callback.asked) == 1
    assert "stakeholder" in callback.asked[0]


@pytest.mark.parametrize("mode", ["legacy", "2026-07-28"])
@pytest.mark.parametrize(
    "reply", [("accept", {"granted": False}), ("decline", None), ("cancel", None)]
)
async def test_elicitation_refusal_blocks_the_write(
    open_cgu: Callable[..., Any], mode: str, reply: tuple[str, dict[str, Any] | None]
) -> None:
    callback = elicit(reply[1], action=reply[0])
    async with open_cgu(mode=mode, client_kwargs={"elicitation_callback": callback}) as h:
        sid, fid = await make_frame(h)
        out = await h.call(
            "cgu_frame",
            action="commit",
            session_id=sid,
            frame_id=fid,
            operator="shift_stakeholder",
            child=STAKEHOLDER_CHILD,
        )
        assert out["ok"] is False and out["error"]["code"] == "consent_required"
        assert out["data"]["declined"] is True
        assert await children_of(h, sid, fid) == []
    assert len(callback.asked) == 1


async def test_unrestricted_commits_never_prompt_even_for_capable_clients(
    open_cgu: Callable[..., Any],
) -> None:
    callback = elicit({"granted": True})
    async with open_cgu(client_kwargs={"elicitation_callback": callback}) as h:
        sid, fid = await make_frame(h)
        await h.ok(
            "cgu_frame",
            action="commit",
            session_id=sid,
            frame_id=fid,
            operator="negate",
            child=NEGATE_CHILD,
        )
        await h.ok("cgu_frame", action="get", session_id=sid, frame_id=fid)
    assert callback.asked == []


async def test_invalid_restricted_drafts_are_reported_not_prompted(
    open_cgu: Callable[..., Any],
) -> None:
    callback = elicit({"granted": True})
    async with open_cgu(client_kwargs={"elicitation_callback": callback}) as h:
        sid, fid = await make_frame(h)
        no_check = await h.call(
            "cgu_frame",
            action="commit",
            session_id=sid,
            frame_id=fid,
            operator="shift_stakeholder",
            child={"why": "add the nurse", "stakeholders": STAKEHOLDER_CHILD["stakeholders"]},
        )
    assert no_check["error"]["code"] == "invalid_input"
    assert "veil_of_ignorance" in no_check["error"]["message"]
    assert callback.asked == []


async def test_operate_marks_restricted_targets_and_builds_a_literal_work_order(
    open_cgu: Callable[..., Any],
) -> None:
    async with open_cgu() as h:
        sid, fid = await make_frame(h)
        plain = await h.ok(
            "cgu_frame",
            action="operate",
            session_id=sid,
            frame_id=fid,
            operator="negate",
            target="a1",
        )
        restricted = await h.ok(
            "cgu_frame",
            action="operate",
            session_id=sid,
            frame_id=fid,
            operator="invert_criterion",
            target="criterion",
        )
        by_kind = await h.ok(
            "cgu_frame",
            action="operate",
            session_id=sid,
            frame_id=fid,
            operator="explicate",
            target="assumption",
        )
    assert plain["data"]["requires_consent"] is False
    assert restricted["data"]["requires_consent"] is True
    assert "consent" in restricted["work_order"]["submit_with"]["args_template"]
    order = plain["work_order"]
    assert order["kind"] == "frame_operate"
    assert "reduce postoperative delirium" in order["instructions"]
    assert order["inputs"]["parent_frame"]["assumptions"][0]["id"] == "a1"
    assert order["submit_with"]["action"] == "commit"
    assert order["output_schema"]["properties"]["why"]
    assert by_kind["provenance"]["warnings"], "explicate without typical ideas must warn"


async def test_explicate_work_order_carries_the_sessions_typical_ideas(
    open_cgu: Callable[..., Any],
) -> None:
    async with open_cgu() as h:
        sid, fid = await make_frame(h)
        await h.ok(
            "cgu_ideas",
            action="add",
            session_id=sid,
            ideas=[{"text": "mobilise early", "kind": "typical"}],
        )
        out = await h.ok(
            "cgu_frame",
            action="operate",
            session_id=sid,
            frame_id=fid,
            operator="explicate",
            target="assumption",
        )
    assert out["work_order"]["inputs"]["typical_ideas"] == ["mobilise early"]
    assert out["provenance"]["warnings"] == []


async def test_operator_cards_listing_matches_the_spec(open_cgu: Callable[..., Any]) -> None:
    async with open_cgu() as h:
        sid, _ = await make_frame(h)
        out = await h.ok("cgu_frame", action="operators", session_id=sid)
    cards = out["data"]["operators"]
    assert len(cards) == 11
    for card in cards:
        assert {"name", "source", "summary", "targets", "restricted", "guardrails"} <= set(card)
    assert {c["name"] for c in cards if c["restricted"]} == {
        "shift_stakeholder",
        "invert_criterion",
        "genealogize",
    }


async def test_doubt_ranks_by_caller_estimates_and_labels_the_method(
    open_cgu: Callable[..., Any],
) -> None:
    async with open_cgu() as h:
        sid, fid = await make_frame(h)
        out = await h.ok(
            "cgu_frame",
            action="doubt",
            session_id=sid,
            frame_id=fid,
            signals={"stalled_rounds": 3},
            estimates={
                "a1": {
                    "load_bearing": 0.9,
                    "uncertainty": 0.8,
                    "decision_impact": 0.9,
                    "irreversibility": 0.6,
                },
                "a2": {
                    "load_bearing": 0.9,
                    "uncertainty": 0.4,
                    "decision_impact": 0.5,
                    "irreversibility": 0.2,
                },
            },
            budget={"max_questions": 1},
        )
        quiet = await h.ok("cgu_frame", action="doubt", session_id=sid, frame_id=fid)
        unknown = await h.call(
            "cgu_frame",
            action="doubt",
            session_id=sid,
            frame_id=fid,
            estimates={
                "a9": {
                    "load_bearing": 1,
                    "uncertainty": 1,
                    "decision_impact": 1,
                    "irreversibility": 1,
                }
            },
        )
    data = out["data"]
    assert data["escalate"] is True and data["triggers"] == ["stalled"]
    assert [r["assumption_id"] for r in data["ranked"]] == ["a1", "a2"]
    priority = data["ranked"][0]["priority"]
    assert priority["value"] == pytest.approx(0.9 * 0.8 * 0.9 * 0.6)
    assert "uncalibrated" in priority["method"] and priority["calibrated"] is False
    assert data["selected"] == ["a1"]
    assert "budget_exhausted" in data["stop_reasons"]
    assert data["untested_load_bearing"] == ["a2"]
    assert stray_floats(out) == []
    assert quiet["data"]["escalate"] is False and "no_trigger" in quiet["data"]["stop_reasons"]
    assert unknown["ok"] is False and unknown["error"]["code"] == "invalid_input"
