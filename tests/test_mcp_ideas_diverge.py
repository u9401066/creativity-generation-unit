"""cgu_ideas and cgu_diverge, including the optional local-model execution path."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import httpx
import pytest
from cgu_support import CountingTransport, FakeLLM, KeywordSemanticEmbedding, stray_floats


async def add(h: Any, sid: str, *items: tuple[str, str]) -> list[str]:
    out = await h.ok(
        "cgu_ideas",
        action="add",
        session_id=sid,
        ideas=[{"text": text, "kind": kind} for kind, text in items],
    )
    return [i["idea_id"] for i in out["data"]["ideas"]]


async def test_near_duplicates_inside_one_batch_are_flagged_against_the_first(
    open_cgu: Callable[..., Any],
) -> None:
    async with open_cgu() as h:
        sid = await h.session()
        out = await h.ok(
            "cgu_ideas",
            action="add",
            session_id=sid,
            ideas=[
                {
                    "text": "Replace night-time vital sign rounds with wearable monitoring",
                    "kind": "candidate",
                },
                {
                    "text": "replace night time vital sign rounds with wearable monitoring!",
                    "kind": "candidate",
                },
                {"text": "Put a clock and family photos at every bedside", "kind": "candidate"},
            ],
        )
        listed = await h.ok("cgu_ideas", action="list", session_id=sid, kind="candidate")
    first, second, third = out["data"]["ideas"]
    assert first["duplicate_of"] is None and third["duplicate_of"] is None
    assert second["duplicate_of"]["idea_id"] == first["idea_id"]
    similarity = second["duplicate_of"]["similarity"]
    assert similarity["value"] >= 0.8 and "Jaccard" in similarity["method"]
    assert any("near-duplicates" in w for w in out["provenance"]["warnings"])
    assert listed["data"]["count"] == 3
    assert stray_floats(out) == []


async def test_measure_gives_null_for_empty_reference_sets_never_zero(
    open_cgu: Callable[..., Any],
) -> None:
    async with open_cgu() as h:
        sid = await h.session()
        await add(h, sid, ("candidate", "a lone candidate about quiet wards"))
        out = await h.ok("cgu_ideas", action="measure", session_id=sid)
    result = out["data"]["results"][0]
    assert result["novelty"] == {
        "vs_typical": None,
        "vs_human": None,
        "vs_prior_art": None,
        "vs_session": None,
    }
    assert out["data"]["diversity"] is None
    assert out["data"]["embedding"] == {"backend": "ngram-hash", "semantic": False}
    assert out["provenance"]["degraded"] is True
    assert any("semantic=false" in w for w in out["provenance"]["warnings"])


async def test_measure_reports_reference_sizes_and_labels_every_measurement(
    open_cgu: Callable[..., Any],
) -> None:
    async with open_cgu(embedding=KeywordSemanticEmbedding()) as h:
        sid = await h.session()
        typical = await add(
            h,
            sid,
            ("typical", "drug drug sedation"),
            ("typical", "drug dosing"),
        )
        await add(h, sid, ("human", "nurse handover"), ("prior_art", "device wearable"))
        cands = await add(
            h,
            sid,
            ("candidate", "drug drug drug sedation protocol"),
            ("candidate", "nurse nurse nurse checklist"),
            ("candidate", "money paper funding"),
        )
        out = await h.ok(
            "cgu_ideas",
            action="measure",
            session_id=sid,
            thresholds={"jaccard": 1.0, "cosine": 1.0},
        )
    by_id = {r["idea_id"]: r["novelty"] for r in out["data"]["results"]}
    near, mid, far = (by_id[c] for c in cands)
    assert near["vs_typical"]["reference_size"] == 2
    assert near["vs_typical"]["nearest_id"] in typical
    assert near["vs_human"]["reference_size"] == 1 and near["vs_prior_art"]["reference_size"] == 1
    assert near["vs_session"]["reference_size"] == 6
    assert (
        near["vs_typical"]["max_similarity"]["value"] > mid["vs_typical"]["max_similarity"]["value"]
    )
    assert (
        near["vs_typical"]["max_similarity"]["value"] > far["vs_typical"]["max_similarity"]["value"]
    )
    assert out["data"]["embedding"] == {"backend": "fake-keywords", "semantic": True}
    assert out["provenance"]["degraded"] is False
    spread = out["data"]["diversity"]
    assert 1.0 < spread["value"] <= 3.0 and spread["n"] == 3
    assert spread["method"].startswith("Vendi score") and spread["calibrated"] is False
    for m in (near["vs_typical"]["max_similarity"], near["vs_typical"]["mean_similarity"]):
        assert m["reference"] == "session typical set (n=2)"
        assert "semantic embeddings" in m["method"]
    assert stray_floats(out) == []


async def test_measure_thresholds_are_written_into_the_method(open_cgu: Callable[..., Any]) -> None:
    async with open_cgu() as h:
        sid = await h.session()
        await add(
            h,
            sid,
            ("typical", "ward rounds at night with extra staff"),
            ("candidate", "ward rounds at night with fewer staff"),
        )
        default = await h.ok("cgu_ideas", action="measure", session_id=sid)
        loose = await h.ok(
            "cgu_ideas", action="measure", session_id=sid, thresholds={"jaccard": 0.4}
        )
    assert default["data"]["results"][0]["duplicate_of"] is None
    found = loose["data"]["results"][0]["duplicate_of"]
    assert found is not None and "0.4" in found["similarity"]["method"]
    assert "0.4" in loose["data"]["duplicate_rule"]


async def test_measure_unknown_idea_and_input_validation(open_cgu: Callable[..., Any]) -> None:
    async with open_cgu() as h:
        sid = await h.session()
        frame = await h.call("cgu_ideas", action="measure", session_id=sid, idea_ids=["i-nope"])
        bad_frame = await h.call(
            "cgu_ideas",
            action="add",
            session_id=sid,
            ideas=[{"text": "t", "kind": "human", "frame_id": "f-nope"}],
        )
        bad_operator = await h.call(
            "cgu_ideas",
            action="add",
            session_id=sid,
            ideas=[{"text": "t", "kind": "human", "operator": "zap"}],
        )
        bad_parent = await h.call(
            "cgu_ideas",
            action="add",
            session_id=sid,
            ideas=[{"text": "t", "kind": "human", "parent_id": "i-x"}],
        )
        bad_material = await h.call(
            "cgu_ideas",
            action="add",
            session_id=sid,
            ideas=[{"text": "t", "kind": "human", "material_ids": ["fr-x"]}],
        )
        nothing = await h.call("cgu_ideas", action="add", session_id=sid)
        empty_measure = await h.ok("cgu_ideas", action="measure", session_id=sid)
    assert frame["error"]["code"] == "not_found"
    assert bad_frame["error"]["code"] == "not_found"
    assert bad_operator["error"]["code"] == "invalid_input"
    assert bad_parent["error"]["code"] == "not_found"
    assert bad_material["error"]["code"] == "not_found"
    assert nothing["error"]["code"] == "invalid_input"
    assert empty_measure["data"]["results"] == []
    assert empty_measure["provenance"]["warnings"]


async def test_auto_embedding_falls_back_to_ngrams_and_says_so(
    open_cgu: Callable[..., Any],
) -> None:
    def down(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    transport = CountingTransport(down)
    async with open_cgu(embedding_mode="auto", http_client=transport.client) as h:
        status = await h.ok("cgu_status")
        sid = await h.session()
        await add(h, sid, ("typical", "alpha beta gamma"), ("candidate", "delta epsilon zeta"))
        out = await h.ok("cgu_ideas", action="measure", session_id=sid)
    assert status["data"]["embedding"] == {"backend": "ngram-hash", "semantic": False}
    assert any("ollama embedding unavailable" in w for w in out["provenance"]["warnings"])
    assert out["provenance"]["degraded"] is True
    assert len(transport.requests) >= 1


async def test_forced_ollama_embedding_that_is_down_is_an_unavailable_error(
    open_cgu: Callable[..., Any],
) -> None:
    def down(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    transport = CountingTransport(down)
    async with open_cgu(embedding_mode="ollama", http_client=transport.client) as h:
        status = await h.ok("cgu_status")
        sid = await h.session()
        await add(h, sid, ("candidate", "something"))
        out = await h.call("cgu_ideas", action="measure", session_id=sid)
    assert status["data"]["embedding"]["backend"] == "unavailable"
    assert out["ok"] is False and out["error"]["code"] == "unavailable"


async def test_working_ollama_embedding_is_semantic(open_cgu: Callable[..., Any]) -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        import json

        texts = json.loads(request.content)["input"]
        return httpx.Response(200, json={"embeddings": [[1.0, 0.1 * len(t), 0.5] for t in texts]})

    transport = CountingTransport(respond)
    async with open_cgu(embedding_mode="ollama", http_client=transport.client) as h:
        status = await h.ok("cgu_status")
        sid = await h.session()
        await add(h, sid, ("typical", "short"), ("candidate", "a much longer candidate text"))
        out = await h.ok("cgu_ideas", action="measure", session_id=sid)
    assert status["data"]["embedding"] == {"backend": "ollama:nomic-embed-text", "semantic": True}
    assert out["data"]["embedding"]["semantic"] is True
    assert out["provenance"]["degraded"] is False
    assert str(transport.requests[0].url).endswith("/api/embed")


async def test_typical_set_work_order_is_self_contained(open_cgu: Callable[..., Any]) -> None:
    async with open_cgu() as h:
        sid = await h.session("postoperative delirium")
        frame = await h.ok(
            "cgu_frame",
            action="create",
            session_id=sid,
            problem="reduce delirium",
            assumptions=["drugs"],
        )
        out = await h.ok(
            "cgu_diverge",
            action="typical_set",
            session_id=sid,
            frame_id=frame["data"]["frame_id"],
            k=5,
        )
    order = out["work_order"]
    assert out["provenance"]["engine"] == "passthrough"
    assert order["kind"] == "typical_set" and order["independence"] == "same_context_ok"
    text = order["instructions"]
    assert "5 個" in text and "reduce delirium" in text and sid in text
    assert 'kind": "typical"' in text and "護欄" in text and "範例" in text
    assert order["output_schema"]["type"] == "array"
    assert order["submit_with"]["tool"] == "cgu_ideas" and order["submit_with"]["action"] == "add"
    assert order["submit_with"]["args_template"]["session_id"] == sid


async def test_anti_typical_attaches_avoid_list_and_operators(open_cgu: Callable[..., Any]) -> None:
    async with open_cgu() as h:
        sid = await h.session()
        first = await h.ok("cgu_diverge", action="anti_typical", session_id=sid)
        await add(h, sid, ("typical", "reduce sedatives"), ("typical", "mobilise early"))
        out = await h.ok(
            "cgu_diverge",
            action="anti_typical",
            session_id=sid,
            operators=["negate", "swap_metaphor"],
            n=3,
        )
        bad = await h.call("cgu_diverge", action="anti_typical", session_id=sid, operators=["zap"])
    assert any("no typical ideas" in w for w in first["provenance"]["warnings"])
    order = out["work_order"]
    assert order["inputs"]["avoid"] == ["reduce sedatives", "mobilise early"]
    assert [o["name"] for o in order["inputs"]["operators"]] == ["negate", "swap_metaphor"]
    assert "negate" in order["instructions"] and "3 個" in order["instructions"]
    assert "meta" in order["instructions"] and "rewrote" in order["instructions"]
    assert out["data"]["avoid_count"] == 2 and out["provenance"]["warnings"] == []
    assert bad["ok"] is False and bad["error"]["code"] == "invalid_input"


async def test_fanout_orders_are_independent_with_distinct_seeds_and_variations(
    open_cgu: Callable[..., Any],
) -> None:
    async with open_cgu() as h:
        sid = await h.session(seed=11)
        await h.ok(
            "cgu_material",
            action="add",
            session_id=sid,
            fragments=[{"text": "tidal rhythm of ward noise", "source_type": "web"}],
        )
        out = await h.ok(
            "cgu_diverge",
            action="fanout",
            session_id=sid,
            n=4,
            vary=["prompt", "material", "operator", "model"],
        )
        none_material = await h.ok(
            "cgu_diverge", action="fanout", session_id=sid, n=2, vary=["prompt"]
        )
        default = await h.ok("cgu_diverge", action="fanout", session_id=sid)
    orders = out["work_orders"]
    assert len(orders) == 4 and len(default["work_orders"]) == 4
    assert all(o["independence"] == "separate_context_recommended" for o in orders)
    assert all("不得參考其他任務的輸出" in o["instructions"] for o in orders)
    assert len({o["inputs"]["seed"] for o in orders}) == 4
    assert len({o["inputs"]["variation"] for o in orders}) == 4
    assert [o["inputs"]["model_slot"] for o in orders] == [1, 2, 3, 4]
    assert all(
        o["inputs"]["materials"][0]["fenced_text"].startswith("<untrusted_data") for o in orders
    )
    assert len({o["inputs"]["operator"] for o in orders}) == 4
    assert len(none_material["work_orders"]) == 2


async def test_fanout_without_material_warns_and_rejects_unknown_dimensions(
    open_cgu: Callable[..., Any],
) -> None:
    async with open_cgu() as h:
        sid = await h.session()
        out = await h.ok("cgu_diverge", action="fanout", session_id=sid, n=2, vary=["material"])
        schema_error = await h.client.call_tool(
            "cgu_diverge", {"action": "fanout", "session_id": sid, "vary": ["telepathy"]}
        )
        too_many = await h.call("cgu_diverge", action="fanout", session_id=sid, n=9)
    assert any("none" in w for w in out["provenance"]["warnings"])
    assert schema_error.is_error is True
    assert too_many["ok"] is False and too_many["error"]["code"] == "invalid_input"


@pytest.mark.parametrize("mode", ["analogy", "bridge"])
async def test_collide_modes_produce_checklists_and_resolve_references(
    open_cgu: Callable[..., Any], mode: str
) -> None:
    async with open_cgu() as h:
        sid = await h.session()
        (idea,) = await add(h, sid, ("human", "pre-operative risk stratification"))
        out = await h.ok(
            "cgu_diverge", action="collide", session_id=sid, a=idea, b="airport security", mode=mode
        )
        missing = await h.call("cgu_diverge", action="collide", session_id=sid, a="only a")
    text = out["work_order"]["instructions"]
    assert "pre-operative risk stratification" in text and "airport security" in text
    assert out["work_order"]["kind"] == "collide"
    if mode == "analogy":
        assert "一對一" in text and "checklist" in text and "relations_not_attributes" in text
    else:
        assert "橋接" in text and "hops" in text
    assert "距離只是變數" in text or mode == "analogy"
    assert missing["ok"] is False


async def test_provider_ollama_runs_typical_set_locally_and_marks_the_ideas(
    open_cgu: Callable[..., Any],
) -> None:
    llm = FakeLLM('{"ideas": ["local typical one", "local typical two", "local typical three"]}')
    async with open_cgu(provider="ollama", llm=llm) as h:
        sid = await h.session("night wards", seed=5)
        out = await h.ok("cgu_diverge", action="typical_set", session_id=sid, k=2)
        stored = await h.ok("cgu_ideas", action="list", session_id=sid, kind="typical")
    assert out["provenance"]["engine"] == "ollama" and out["provenance"]["model"] == "fake-local"
    assert out["work_order"] is None and out["data"]["executed"] is True
    assert len(out["data"]["idea_ids"]) == 2
    assert [i["text"] for i in stored["data"]["ideas"]] == [
        "local typical one",
        "local typical two",
    ]
    assert stored["data"]["ideas"][0]["meta"] == {"engine": "ollama", "model": "fake-local"}
    assert len(llm.calls) == 1 and "typical_set" in llm.calls[0] and "night wards" in llm.calls[0]


async def test_provider_ollama_executes_anti_typical_only_when_there_is_something_to_avoid(
    open_cgu: Callable[..., Any],
) -> None:
    llm = FakeLLM('["alt one", "alt two"]')
    async with open_cgu(provider="ollama", llm=llm) as h:
        sid = await h.session()
        without = await h.ok("cgu_diverge", action="anti_typical", session_id=sid, n=2)
        await add(h, sid, ("typical", "the usual answer"))
        with_avoid = await h.ok("cgu_diverge", action="anti_typical", session_id=sid, n=2)
        cands = await h.ok("cgu_ideas", action="list", session_id=sid, kind="candidate")
    assert without["work_order"] is not None and llm.calls and len(llm.calls) == 1
    assert with_avoid["data"]["executed"] is True
    assert [i["text"] for i in cands["data"]["ideas"]] == ["alt one", "alt two"]


async def test_provider_ollama_fanout_runs_each_order_and_failure_returns_the_orders(
    open_cgu: Callable[..., Any],
) -> None:
    llm = FakeLLM('{"ideas": ["x one", "x two", "x three"]}')
    async with open_cgu(provider="ollama", llm=llm) as h:
        sid = await h.session()
        out = await h.ok("cgu_diverge", action="fanout", session_id=sid, n=3)
    assert len(llm.calls) == 3 and out["data"]["executed"] is True
    assert len(out["data"]["idea_ids"]) == 9

    junk = FakeLLM("sorry, I cannot help with that")
    async with open_cgu(provider="ollama", llm=junk) as h:
        sid = await h.session()
        failed = await h.ok("cgu_diverge", action="typical_set", session_id=sid)
    assert failed["provenance"]["degraded"] is True
    assert failed["work_order"] is not None and failed["data"]["executed"] is False
    assert "execute the work order yourself" in failed["provenance"]["warnings"][0]
