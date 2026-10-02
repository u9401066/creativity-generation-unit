"""彙整階段：由評審結果與執行紀錄產生 zh-TW 報告（.md）與機器可讀摘要（.json）。

用法：uv run --no-project python -m evals.aggregate --run-dir evals/runs/<ts>
"""

from __future__ import annotations

import argparse
import itertools
import sys
from collections import Counter, defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from evals import common
from evals.common import read_json, read_jsonl, write_json
from evals.stats import (
    cohen_kappa,
    fmt_interval,
    fmt_rate,
    mean,
    median,
    wilson_interval,
)

RUBRIC_LABELS = {
    "novelty": "新穎度（相對典型答案）",
    "practicality": "實用性與可行性",
    "reframing": "問題框架重寫",
    "decidability": "可決策性與可驗證性",
}
LEVEL_SCORE = {"low": 0, "medium": 1, "high": 2}
LENGTH_MATCH_RANGE = (0.67, 1.5)


# ---------------------------------------------------------------- 載入


def split_pair(pair: str) -> tuple[str, str]:
    base, _, treatment = pair.partition(":")
    return base, treatment


def load_judgments(run_dir: Path) -> list[dict[str, Any]]:
    """依 key 去重：同 key 若有成功紀錄就取最後一筆成功紀錄，否則取最後一筆。"""
    latest: dict[str, dict[str, Any]] = {}
    for row in read_jsonl(run_dir / "judgments.jsonl"):
        key = row.get("key")
        if not key:
            continue
        prev = latest.get(key)
        if prev is None or row.get("ok") or not prev.get("ok"):
            latest[key] = row
    return list(latest.values())


def load_metas(run_dir: Path) -> dict[tuple[str, str, str, int], dict[str, Any]]:
    metas: dict[tuple[str, str, str, int], dict[str, Any]] = {}
    for path in run_dir.glob("*/*/*/meta.json"):
        meta = read_json(path)
        key = (meta["condition"], meta["model"], meta["task_id"], int(meta.get("repeat", 0)))
        metas[key] = meta
    return metas


# ---------------------------------------------------------------- 勝率核心


def judgment_score(j: dict[str, Any]) -> float:
    """從處理組（pair 的第二項）角度：勝 1、平 0.5、負 0。"""
    base, treatment = split_pair(j["pair"])
    winner = j.get("winner")
    if winner == treatment:
        return 1.0
    if winner == base:
        return 0.0
    return 0.5


def group_cells(judgments: Iterable[dict[str, Any]]) -> dict[tuple, list[dict[str, Any]]]:
    groups: dict[tuple, list[dict[str, Any]]] = defaultdict(list)
    for j in judgments:
        groups[(j["pair"], j["task_id"], j["gen_model"], j.get("repeat", 0))].append(j)
    return groups


def cell_outcome(group: list[dict[str, Any]]) -> str:
    score = mean(judgment_score(j) for j in group)
    if score is None or abs(score - 0.5) < 1e-9:
        return "tie"
    return "win" if score > 0.5 else "loss"


def summarize_outcomes(outcomes: list[str]) -> dict[str, Any]:
    counts = Counter(outcomes)
    wins, losses, ties = counts["win"], counts["loss"], counts["tie"]
    decisive = wins + losses
    total = len(outcomes)
    interval = wilson_interval(wins, decisive)
    half = wins + 0.5 * ties
    return {
        "cells": total,
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "decisive": decisive,
        "win_rate": wins / decisive if decisive else None,
        "ci95": list(interval) if interval else None,
        "win_rate_ties_half": half / total if total else None,
        "ci95_ties_half_approx": list(wilson_interval(half, total) or []) or None,
    }


def summarize_groups(groups: Iterable[list[dict[str, Any]]]) -> dict[str, Any]:
    return summarize_outcomes([cell_outcome(g) for g in groups])


def summarize_judgments(judgments: list[dict[str, Any]]) -> dict[str, Any]:
    scores = [judgment_score(j) for j in judgments]
    wins = sum(1 for s in scores if s == 1.0)
    losses = sum(1 for s in scores if s == 0.0)
    ties = len(scores) - wins - losses
    interval = wilson_interval(wins, wins + losses)
    return {
        "judgments": len(scores),
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "win_rate": wins / (wins + losses) if wins + losses else None,
        "ci95": list(interval) if interval else None,
    }


def verdict(stats: dict[str, Any]) -> str:
    ci = stats.get("ci95")
    if not stats.get("decisive") or not ci:
        return "沒有決勝資料，無法下結論。"
    lo, hi = ci
    if lo > 0.5:
        return (
            "處理組勝率的 95% CI 下界 > 50%：在這組題目與評審設定下，處理組較常勝出"
            "（不代表可推廣到其他題目、模型或真實使用者）。"
        )
    if hi < 0.5:
        return "處理組勝率的 95% CI 上界 < 50%：在這組題目與評審設定下，baseline 較常勝出（負面結果）。"
    return "95% CI 跨越 50%：無法與「沒有差別」區分，不得宣稱處理組較好或較差。"


# ---------------------------------------------------------------- 各項診斷


def order_consistency(valid: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[tuple, dict[str, str]] = defaultdict(dict)
    for j in valid:
        key = (j["pair"], j["task_id"], j["gen_model"], j.get("repeat", 0), j["judge_model"])
        groups[key][j["order"]] = j["winner"]
    both = [g for g in groups.values() if "AB" in g and "BA" in g]
    consistent = sum(1 for g in both if g["AB"] == g["BA"])
    interval = wilson_interval(consistent, len(both))
    return {
        "pairs_with_both_orders": len(both),
        "consistent": consistent,
        "rate": consistent / len(both) if both else None,
        "ci95": list(interval) if interval else None,
    }


def position_bias(valid: list[dict[str, Any]]) -> dict[str, Any]:
    decisive = [j for j in valid if j.get("overall_label") in ("A", "B")]
    a_wins = sum(1 for j in decisive if j["overall_label"] == "A")
    interval = wilson_interval(a_wins, len(decisive))
    return {
        "decisive": len(decisive),
        "a_win_rate": a_wins / len(decisive) if decisive else None,
        "ci95": list(interval) if interval else None,
    }


def judge_agreement(valid: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[tuple, dict[str, str]] = defaultdict(dict)
    for j in valid:
        base, treatment = split_pair(j["pair"])
        role = (
            "treatment"
            if j["winner"] == treatment
            else "baseline"
            if j["winner"] == base
            else "tie"
        )
        key = (j["pair"], j["task_id"], j["gen_model"], j.get("repeat", 0), j["order"])
        groups[key][j["judge_model"]] = role
    labels: list[tuple[str, str]] = []
    per_pair: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for g in groups.values():
        for (m1, r1), (m2, r2) in itertools.combinations(sorted(g.items()), 2):
            labels.append((r1, r2))
            per_pair[f"{m1} vs {m2}"].append((r1, r2))

    def summarize(items: list[tuple[str, str]]) -> dict[str, Any]:
        agree = sum(1 for a, b in items if a == b)
        return {
            "n": len(items),
            "agreement": agree / len(items) if items else None,
            "kappa": cohen_kappa(items),
        }

    return {**summarize(labels), "by_judge_pair": {k: summarize(v) for k, v in per_pair.items()}}


def length_analysis(
    groups: dict[tuple, list[dict[str, Any]]],
    metas: dict[tuple[str, str, str, int], dict[str, Any]],
) -> dict[str, Any]:
    ratios: list[float] = []
    longer_wins = decisive = 0
    matched_groups: list[list[dict[str, Any]]] = []
    for (pair, task_id, model, repeat), group in groups.items():
        base, treatment = split_pair(pair)
        b = metas.get((base, model, task_id, repeat))
        t = metas.get((treatment, model, task_id, repeat))
        if not b or not t or not b.get("answer_chars") or not t.get("answer_chars"):
            continue
        ratio = t["answer_chars"] / b["answer_chars"]
        ratios.append(ratio)
        if LENGTH_MATCH_RANGE[0] <= ratio <= LENGTH_MATCH_RANGE[1]:
            matched_groups.append(group)
        outcome = cell_outcome(group)
        if outcome != "tie" and ratio != 1.0:
            decisive += 1
            treatment_longer = ratio > 1.0
            longer_wins += (outcome == "win") == treatment_longer
    interval = wilson_interval(longer_wins, decisive)
    return {
        "cells_with_length": len(ratios),
        "mean_ratio": mean(ratios),
        "median_ratio": median(ratios),
        "longer_wins": longer_wins,
        "longer_decisive": decisive,
        "longer_wins_rate": longer_wins / decisive if decisive else None,
        "longer_wins_ci95": list(interval) if interval else None,
        "length_matched_range": list(LENGTH_MATCH_RANGE),
        "length_matched": summarize_groups(matched_groups),
        "flag": bool(
            (mean(ratios) or 0) >= 1.3 or (decisive >= 5 and interval and interval[0] > 0.5)
        ),
    }


def criteria_analysis(valid: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in RUBRIC_LABELS:
        rows = []
        for j in valid:
            base, treatment = split_pair(j["pair"])
            w = (j.get("criteria_winners") or {}).get(key)
            if w is None:
                continue
            rows.append(1.0 if w == treatment else 0.0 if w == base else 0.5)
        wins = sum(1 for s in rows if s == 1.0)
        losses = sum(1 for s in rows if s == 0.0)
        interval = wilson_interval(wins, wins + losses)
        out[key] = {
            "judgments": len(rows),
            "wins": wins,
            "losses": losses,
            "ties": len(rows) - wins - losses,
            "win_rate": wins / (wins + losses) if wins + losses else None,
            "ci95": list(interval) if interval else None,
        }
    return out


def overconfidence_analysis(valid: list[dict[str, Any]]) -> dict[str, Any]:
    scores: dict[str, list[int]] = {"baseline": [], "treatment": []}
    for j in valid:
        conf = j.get("overconfidence")
        if not conf:
            continue
        base, treatment = split_pair(j["pair"])
        scores["baseline"].append(LEVEL_SCORE[conf[base]])
        scores["treatment"].append(LEVEL_SCORE[conf[treatment]])
    return {
        "judgments": len(scores["baseline"]),
        "baseline_mean": mean(scores["baseline"]),
        "treatment_mean": mean(scores["treatment"]),
        "scale": "low=0, medium=1, high=2（評審對『確定語氣但無法驗證』主張的主觀評等）",
    }


def leak_analysis(groups: dict[tuple, list[dict[str, Any]]], valid: list[dict[str, Any]]) -> dict:
    leaked = [j for j in valid if any((j.get("redactions") or {}).values())]
    clean_groups = [
        g for g in groups.values() if not any(any((j.get("redactions") or {}).values()) for j in g)
    ]
    return {
        "judgments_with_redactions": len(leaked),
        "judgments": len(valid),
        "clean_cells": summarize_groups(clean_groups),
        "truncated_judgments": sum(1 for j in valid if any((j.get("truncated") or {}).values())),
    }


def pair_analysis(
    pair: str,
    judgments: list[dict[str, Any]],
    metas: dict[tuple[str, str, str, int], dict[str, Any]],
) -> dict[str, Any]:
    valid = [j for j in judgments if j.get("ok") and j["pair"] == pair]
    failed = [j for j in judgments if not j.get("ok") and j.get("pair") == pair]
    groups = group_cells(valid)
    overall = summarize_groups(groups.values())

    def by(field: str) -> dict[str, Any]:
        keys = sorted({j[field] for j in valid})
        return {
            k: {
                **summarize_groups(group_cells([j for j in valid if j[field] == k]).values()),
                "judgment_level": summarize_judgments([j for j in valid if j[field] == k]),
            }
            for k in keys
        }

    return {
        "pair": pair,
        "baseline": split_pair(pair)[0],
        "treatment": split_pair(pair)[1],
        "overall": overall,
        "judgment_level": summarize_judgments(valid),
        "verdict": verdict(overall),
        "by_model": by("gen_model"),
        "by_domain": by("domain"),
        "by_judge": by("judge_model"),
        "order_consistency": order_consistency(valid),
        "position_bias": position_bias(valid),
        "judge_agreement": judge_agreement(valid),
        "length": length_analysis(groups, metas),
        "criteria": criteria_analysis(valid),
        "overconfidence": overconfidence_analysis(valid),
        "leakage": leak_analysis(groups, valid),
        "judgments_failed": len(failed),
        "parse_retries": sum(int(j.get("parse_retries", 0)) for j in valid),
        "cells": [
            {
                "task_id": key[1],
                "gen_model": key[2],
                "repeat": key[3],
                "outcome": cell_outcome(group),
                "mean_treatment_score": mean(judgment_score(j) for j in group),
                "judgments": len(group),
            }
            for key, group in sorted(groups.items(), key=lambda kv: kv[0])
        ],
    }


def condition_stats(metas: dict[tuple[str, str, str, int], dict[str, Any]]) -> dict[str, Any]:
    by_cond: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for meta in metas.values():
        by_cond[meta["condition"]].append(meta)

    def avg(rows: list[dict[str, Any]], getter) -> float | None:
        return mean(v for v in (getter(r) for r in rows) if v is not None)

    out: dict[str, Any] = {}
    for cond, rows in sorted(by_cond.items()):
        ok = [r for r in rows if r.get("status") == "ok"]
        tools: Counter[str] = Counter()
        for r in ok:
            tools.update(r.get("cgu_tools") or {})
        warn: Counter[str] = Counter()
        for r in rows:
            warn.update(w.split(":")[0] for w in r.get("warnings") or [])
        out[cond] = {
            "cells": len(rows),
            "ok": len(ok),
            "failed": len(rows) - len(ok),
            "failure_reasons": dict(
                Counter(r.get("failure_reason") for r in rows if r.get("status") != "ok")
            ),
            "cgu_connected_rate": mean(1.0 if r.get("cgu_connected") else 0.0 for r in ok)
            if ok
            else None,
            "any_cgu_call_rate": mean(1.0 if r.get("cgu_tool_calls") else 0.0 for r in ok)
            if ok
            else None,
            "mean_cgu_calls": avg(ok, lambda r: r.get("cgu_tool_calls")),
            "cgu_tool_histogram": dict(tools.most_common()),
            "skill_invoked_rate": mean(
                1.0 if "creative-ideation" in (r.get("skills_invoked") or []) else 0.0 for r in ok
            )
            if ok
            else None,
            "mean_duration_s": avg(ok, lambda r: r.get("duration_s")),
            "mean_answer_chars": avg(ok, lambda r: r.get("answer_chars")),
            "mean_input_tokens": avg(ok, lambda r: (r.get("usage") or {}).get("input_tokens")),
            "mean_output_tokens": avg(ok, lambda r: (r.get("usage") or {}).get("output_tokens")),
            "mean_chat_calls": avg(ok, lambda r: (r.get("usage") or {}).get("chat_calls")),
            "mean_premium_requests": avg(
                ok, lambda r: (r.get("usage") or {}).get("premium_requests")
            ),
            "warnings": dict(warn.most_common()),
        }
    return out


def aggregate(run_dir: Path) -> dict[str, Any]:
    run = read_json(run_dir / "run.json")
    judgments = load_judgments(run_dir)
    metas = load_metas(run_dir)
    pairs = sorted({j["pair"] for j in judgments if j.get("pair")})
    judge_models_path = run_dir / "judge_models.json"
    return {
        "run": run,
        "judge_models": read_json(judge_models_path) if judge_models_path.exists() else None,
        "generated_at": common.iso_now(),
        "n_judgments_total": len(judgments),
        "n_judgments_valid": sum(1 for j in judgments if j.get("ok")),
        "conditions": condition_stats(metas),
        "pairs": {pair: pair_analysis(pair, judgments, metas) for pair in pairs},
    }


# ---------------------------------------------------------------- 報告


def md_table(header: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join(["---"] * len(header)) + "|"]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(lines)


def winrate_row(label: str, s: dict[str, Any]) -> list[str]:
    return [
        label,
        str(s["cells"]),
        f"{s['wins']}/{s['losses']}/{s['ties']}",
        fmt_rate(s["win_rate"]),
        fmt_interval(tuple(s["ci95"]) if s["ci95"] else None),
        fmt_rate(s["win_rate_ties_half"]),
    ]


WINRATE_HEADER = ["分組", "格數", "勝/負/平", "勝率（不含平手）", "Wilson 95% CI", "平手計 0.5"]


def fmt_num(value: float | None, digits: int = 1) -> str:
    return "n/a" if value is None else f"{value:.{digits}f}"


def render_report(data: dict[str, Any]) -> str:
    run = data["run"]
    out: list[str] = []
    add = out.append
    add("# CGU plugin 評估報告")
    add("")
    if run.get("dry_run"):
        add(
            "> ⚠️ **這是 dry-run 的假資料**：答案與評審皆由假後端決定性產生，只用來驗證流程，**不可解讀為任何實驗結果**。"
        )
        add("")
    git = run.get("git") or {}
    add(f"- 產生時間：{data['generated_at']}")
    add(
        f"- Run：`{run.get('run_id')}`（開始 {run.get('started_at')}，結束 {run.get('finished_at', 'n/a')}）"
    )
    add(f"- Repo commit：`{git.get('commit')}`（工作樹有未提交變更：{git.get('dirty')}）")
    add(
        f"- Plugin 目錄雜湊：`{run.get('plugin_tree_sha256')}`；MCP 來源：`{run.get('mcp_source')}`"
    )
    add(
        f"- Copilot CLI：{run.get('copilot_version')}；生成模型：{', '.join(run.get('models', []))}"
    )
    jm = data.get("judge_models") or {}
    resolved = ", ".join(f"{k}→{v}" for k, v in (jm.get("resolved") or {}).items()) or "n/a"
    add(f"- 評審模型（要求→實際）：{resolved}")
    add(
        f"- 題數 {len(run.get('tasks', []))}、重複 {run.get('repeats')}、條件 {', '.join(run.get('conditions', []))}"
    )
    add(f"- 評審紀錄：有效 {data['n_judgments_valid']} / 總計 {data['n_judgments_total']}")
    add("")
    add("## 0. 先讀這裡")
    add("")
    add(
        "- 主要指標是**格子層級**勝率：一格 = (題目, 生成模型, 重複)，其下的評審結果（2 評審 × 2 順序）先合併成一個勝/負/平，再計算 Wilson 95% CI。"
    )
    add("- 「評審層級」的 CI 把同一格的多次判斷當成獨立樣本，**會高估精確度**，只作輔助。")
    add("- 結果只適用於本題庫、本批生成模型、本批 LLM 評審；未經人類評分校準。")
    add("")

    add("## 1. 主要結果")
    add("")
    for p in data["pairs"].values():
        add(f"### {p['baseline']} vs {p['treatment']}")
        add("")
        add(md_table(WINRATE_HEADER, [winrate_row("整體（格子層級）", p["overall"])]))
        jl = p["judgment_level"]
        add("")
        add(
            f"- 評審層級（輔助、偏樂觀）：{jl['wins']}/{jl['losses']}/{jl['ties']}，"
            f"勝率 {fmt_rate(jl['win_rate'])}，CI {fmt_interval(tuple(jl['ci95']) if jl['ci95'] else None)}"
        )
        add(f"- 判讀：{p['verdict']}")
        add("")
    if not data["pairs"]:
        add("沒有有效的評審紀錄。")
        add("")

    for i, p in enumerate(data["pairs"].values(), start=1):
        add(f"## 2.{i} 細分：{p['baseline']} vs {p['treatment']}")
        add("")
        for title, key in (
            ("依生成模型", "by_model"),
            ("依領域", "by_domain"),
            ("依評審", "by_judge"),
        ):
            add(f"**{title}**")
            add("")
            add(md_table(WINRATE_HEADER, [winrate_row(k, v) for k, v in p[key].items()]))
            add("")
        add("**準則別（評審層級，同一格多次判斷彼此相關）**")
        add("")
        rows = []
        for key, label in RUBRIC_LABELS.items():
            c = p["criteria"][key]
            rows.append(
                [
                    label,
                    f"{c['wins']}/{c['losses']}/{c['ties']}",
                    fmt_rate(c["win_rate"]),
                    fmt_interval(tuple(c["ci95"]) if c["ci95"] else None),
                ]
            )
        add(md_table(["準則", "處理組 勝/負/平", "勝率（不含平手）", "Wilson 95% CI"], rows))
        add("")

        oc, pb, ja = p["order_consistency"], p["position_bias"], p["judge_agreement"]
        add(f"## 3.{i} 評審可靠度：{p['baseline']} vs {p['treatment']}")
        add("")
        add(
            f"- 順序一致率（同一評審、兩種 A/B 順序給出同一結論）：{fmt_rate(oc['rate'])}"
            f"（{oc['consistent']}/{oc['pairs_with_both_orders']}），CI {fmt_interval(tuple(oc['ci95']) if oc['ci95'] else None)}"
        )
        add(
            f"- 位置偏誤：決勝判斷中選 A 的比例 {fmt_rate(pb['a_win_rate'])}（n={pb['decisive']}；無位置偏誤應接近 50%）"
        )
        kappa = "n/a" if ja["kappa"] is None else f"{ja['kappa']:.2f}"
        add(f"- 評審間一致率：{fmt_rate(ja['agreement'])}（n={ja['n']}），Cohen's kappa {kappa}")
        for name, s in ja["by_judge_pair"].items():
            k = "n/a" if s["kappa"] is None else f"{s['kappa']:.2f}"
            add(f"  - {name}：一致 {fmt_rate(s['agreement'])}，kappa {k}，n={s['n']}")
        add(
            f"- 評審 JSON 解析重試 {p['parse_retries']} 次；失敗（未取得有效判斷）{p['judgments_failed']} 筆"
        )
        add("")

        ln = p["length"]
        add(f"## 4.{i} 長度偏誤檢查：{p['baseline']} vs {p['treatment']}")
        add("")
        add(
            f"- 處理組 / baseline 答案長度比：平均 {fmt_num(ln['mean_ratio'], 2)}、中位數 {fmt_num(ln['median_ratio'], 2)}（{ln['cells_with_length']} 格）"
        )
        add(
            f"- 「較長者勝」比例：{fmt_rate(ln['longer_wins_rate'])}（{ln['longer_wins']}/{ln['longer_decisive']}），CI {fmt_interval(tuple(ln['longer_wins_ci95']) if ln['longer_wins_ci95'] else None)}"
        )
        lm = ln["length_matched"]
        add(
            f"- 長度相近子集（比值 {ln['length_matched_range'][0]}–{ln['length_matched_range'][1]}）：{lm['cells']} 格，勝率 {fmt_rate(lm['win_rate'])}，CI {fmt_interval(tuple(lm['ci95']) if lm['ci95'] else None)}"
        )
        add(
            f"- 提示：{'**長度可能是混淆因素**，請優先參考長度相近子集' if ln['flag'] else '未觸發長度偏誤提示（不代表沒有偏誤）'}"
        )
        ov = p["overconfidence"]
        add(
            f"- 評審標示的「確定語氣但無法驗證」程度（0–2）：baseline {fmt_num(ov['baseline_mean'], 2)}，處理組 {fmt_num(ov['treatment_mean'], 2)}（n={ov['judgments']}）"
        )
        lk = p["leakage"]
        clean = lk["clean_cells"]
        add(
            f"- 條件洩漏檢查：{lk['judgments_with_redactions']}/{lk['judgments']} 筆判斷的答案含工具/skill 名稱（已遮蔽）；排除這些格子後勝率 {fmt_rate(clean['win_rate'])}（{clean['cells']} 格）"
        )
        add("")

    add("## 5. 條件別：工具使用與成本")
    add("")
    rows = []
    for cond, c in data["conditions"].items():
        rows.append(
            [
                cond,
                f"{c['ok']}/{c['cells']}",
                fmt_rate(c["cgu_connected_rate"], 0),
                fmt_rate(c["any_cgu_call_rate"], 0),
                fmt_num(c["mean_cgu_calls"], 2),
                fmt_rate(c["skill_invoked_rate"], 0),
                fmt_num(c["mean_duration_s"], 0),
                fmt_num(c["mean_input_tokens"], 0),
                fmt_num(c["mean_output_tokens"], 0),
                fmt_num(c["mean_premium_requests"], 1),
                fmt_num(c["mean_answer_chars"], 0),
            ]
        )
    add(
        md_table(
            [
                "條件",
                "成功/總格",
                "cgu 已連線",
                "有呼叫 cgu 工具",
                "平均 cgu 呼叫",
                "觸發 creative-ideation",
                "平均秒數",
                "平均輸入 tokens",
                "平均輸出 tokens",
                "平均 premium requests",
                "平均答案字數",
            ],
            rows,
        )
    )
    add("")
    for cond, c in data["conditions"].items():
        if c["cgu_tool_histogram"]:
            add(f"- `{cond}` 的 cgu 工具使用分布：{c['cgu_tool_histogram']}")
        if c["failure_reasons"]:
            add(f"- `{cond}` 失敗原因：{c['failure_reasons']}")
        if c["warnings"]:
            add(f"- `{cond}` 警告統計：{c['warnings']}")
    add("")
    add(
        "**等預算說明**：本框架保證「同模型、同提示、同 reasoning effort、同逾時」，但**不**強制等 token。plugin 條件會多出 skill 載入與工具往返；請對照上表的 token／秒數／premium requests，不要把「用了更多算力」誤讀為「方法更好」。"
    )
    add("")

    add("## 6. 限制")
    add("")
    for line in (
        "樣本很小：題數有限、通常每格只跑一次；CI 很寬，且重複只增加雜訊估計，不增加題目多樣性。",
        "評審是 LLM：與人類創意評價的相關性未經校準；LLM 評審偏好長答案、條列式、自信語氣，並可能偏好同家族模型的文風。已用雙順序、雙評審、長度比與遮蔽檢查降低（不是消除）這些風險。",
        "匿名化只遮蔽明顯的工具名稱；plugin 答案若帶有特定方法論的行文痕跡（例如固定的框架詞彙），評審仍可能辨識出來。",
        "刻意聚焦中階模型：結果不能外推到更強的模型，也不能外推到未測試的模型家族。",
        "題庫只涵蓋三個領域（醫學研究發想、醫學產品開發、行政流程改造）的 zh-TW 決策型題目；不代表一般創意任務（如 AUT、文學創作）。",
        "事實正確性未逐項查證；評審只被要求懲罰『確定語氣但無法驗證』的主張，這不等於查核過事實。",
        "plugin 條件的結果取決於 plugin 版本、skill 是否被自動觸發、MCP 是否連線；請見第 5 節的觸發率與連線率。",
    ):
        add(f"- {line}")
    add("")
    add("## 7. 這份結果「不能」說明什麼")
    add("")
    for line in (
        "不能說明 plugin 讓答案「更有創意」——只能說在此評審設定下，兩種答案被偏好的相對頻率。",
        "不能說明對真實使用者的價值：沒有人類評分、沒有實際採用或後續成果的追蹤。",
        "不能說明各個 skill／工具各自的貢獻（沒有做消融實驗）；plugin 與 plugin_explicit 的差異只反映『是否明示使用 skill』。",
        "不能說明對更強模型、不同語言、不同領域是否成立。",
        "CI 跨越 50% 時，結論是『無法區分』，不是『沒有效果』；CI 在 50% 之上，也只是此樣本的結果。",
        "不能說明成本效益：plugin 條件通常使用更多 token 與時間，需另行權衡。",
    ):
        add(f"- {line}")
    add("")

    add("## 附錄 A：逐格結果（處理組相對 baseline）")
    add("")
    for p in data["pairs"].values():
        add(f"### {p['baseline']} vs {p['treatment']}")
        add("")
        rows = [
            [
                c["task_id"],
                c["gen_model"],
                str(c["repeat"]),
                c["outcome"],
                fmt_num(c["mean_treatment_score"], 2),
                str(c["judgments"]),
            ]
            for c in p["cells"]
        ]
        add(md_table(["題目", "生成模型", "重複", "結果", "處理組平均得分", "判斷數"], rows))
        add("")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- 主程式


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="彙整評審結果並產生報告")
    p.add_argument("--run-dir", type=Path, required=True)
    p.add_argument("--reports-dir", type=Path, default=common.DEFAULT_REPORTS_DIR)
    p.add_argument("--name", default=None, help="報告檔名（不含副檔名），預設為 UTC 時間戳")
    args = p.parse_args(argv)
    if not (args.run_dir / "run.json").exists():
        print(f"找不到 run.json：{args.run_dir}", file=sys.stderr)
        return 2
    data = aggregate(args.run_dir)
    name = args.name or (("dry-" if data["run"].get("dry_run") else "") + common.utc_stamp())
    args.reports_dir.mkdir(parents=True, exist_ok=True)
    (args.reports_dir / f"{name}.md").write_text(render_report(data), encoding="utf-8")
    write_json(args.reports_dir / f"{name}.json", data)
    print(f"報告：{args.reports_dir / (name + '.md')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
