"""evals.judge：匿名化、位置對調、JSON 解析重試、評審模型備援。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from test_evals_support import make_cell, write_run_json

from evals import common, judge, runner
from evals.copilot_cli import CliRequest, CliResult, FakeBackend, make_events

LEAK_WORDS = ("baseline", "plugin", "cgu", "creative-ideation", "skill", "MCP")


def judge_json(winner: str = "A", **overrides) -> str:
    obj = {
        "criteria": dict.fromkeys(judge.RUBRIC_KEYS, winner),
        "overconfidence": {"A": "low", "B": "high"},
        "overall_winner": winner,
        "reason": "理由。",
    }
    obj.update(overrides)
    return json.dumps(obj, ensure_ascii=False)


def cli_result(text: str, exit_code: int = 0) -> CliResult:
    events = make_events(text, model="j", plugin=False, skill=None, cgu_tools=[])
    stdout = "\n".join(json.dumps(e, ensure_ascii=False) for e in events)
    return CliResult(exit_code=exit_code, stdout=stdout, stderr="", duration_s=0.1)


class Scripted:
    def __init__(self, texts: list[str | CliResult]) -> None:
        self.texts = texts
        self.prompts: list[str] = []
        self.models: list[str] = []

    def __call__(self, req: CliRequest) -> CliResult:
        self.prompts.append(req.prompt)
        self.models.append(req.model)
        item = self.texts[min(len(self.prompts) - 1, len(self.texts) - 1)]
        return item if isinstance(item, CliResult) else cli_result(item)


def build_run(tmp_path: Path, *, leak: bool = False) -> Path:
    run_dir = tmp_path / "run"
    write_run_json(run_dir)
    for task in ("t1", "t2"):
        for model in ("m1", "m2"):
            make_cell(run_dir, "baseline", model, task, f"基線答案 {task} {model}")
            plugin_answer = f"外掛答案 {task} {model}"
            if leak:
                plugin_answer += " 我用了 cgu_spark 與 creative-ideation 的方法。"
            make_cell(run_dir, "plugin", model, task, plugin_answer)
            make_cell(run_dir, "plugin_explicit", model, task, f"明示答案 {task} {model}")
    return run_dir


# ---------------------------------------------------------------- 位置與規劃


def test_assign_positions_and_winner_mapping() -> None:
    pair = ("baseline", "plugin")
    assert judge.assign_positions(pair, "AB") == ("baseline", "plugin")
    assert judge.assign_positions(pair, "BA") == ("plugin", "baseline")
    with pytest.raises(ValueError):
        judge.assign_positions(pair, "XX")
    assert judge.winner_condition("A", "plugin", "baseline") == "plugin"
    assert judge.winner_condition("B", "plugin", "baseline") == "baseline"
    assert judge.winner_condition("tie", "plugin", "baseline") == "tie"


def test_plan_items_covers_both_orders_and_judges(tmp_path: Path) -> None:
    run_dir = build_run(tmp_path)
    cells = judge.load_cells(run_dir)
    pairs = [("baseline", "plugin"), ("baseline", "plugin_explicit")]
    items = judge.plan_items(cells, pairs, ["j1", "j2"])
    assert len(items) == 2 * (2 * 2) * 2 * 2
    assert len({i.key for i in items}) == len(items)
    for item in items:
        a_text = (item.a_dir / "answer.md").read_text("utf-8")
        b_text = (item.b_dir / "answer.md").read_text("utf-8")
        assert item.task_id in a_text and item.gen_model in a_text
        assert item.a_dir.parts[-3] == item.a_condition
        assert item.b_dir.parts[-3] == item.b_condition
        assert {item.a_condition, item.b_condition} == set(item.pair)
        assert a_text != b_text
    by_cell: dict[tuple, set[str]] = {}
    for item in items:
        by_cell.setdefault((item.pair, item.task_id, item.gen_model, item.judge_model), set()).add(
            item.order
        )
    assert all(orders == {"AB", "BA"} for orders in by_cell.values())
    first_in_a = {i.a_condition for i in items if i.order == "AB"}
    assert first_in_a == {"baseline"}


def test_plan_items_skips_cells_missing_either_side(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    write_run_json(run_dir)
    make_cell(run_dir, "baseline", "m1", "t1", "a")
    make_cell(run_dir, "plugin", "m1", "t2", "b")
    failed = make_cell(run_dir, "plugin", "m1", "t1", "c")
    meta = json.loads((failed / "meta.json").read_text("utf-8"))
    meta["status"] = "failed"
    (failed / "meta.json").write_text(json.dumps(meta), "utf-8")
    assert judge.plan_items(judge.load_cells(run_dir), [("baseline", "plugin")], ["j"]) == []


# ---------------------------------------------------------------- 匿名化


def test_scrub_and_truncate() -> None:
    text, n = judge.scrub_answer(
        "用了 cgu_spark、CGU-ideate 與 creative-ideation，另有 creativity-generation-unit"
    )
    assert n == 4
    assert "cgu" not in text.lower() and "creative-ideation" not in text
    assert judge.truncate_answer("x" * 20, 10)[1] is True
    assert judge.truncate_answer("x" * 10, 10) == ("x" * 10, False)
    assert judge.truncate_answer("x" * 50, 0)[1] is False


def test_judge_prompt_contains_only_task_and_two_answers() -> None:
    prompt = judge.build_judge_prompt("需求內容", "答案一", "答案二")
    assert "需求內容" in prompt and "答案一" in prompt and "答案二" in prompt
    for word in judge.RUBRIC_KEYS:
        assert word in prompt
    for word in LEAK_WORDS:
        assert word.lower() not in prompt.lower()


def test_judge_call_never_sees_conditions_prefix_or_tool_names(tmp_path: Path) -> None:
    run_dir = build_run(tmp_path, leak=True)
    for cond in ("baseline", "plugin", "plugin_explicit"):
        prefix = common.EXPLICIT_PREFIX if cond == "plugin_explicit" else ""
        for path in run_dir.glob(f"{cond}/*/*/prompt.txt"):
            path.write_text(prefix + "共同需求", "utf-8")
    backend = Scripted([judge_json("A")])
    ctx = judge.JudgeContext(run_dir=run_dir, work_root=tmp_path / "w", backend=backend)
    items = judge.plan_items(
        judge.load_cells(run_dir), [("baseline", "plugin"), ("baseline", "plugin_explicit")], ["j"]
    )
    records = [judge.run_judge_item(item, ctx) for item in items]
    assert all(r["ok"] for r in records)
    assert backend.prompts
    for prompt in backend.prompts:
        for word in ("baseline", "plugin", "cgu", "creative-ideation"):
            assert word.lower() not in prompt.lower(), word
        assert "共同需求" in prompt
    assert any(sum(r["redactions"].values()) for r in records)


def test_judge_item_maps_label_back_to_condition(tmp_path: Path) -> None:
    run_dir = build_run(tmp_path)
    ctx = judge.JudgeContext(
        run_dir=run_dir, work_root=tmp_path / "w", backend=Scripted([judge_json("A")])
    )
    items = judge.plan_items(judge.load_cells(run_dir), [("baseline", "plugin")], ["j"])
    for item in items:
        record = judge.run_judge_item(item, ctx)
        expected = "baseline" if item.order == "AB" else "plugin"
        assert record["winner"] == expected
        assert record["criteria_winners"]["novelty"] == expected
        assert record["overconfidence"] == {item.a_condition: "low", item.b_condition: "high"}
        assert record["a_condition"] == item.a_condition


# ---------------------------------------------------------------- JSON 解析與重試


@pytest.mark.parametrize(
    "text",
    [
        judge_json("B"),
        "```json\n" + judge_json("B") + "\n```",
        "好的，這是我的評分：\n" + judge_json("B") + "\n以上。",
    ],
)
def test_parse_judge_json_accepts_wrapped_output(text: str) -> None:
    parsed, error = judge.parse_judge_json(text)
    assert error is None
    assert parsed["overall_winner"] == "B"
    assert parsed["criteria"]["practicality"] == "B"
    assert parsed["overconfidence"] == {"A": "low", "B": "high"}


def test_parse_judge_json_normalizes_and_handles_braces_in_strings() -> None:
    raw = json.dumps(
        {
            "criteria": dict.fromkeys(judge.RUBRIC_KEYS, "a"),
            "overall_winner": "平手",
            "reason": "含 {大括號} 的理由",
        },
        ensure_ascii=False,
    )
    parsed, error = judge.parse_judge_json(raw)
    assert error is None
    assert parsed["overall_winner"] == "tie"
    assert parsed["criteria"]["novelty"] == "A"
    assert parsed["overconfidence"] is None
    assert "{大括號}" in parsed["reason"]


@pytest.mark.parametrize(
    "text",
    [
        "",
        "沒有 JSON",
        "{not json}",
        "[1]",
        judge_json("C"),
        judge_json("A", reason=""),
        json.dumps({"overall_winner": "A", "reason": "x"}),
        json.dumps({"overall_winner": "A", "reason": "x", "criteria": {"novelty": "A"}}),
    ],
)
def test_parse_judge_json_rejects_invalid(text: str) -> None:
    parsed, error = judge.parse_judge_json(text)
    assert parsed is None
    assert error


def test_invalid_json_triggers_retry_with_correction_note(tmp_path: Path) -> None:
    run_dir = build_run(tmp_path)
    backend = Scripted(["這不是 JSON", judge_json("B")])
    ctx = judge.JudgeContext(
        run_dir=run_dir, work_root=tmp_path / "w", backend=backend, max_attempts=3
    )
    item = judge.plan_items(judge.load_cells(run_dir), [("baseline", "plugin")], ["j"])[0]
    record = judge.run_judge_item(item, ctx)
    assert record["ok"] is True
    assert record["attempts"] == 2
    assert record["parse_retries"] == 1
    assert "格式錯誤" not in backend.prompts[0]
    assert "格式錯誤" in backend.prompts[1]
    assert backend.prompts[1].startswith(backend.prompts[0])


def test_persistent_garbage_fails_after_max_attempts(tmp_path: Path) -> None:
    run_dir = build_run(tmp_path)
    backend = Scripted(["垃圾"])
    ctx = judge.JudgeContext(
        run_dir=run_dir, work_root=tmp_path / "w", backend=backend, max_attempts=3
    )
    item = judge.plan_items(judge.load_cells(run_dir), [("baseline", "plugin")], ["j"])[0]
    record = judge.run_judge_item(item, ctx)
    assert record["ok"] is False
    assert record["attempts"] == 3
    assert record["error"]
    assert "winner" not in record


def test_cli_failure_is_retried_then_recovers(tmp_path: Path) -> None:
    run_dir = build_run(tmp_path)
    backend = Scripted(
        [CliResult(exit_code=1, stdout="", stderr="x", duration_s=0.1), judge_json("A")]
    )
    ctx = judge.JudgeContext(run_dir=run_dir, work_root=tmp_path / "w", backend=backend)
    item = judge.plan_items(judge.load_cells(run_dir), [("baseline", "plugin")], ["j"])[0]
    record = judge.run_judge_item(item, ctx)
    assert record["ok"] is True and record["attempts"] == 2


# ---------------------------------------------------------------- 模型可用性


def test_judge_model_fallback_is_recorded(tmp_path: Path) -> None:
    class Picky:
        def __call__(self, req: CliRequest) -> CliResult:
            if req.model == "claude-opus-5.5":
                return CliResult(
                    exit_code=1, stdout="", stderr="Model not available", duration_s=0.1
                )
            return cli_result("OK")

    ctx = judge.JudgeContext(run_dir=tmp_path, work_root=tmp_path / "w", backend=Picky())
    info = judge.check_judge_models(["claude-opus-5.5", "gpt-6-sol"], ctx)
    assert info["resolved"] == {"claude-opus-5.5": "claude-opus-5", "gpt-6-sol": "gpt-6-sol"}
    assert any("不可用" in w for w in info["warnings"])
    assert any("取代" in w for w in info["warnings"])


def test_judge_model_all_unavailable(tmp_path: Path) -> None:
    dead = Scripted([CliResult(exit_code=1, stdout="", stderr="no", duration_s=0.1)])
    ctx = judge.JudgeContext(run_dir=tmp_path, work_root=tmp_path / "w", backend=dead)
    info = judge.check_judge_models(["gpt-6-sol"], ctx)
    assert info["resolved"] == {"gpt-6-sol": None}


# ---------------------------------------------------------------- 主程式（dry-run）


def test_judge_main_rejects_oversized_answer_limit_and_missing_run(tmp_path: Path) -> None:
    run_dir = build_run(tmp_path)
    assert judge.main(["--run-dir", str(run_dir), "--dry-run", "--max-answer-chars", "50000"]) == 2
    assert judge.main(["--run-dir", str(tmp_path / "nope"), "--dry-run"]) == 2
    assert judge.main(["--run-dir", str(run_dir), "--dry-run", "--orders", "XY"]) == 2


def test_judge_main_dry_run_is_resumable(tmp_path: Path) -> None:
    run_dir = build_run(tmp_path)
    assert (
        judge.main(["--run-dir", str(run_dir), "--dry-run", "--work-root", str(tmp_path / "w")])
        == 0
    )
    rows = [
        json.loads(line) for line in (run_dir / "judgments.jsonl").read_text("utf-8").splitlines()
    ]
    assert len(rows) == 2 * 4 * 2 * 2
    assert all(r["ok"] for r in rows)
    assert {r["order"] for r in rows} == {"AB", "BA"}
    assert (run_dir / "judge_models.json").exists()
    assert (
        judge.main(["--run-dir", str(run_dir), "--dry-run", "--work-root", str(tmp_path / "w")])
        == 0
    )
    rows_again = (run_dir / "judgments.jsonl").read_text("utf-8").splitlines()
    assert len(rows_again) == len(rows)


def test_runner_dry_run_feeds_judge(tmp_path: Path) -> None:
    plugin_src = tmp_path / "plugin"
    plugin_src.mkdir()
    (plugin_src / "mcp.json").write_text("{}", "utf-8")
    assert (
        runner.main(
            [
                "--dry-run",
                "--run-id",
                "r",
                "--out-root",
                str(tmp_path / "runs"),
                "--work-root",
                str(tmp_path / "work"),
                "--plugin-source",
                str(plugin_src),
                "--tasks",
                "mr-delirium",
                "--models",
                "m",
            ]
        )
        == 0
    )
    run_dir = tmp_path / "runs" / "r"
    backend = FakeBackend()
    assert (
        judge.main(
            ["--run-dir", str(run_dir), "--dry-run", "--work-root", str(tmp_path / "w")],
            backend=backend,
        )
        == 0
    )
    assert backend.calls
    for req in backend.calls:
        for word in ("baseline", "plugin", "creative-ideation"):
            assert word not in req.prompt
