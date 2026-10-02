"""evals.aggregate：勝率、CI、順序一致率、評審間一致率、長度比與端到端報告。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from test_evals_support import make_cell, write_run_json

from evals import aggregate, judge, runner
from evals.stats import wilson_interval

PAIR = "baseline:plugin"


def jrow(
    task: str,
    winner: str,
    *,
    model: str = "m1",
    judge_model: str = "j1",
    order: str = "AB",
    domain: str = "medical_research",
    repeat: int = 0,
    pair: str = PAIR,
    ok: bool = True,
    **extra: Any,
) -> dict[str, Any]:
    base, treatment = pair.split(":")
    a, b = (base, treatment) if order == "AB" else (treatment, base)
    label = "A" if winner == a else "B" if winner == b else "tie"
    return {
        "key": f"{pair}|{task}|{model}|r{repeat}|{judge_model}|{order}",
        "pair": pair,
        "task_id": task,
        "domain": domain,
        "gen_model": model,
        "repeat": repeat,
        "judge_model": judge_model,
        "order": order,
        "a_condition": a,
        "b_condition": b,
        "ok": ok,
        "winner": winner,
        "overall_label": label,
        "criteria_winners": dict.fromkeys(aggregate.RUBRIC_LABELS, winner),
        "overconfidence": {base: "low", treatment: "high"},
        "redactions": {"A": 0, "B": 0},
        "truncated": {"A": False, "B": False},
        "parse_retries": 0,
        **extra,
    }


def all_orders(task: str, winner_ab: str, winner_ba: str, **kw: Any) -> list[dict[str, Any]]:
    return [jrow(task, winner_ab, order="AB", **kw), jrow(task, winner_ba, order="BA", **kw)]


def test_all_wins_gives_wilson_lower_bound_and_positive_verdict() -> None:
    judgments = []
    for i in range(10):
        judgments += all_orders(f"t{i}", "plugin", "plugin")
    stats = aggregate.pair_analysis(PAIR, judgments, {})
    overall = stats["overall"]
    assert (overall["wins"], overall["losses"], overall["ties"]) == (10, 0, 0)
    assert overall["win_rate"] == 1.0
    assert overall["ci95"][0] == pytest.approx(wilson_interval(10, 10)[0])
    assert "下界 > 50%" in stats["verdict"]
    assert stats["order_consistency"]["rate"] == 1.0


def test_position_flips_cancel_into_ties() -> None:
    judgments = []
    for i in range(4):
        judgments += all_orders(f"t{i}", "baseline", "plugin")
    stats = aggregate.pair_analysis(PAIR, judgments, {})
    assert stats["overall"]["ties"] == 4
    assert stats["overall"]["win_rate"] is None
    assert stats["overall"]["ci95"] is None
    assert stats["order_consistency"]["rate"] == 0.0
    assert stats["position_bias"]["a_win_rate"] == 1.0
    assert "沒有決勝資料" in stats["verdict"]


def test_negative_result_is_reported() -> None:
    judgments = []
    for i in range(10):
        judgments += all_orders(f"t{i}", "baseline", "baseline")
    stats = aggregate.pair_analysis(PAIR, judgments, {})
    assert stats["overall"]["win_rate"] == 0.0
    assert stats["overall"]["ci95"][1] < 0.5
    assert "負面結果" in stats["verdict"]


def test_mixed_results_span_fifty_percent() -> None:
    judgments = []
    for i in range(3):
        judgments += all_orders(f"w{i}", "plugin", "plugin")
    for i in range(3):
        judgments += all_orders(f"l{i}", "baseline", "baseline")
    stats = aggregate.pair_analysis(PAIR, judgments, {})
    assert stats["overall"]["win_rate"] == 0.5
    assert "跨越 50%" in stats["verdict"]


def test_cell_outcome_uses_all_judgments_in_the_cell() -> None:
    group = [
        jrow("t", "plugin", judge_model="j1", order="AB"),
        jrow("t", "plugin", judge_model="j2", order="AB"),
        jrow("t", "baseline", judge_model="j1", order="BA"),
        jrow("t", "tie", judge_model="j2", order="BA"),
    ]
    assert aggregate.cell_outcome(group) == "win"
    assert aggregate.cell_outcome(group[:3]) == "win"
    assert aggregate.cell_outcome([group[2]]) == "loss"
    assert aggregate.cell_outcome([group[3]]) == "tie"


def test_order_consistency_rate() -> None:
    judgments = []
    for i in range(3):
        judgments += all_orders(f"t{i}", "plugin", "plugin")
    judgments += all_orders("flip", "plugin", "baseline")
    result = aggregate.order_consistency([j for j in judgments if j["ok"]])
    assert result["pairs_with_both_orders"] == 4
    assert result["consistent"] == 3
    assert result["rate"] == 0.75
    only_ab = aggregate.order_consistency([jrow("x", "plugin", order="AB")])
    assert only_ab["pairs_with_both_orders"] == 0 and only_ab["rate"] is None


def test_judge_agreement_and_kappa() -> None:
    rows = []
    for i in range(6):
        winner = "plugin" if i % 2 == 0 else "baseline"
        rows.append(jrow(f"t{i}", winner, judge_model="j1"))
        rows.append(jrow(f"t{i}", winner, judge_model="j2"))
    full = aggregate.judge_agreement(rows)
    assert full["n"] == 6
    assert full["agreement"] == 1.0
    assert full["kappa"] == pytest.approx(1.0)
    rows[1] = jrow("t0", "baseline", judge_model="j2")
    partial = aggregate.judge_agreement(rows)
    assert partial["agreement"] == pytest.approx(5 / 6)
    assert "j1 vs j2" in partial["by_judge_pair"]
    assert aggregate.judge_agreement([jrow("t", "plugin")])["agreement"] is None


def test_breakdowns_by_model_domain_and_judge() -> None:
    judgments = []
    for i in range(5):
        judgments += all_orders(
            f"a{i}", "plugin", "plugin", model="m1", domain="d1", judge_model="j1"
        )
    for i in range(5):
        judgments += all_orders(
            f"b{i}", "baseline", "baseline", model="m2", domain="d2", judge_model="j2"
        )
    stats = aggregate.pair_analysis(PAIR, judgments, {})
    assert stats["by_model"]["m1"]["win_rate"] == 1.0
    assert stats["by_model"]["m2"]["win_rate"] == 0.0
    assert set(stats["by_domain"]) == {"d1", "d2"}
    assert stats["by_judge"]["j1"]["wins"] == 5
    assert stats["by_judge"]["j2"]["losses"] == 5
    assert stats["by_judge"]["j1"]["judgment_level"]["judgments"] == 10


def test_length_ratio_and_longer_wins_flag() -> None:
    judgments = []
    metas = {}
    for i in range(6):
        task = f"t{i}"
        judgments += all_orders(task, "plugin", "plugin")
        metas[("baseline", "m1", task, 0)] = {"answer_chars": 1000}
        metas[("plugin", "m1", task, 0)] = {"answer_chars": 2500}
    stats = aggregate.pair_analysis(PAIR, judgments, metas)
    length = stats["length"]
    assert length["mean_ratio"] == pytest.approx(2.5)
    assert length["longer_wins"] == 6 and length["longer_decisive"] == 6
    assert length["flag"] is True
    assert length["length_matched"]["cells"] == 0


def test_length_matched_subset_and_no_flag() -> None:
    judgments = []
    metas = {}
    for i in range(4):
        task = f"t{i}"
        judgments += all_orders(task, "baseline", "baseline")
        metas[("baseline", "m1", task, 0)] = {"answer_chars": 1000}
        metas[("plugin", "m1", task, 0)] = {"answer_chars": 1100}
    length = aggregate.pair_analysis(PAIR, judgments, metas)["length"]
    assert length["length_matched"]["cells"] == 4
    assert length["flag"] is False
    assert length["longer_wins"] == 0


def test_criteria_overconfidence_and_leakage() -> None:
    judgments = all_orders("t0", "plugin", "plugin")
    judgments += all_orders("t1", "baseline", "baseline", redactions={"A": 2, "B": 0})
    stats = aggregate.pair_analysis(PAIR, judgments, {})
    assert stats["criteria"]["novelty"]["wins"] == 2
    assert stats["criteria"]["novelty"]["losses"] == 2
    assert stats["overconfidence"]["baseline_mean"] == 0
    assert stats["overconfidence"]["treatment_mean"] == 2
    assert stats["leakage"]["judgments_with_redactions"] == 2
    assert stats["leakage"]["clean_cells"]["cells"] == 1
    assert stats["leakage"]["clean_cells"]["wins"] == 1


def test_load_judgments_prefers_successful_retry(tmp_path: Path) -> None:
    run_dir = tmp_path / "r"
    run_dir.mkdir()
    bad = {**jrow("t", "plugin"), "ok": False, "error": "x"}
    good = jrow("t", "plugin")
    other = {**jrow("u", "plugin"), "ok": False}
    lines = [bad, good, other]
    (run_dir / "judgments.jsonl").write_text(
        "\n".join(json.dumps(r) for r in lines) + "\n", "utf-8"
    )
    loaded = {j["key"]: j for j in aggregate.load_judgments(run_dir)}
    assert loaded[good["key"]]["ok"] is True
    assert loaded[other["key"]]["ok"] is False
    assert len(loaded) == 2


def test_condition_stats_from_metas() -> None:
    metas = {
        ("plugin", "m", "t1", 0): {
            "condition": "plugin",
            "status": "ok",
            "cgu_connected": True,
            "cgu_tool_calls": 2,
            "cgu_tools": {"a": 1, "b": 1},
            "skills_invoked": ["creative-ideation"],
            "duration_s": 10,
            "answer_chars": 100,
            "usage": {"input_tokens": 1000, "output_tokens": 50},
            "warnings": ["x:y"],
        },
        ("plugin", "m", "t2", 0): {
            "condition": "plugin",
            "status": "ok",
            "cgu_connected": True,
            "cgu_tool_calls": 0,
            "cgu_tools": {},
            "skills_invoked": [],
            "duration_s": 20,
            "answer_chars": 300,
            "usage": {"input_tokens": 3000, "output_tokens": 150},
            "warnings": [],
        },
        ("plugin", "m", "t3", 0): {
            "condition": "plugin",
            "status": "failed",
            "failure_reason": "timeout",
        },
    }
    stats = aggregate.condition_stats(metas)["plugin"]
    assert stats["cells"] == 3 and stats["ok"] == 2 and stats["failed"] == 1
    assert stats["any_cgu_call_rate"] == 0.5
    assert stats["mean_cgu_calls"] == 1.0
    assert stats["skill_invoked_rate"] == 0.5
    assert stats["mean_input_tokens"] == 2000
    assert stats["failure_reasons"] == {"timeout": 1}
    assert stats["cgu_tool_histogram"] == {"a": 1, "b": 1}


def test_end_to_end_dry_run_report(tmp_path: Path) -> None:
    plugin_src = tmp_path / "plugin"
    plugin_src.mkdir()
    (plugin_src / "mcp.json").write_text("{}", "utf-8")
    assert (
        runner.main(
            [
                "--dry-run",
                "--run-id",
                "e2e",
                "--out-root",
                str(tmp_path / "runs"),
                "--work-root",
                str(tmp_path / "work"),
                "--plugin-source",
                str(plugin_src),
                "--models",
                "m1,m2",
                "--jobs",
                "4",
            ]
        )
        == 0
    )
    run_dir = tmp_path / "runs" / "e2e"
    assert (
        judge.main(
            [
                "--run-dir",
                str(run_dir),
                "--dry-run",
                "--work-root",
                str(tmp_path / "jw"),
                "--jobs",
                "4",
            ]
        )
        == 0
    )
    reports = tmp_path / "reports"
    assert (
        aggregate.main(["--run-dir", str(run_dir), "--reports-dir", str(reports), "--name", "x"])
        == 0
    )

    data = json.loads((reports / "x.json").read_text("utf-8"))
    assert set(data["pairs"]) == {"baseline:plugin", "baseline:plugin_explicit"}
    pair = data["pairs"]["baseline:plugin"]
    assert pair["overall"]["cells"] == 12
    assert pair["judgment_level"]["judgments"] == 48
    assert set(pair["by_model"]) == {"m1", "m2"}
    assert set(pair["by_domain"]) == {"medical_research", "medical_product", "admin_process"}
    assert set(pair["by_judge"]) == {"claude-opus-5.5", "gpt-6-sol"}
    assert data["conditions"]["plugin"]["cgu_connected_rate"] == 1.0

    report = (reports / "x.md").read_text("utf-8")
    for needle in (
        "dry-run",
        "Wilson",
        "## 6. 限制",
        "不能」說明什麼",
        "順序一致率",
        "長度偏誤",
        "等預算",
    ):
        assert needle in report
    assert "baseline vs plugin_explicit" in report


def test_report_without_judgments_does_not_crash(tmp_path: Path) -> None:
    run_dir = tmp_path / "r"
    write_run_json(
        run_dir, started_at="t", models=["m"], tasks=["t"], conditions=["baseline"], repeats=1
    )
    make_cell(run_dir, "baseline", "m", "t", "答案", cgu_connected=False, usage={})
    data = aggregate.aggregate(run_dir)
    text = aggregate.render_report(data)
    assert "沒有有效的評審紀錄" in text
    assert data["pairs"] == {}
