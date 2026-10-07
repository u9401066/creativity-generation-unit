"""cgu_inquiry through the SDK 2 client: consent (Elicit and caller), gating, errors, no network."""

from __future__ import annotations

import ast
from collections.abc import Callable
from typing import Any

import httpx
import pytest
from cgu_support import SRC, CountingTransport, FakeLLM, Harness, measurements, stray_floats
from inquiry_support import CLUSTER_DIM, ClusterEmbedding  # noqa: F401
from mcp_types import ElicitResult

NOTE = "yes please, remember my questions on this machine"
QUESTIONS = [
    "how can drug alpha bravo charlie matter at our hospital",
    "how can drug delta echo foxtrot matter at our hospital",
    "how can drug golf hotel india matter at our hospital",
    "why does device alpha bravo charlie matter at our hospital",
    "why does device delta echo foxtrot matter at our hospital",
    "why does device golf hotel india matter at our hospital",
]


def elicit(reply: dict[str, Any] | None, action: str = "accept") -> Any:
    asked: list[str] = []

    async def callback(context: Any, params: Any) -> ElicitResult:
        asked.append(params.message)
        return ElicitResult(action=action, content=reply)  # type: ignore[arg-type]

    callback.asked = asked  # type: ignore[attr-defined]
    return callback


async def enabled_state(h: Harness) -> Any:
    out = await h.ok("cgu_inquiry", action="settings")
    return out["data"]["enabled"]


async def enable(h: Harness) -> None:
    await h.ok(
        "cgu_inquiry", action="settings", enable=True, consent={"granted": True, "note": NOTE}
    )


# --- consent ---------------------------------------------------------------------------------------


async def test_enabling_without_consent_or_a_capable_client_is_refused_and_records_nothing(
    open_cgu: Callable[..., Any],
) -> None:
    async with open_cgu() as h:
        assert await enabled_state(h) is None
        refused = await h.call("cgu_inquiry", action="settings", enable=True)
        assert refused["ok"] is False and refused["error"]["code"] == "consent_required"
        assert refused["data"]["requires_consent"] is True
        assert refused["data"]["disclosure"]["never_recorded"]
        assert "consent" in refused["error"]["hint"]
        assert await enabled_state(h) is None
        captured = await h.ok("cgu_inquiry", action="capture", text="a question")
        assert captured["data"]["recorded"] is False
        assert captured["data"]["reason"] == "consent_not_asked"


async def test_a_caller_needs_granted_true_and_the_users_words(
    open_cgu: Callable[..., Any],
) -> None:
    async with open_cgu() as h:
        silent = await h.call(
            "cgu_inquiry", action="settings", enable=True, consent={"granted": True, "note": ""}
        )
        assert silent["ok"] is False and silent["error"]["code"] == "consent_required"
        no = await h.call(
            "cgu_inquiry",
            action="settings",
            enable=True,
            consent={"granted": False, "note": "the user said no"},
        )
        assert no["ok"] is False and no["data"]["declined"] is True
        assert await enabled_state(h) is False
        yes = await h.ok(
            "cgu_inquiry", action="settings", enable=True, consent={"granted": True, "note": NOTE}
        )
        assert yes["data"]["enabled"] is True
        assert yes["data"]["consent"]["via"] == "caller" and yes["data"]["consent"]["note"] == NOTE
        assert yes["data"]["consent"]["at"]


async def test_disabling_needs_no_consent_and_does_not_prompt(
    open_cgu: Callable[..., Any],
) -> None:
    callback = elicit({"granted": True})
    async with open_cgu(client_kwargs={"elicitation_callback": callback}) as h:
        await enable(h)
        off = await h.ok("cgu_inquiry", action="settings", enable=False)
        assert off["data"]["enabled"] is False
    assert callback.asked == []


@pytest.mark.parametrize("mode", ["legacy", "2026-07-28"])
async def test_elicitation_accept_enables_with_via_elicitation(
    open_cgu: Callable[..., Any], mode: str
) -> None:
    callback = elicit({"granted": True, "note": "ok by dialog"})
    async with open_cgu(mode=mode, client_kwargs={"elicitation_callback": callback}) as h:
        out = await h.ok("cgu_inquiry", action="settings", enable=True)
        assert out["data"]["enabled"] is True
        assert out["data"]["consent"]["via"] == "elicitation"
        assert out["data"]["consent"]["note"] == "ok by dialog"
        recorded = await h.ok("cgu_inquiry", action="capture", text="a recorded question")
        assert recorded["data"]["recorded"] is True
    assert len(callback.asked) == 1
    assert "本機" in callback.asked[0] and "姓名" in callback.asked[0]


@pytest.mark.parametrize("mode", ["legacy", "2026-07-28"])
@pytest.mark.parametrize(
    ("reply", "remembered"),
    [(("accept", {"granted": False}), False), (("decline", None), False), (("cancel", None), None)],
)
async def test_elicitation_refusal_keeps_recording_off(
    open_cgu: Callable[..., Any],
    mode: str,
    reply: tuple[str, dict[str, Any] | None],
    remembered: Any,
) -> None:
    callback = elicit(reply[1], action=reply[0])
    async with open_cgu(mode=mode, client_kwargs={"elicitation_callback": callback}) as h:
        out = await h.call("cgu_inquiry", action="settings", enable=True)
        assert out["ok"] is False and out["error"]["code"] == "consent_required"
        assert await enabled_state(h) is remembered
        capture = await h.ok("cgu_inquiry", action="capture", text="a question")
        assert capture["data"]["recorded"] is False
        assert capture["data"]["reason"] == (
            "consent_not_asked" if remembered is None else "disabled"
        )
    assert len(callback.asked) == 1


async def test_a_caller_supplied_consent_skips_the_dialog(open_cgu: Callable[..., Any]) -> None:
    callback = elicit({"granted": False})
    async with open_cgu(client_kwargs={"elicitation_callback": callback}) as h:
        await enable(h)
        assert await enabled_state(h) is True
    assert callback.asked == []


async def test_no_dialog_when_already_enabled(open_cgu: Callable[..., Any]) -> None:
    callback = elicit({"granted": True, "note": "dialog"})
    async with open_cgu(client_kwargs={"elicitation_callback": callback}) as h:
        await enable(h)
        again = await h.ok("cgu_inquiry", action="settings", enable=True)
        assert again["data"]["enabled"] is True
    assert callback.asked == []


async def test_other_actions_never_prompt(open_cgu: Callable[..., Any]) -> None:
    callback = elicit({"granted": True})
    async with open_cgu(client_kwargs={"elicitation_callback": callback}) as h:
        await h.ok("cgu_inquiry", action="settings")
        await h.ok("cgu_inquiry", action="capture", text="not recorded")
        await h.ok("cgu_inquiry", action="themes")
        await h.ok("cgu_inquiry", action="mine")
        await h.ok("cgu_inquiry", action="export")
    assert callback.asked == []


# --- status, capture, errors -----------------------------------------------------------------------


async def test_cgu_status_reports_the_inquiry_block(open_cgu: Callable[..., Any]) -> None:
    async with open_cgu() as h:
        before = (await h.ok("cgu_status"))["data"]["inquiry"]
        assert before == {
            "enabled": None,
            "count": 0,
            "maintenance": {"pending": 0, "materials": 0, "organize_after": 20, "due": False},
        }
        await enable(h)
        await h.ok("cgu_inquiry", action="capture", text="first question here")
        after = (await h.ok("cgu_status"))["data"]["inquiry"]
        assert after == {
            "enabled": True,
            "count": 1,
            "maintenance": {"pending": 1, "materials": 0, "organize_after": 20, "due": False},
        }
        await h.ok("cgu_inquiry", action="settings", enable=False)
        assert (await h.ok("cgu_status"))["data"]["inquiry"] == {
            "enabled": False,
            "count": 1,
            "maintenance": {"pending": 1, "materials": 0, "organize_after": 20, "due": False},
        }


async def test_capture_links_a_session_and_excluded_projects_are_skipped(
    open_cgu: Callable[..., Any],
) -> None:
    async with open_cgu() as h:
        await enable(h)
        sid = await h.session()
        out = await h.ok(
            "cgu_inquiry",
            action="capture",
            text="how can we reduce delirium?",
            session_id=sid,
            project="D:\\work\\ward",
            source="manual",
        )
        assert out["data"]["recorded"] and out["data"]["project"] == "ward"
        assert out["data"]["source"] == "manual" and out["data"]["family_id"].startswith("fam-")
        await h.ok("cgu_inquiry", action="settings", excluded_projects=["ward"])
        skipped = await h.ok(
            "cgu_inquiry", action="capture", text="another question", project="ward"
        )
        assert (
            skipped["data"]["recorded"] is False and skipped["data"]["reason"] == "excluded_project"
        )
        listed = await h.ok("cgu_inquiry", action="list")
        assert listed["data"]["total"] == 1
        assert listed["data"]["items"][0]["session_id"] == sid
        assert listed["data"]["items"][0]["project"] == "ward"


async def test_batch_capture_via_items_reports_redactions_and_the_note(
    open_cgu: Callable[..., Any],
) -> None:
    async with open_cgu() as h:
        await enable(h)
        out = await h.ok(
            "cgu_inquiry",
            action="capture",
            items=[
                {"text": "寄到 me@x.org 好嗎", "project": "a"},
                {"text": "電話 0912-345-678 可以嗎", "source": "import"},
            ],
        )
        assert out["data"]["count"] == 2
        assert out["data"]["redactions"]["email"] == 1 and out["data"]["redactions"]["phone"] == 1
        assert "姓名" in out["data"]["redaction_note"]
        listed = await h.ok("cgu_inquiry", action="list")
        assert {i["source"] for i in listed["data"]["items"]} == {"agent", "import"}
        assert all(
            "@" not in i["text"] and "0912" not in i["text"] for i in listed["data"]["items"]
        )


@pytest.mark.parametrize(
    ("arguments", "code"),
    [
        ({"action": "capture"}, "invalid_input"),
        ({"action": "capture", "text": "q", "items": [{"text": "r"}]}, "invalid_input"),
        ({"action": "capture", "text": "q", "session_id": "s-nope"}, "not_found"),
        ({"action": "capture", "text": "q", "occurred_at": "later"}, "invalid_input"),
        ({"action": "label", "labels": [{"theme_id": "th-nope", "label": "x"}]}, "not_found"),
        ({"action": "label"}, "invalid_input"),
        ({"action": "related"}, "invalid_input"),
        ({"action": "mine", "limit": 0}, "invalid_input"),
        ({"action": "list", "theme_id": "th-nope"}, "not_found"),
        ({"action": "list", "limit": 9999}, "invalid_input"),
        ({"action": "themes", "threshold": 5.0}, "invalid_input"),
        ({"action": "themes", "min_size": 0}, "invalid_input"),
        ({"action": "delete", "all": True}, "invalid_input"),
        ({"action": "delete", "confirm": True}, "invalid_input"),
    ],
)
async def test_domain_errors_are_ok_false_results_not_exceptions(
    open_cgu: Callable[..., Any], arguments: dict[str, Any], code: str
) -> None:
    async with open_cgu() as h:
        await enable(h)
        out = await h.call("cgu_inquiry", **arguments)
        assert out["ok"] is False and out["error"]["code"] == code
        assert out["error"]["message"]
        assert stray_floats(out) == []


async def test_delete_needs_confirm_and_then_leaves_nothing(open_cgu: Callable[..., Any]) -> None:
    async with open_cgu() as h:
        await enable(h)
        await h.ok("cgu_inquiry", action="capture", items=[{"text": t} for t in QUESTIONS])
        await h.ok("cgu_inquiry", action="themes")
        await h.ok("cgu_inquiry", action="mine")
        refused = await h.call("cgu_inquiry", action="delete", all=True)
        assert refused["ok"] is False and "confirm" in refused["error"]["message"]
        assert (await h.ok("cgu_inquiry", action="list"))["data"]["total"] == 6
        done = await h.ok("cgu_inquiry", action="delete", all=True, confirm=True)
        assert done["data"]["deleted"] == 6 and done["data"]["remaining"] == 0
        exported = (await h.ok("cgu_inquiry", action="export"))["data"]
        assert (
            exported["inquiries"] == [] and exported["themes"] == [] and exported["sources"] == []
        )


async def test_deleting_a_cgu_session_deletes_its_linked_questions(
    open_cgu: Callable[..., Any],
) -> None:
    async with open_cgu() as h:
        await enable(h)
        sid = await h.session()
        await h.ok("cgu_inquiry", action="capture", text="linked question one", session_id=sid)
        await h.ok("cgu_inquiry", action="capture", text="free question two")
        await h.ok("cgu_session", action="delete", session_id=sid, confirm=True)
        listed = await h.ok("cgu_inquiry", action="list")
        assert [i["text"] for i in listed["data"]["items"]] == ["free question two"]
        assert (await h.ok("cgu_status"))["data"]["inquiry"]["count"] == 1


# --- floats live in Measurements; the output never claims a creativity score ---------------------


async def test_every_float_that_leaves_cgu_inquiry_is_inside_a_measurement(
    open_cgu: Callable[..., Any],
) -> None:
    async with open_cgu(embedding_mode="ngram") as h:
        await enable(h)
        await h.ok("cgu_inquiry", action="capture", items=[{"text": t} for t in QUESTIONS * 2])
        outputs = [
            await h.ok("cgu_inquiry", action="settings"),
            await h.ok("cgu_inquiry", action="list"),
            await h.ok("cgu_inquiry", action="themes", min_size=1, threshold=0.99),
            await h.ok("cgu_inquiry", action="mine", limit=5),
            await h.ok("cgu_inquiry", action="related", query="how can drug matter"),
            await h.ok("cgu_inquiry", action="export"),
        ]
    for out in outputs:
        assert stray_floats(out) == [], stray_floats(out)
        for m in measurements(out):
            assert m["calibrated"] is False and m["method"] and m["reference"]
    themes = outputs[2]["data"]
    assert themes["threshold"]["value"] == pytest.approx(0.99)
    assert "parameter" in themes["threshold"]["method"].lower() or themes["threshold"]["method"]
    blob = str(outputs).lower()
    assert "creativity_score" not in blob and "creativity score" not in blob


# --- zero network ---------------------------------------------------------------------------------


def responder(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json={})


async def test_no_inquiry_action_touches_the_network_or_a_model(
    open_cgu: Callable[..., Any],
) -> None:
    transport = CountingTransport(responder)
    llm = FakeLLM()
    async with open_cgu(http_client=transport.client, llm=llm, embedding_mode="ngram") as h:
        await h.ok("cgu_inquiry", action="settings")
        await enable(h)
        await h.ok("cgu_inquiry", action="settings", excluded_projects=["scratch"])
        sid = await h.session()
        await h.ok("cgu_inquiry", action="capture", text=QUESTIONS[0], session_id=sid)
        await h.ok(
            "cgu_inquiry", action="capture", items=[{"text": t, "project": "p"} for t in QUESTIONS]
        )
        await h.ok("cgu_inquiry", action="list")
        themes = await h.ok("cgu_inquiry", action="themes", min_size=1, threshold=0.99)
        stored = await h.ok("cgu_inquiry", action="themes")
        if stored["data"]["themes"]:
            await h.ok(
                "cgu_inquiry",
                action="label",
                labels=[{"theme_id": stored["data"]["themes"][0]["theme_id"], "label": "x"}],
            )
        await h.ok("cgu_inquiry", action="mine")
        await h.ok("cgu_inquiry", action="related", query="how can drug matter")
        await h.ok("cgu_inquiry", action="export")
        await h.ok("cgu_inquiry", action="delete", all=True, confirm=True)
        assert themes["data"]["themes"]
    assert transport.requests == []
    assert llm.calls == []


def _imported(nodes: list[ast.AST]) -> set[str]:
    names: set[str] = set()
    for root in nodes:
        for node in ast.walk(root):
            if isinstance(node, ast.Import):
                names.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                names.add(node.module.split(".")[0])
    return names


def test_inquiry_code_paths_import_no_network_library() -> None:
    forbidden = {"httpx", "requests", "urllib", "urllib3", "http", "socket", "aiohttp", "ssl"}
    files = [
        *(SRC / "domain").glob("*.py"),
        SRC / "application" / "services" / "inquiry.py",
        SRC / "application" / "services" / "inquiry_instructions.py",
        SRC / "application" / "services" / "inquiry_maintenance.py",
        SRC / "infrastructure" / "schema.py",
        SRC / "infrastructure" / "inquiry_sql.py",
        SRC / "interfaces" / "mcp" / "tools" / "inquiry.py",
    ]
    assert len(files) > 6
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        assert not _imported([tree]) & forbidden, (path.name, _imported([tree]) & forbidden)
    # The CLI builds an httpx client lazily, only for the embedding adapter (a local Ollama);
    # the module top level and the hook path never import it.
    cli = ast.parse((SRC / "interfaces" / "inquiry_cli.py").read_text(encoding="utf-8"))
    top = [n for n in cli.body if isinstance(n, ast.Import | ast.ImportFrom)]
    assert not _imported(list(top)) & forbidden
    hook = next(
        n for n in cli.body if isinstance(n, ast.FunctionDef) and n.name == "_record_from_hook"
    )
    assert not _imported([hook]) & forbidden
