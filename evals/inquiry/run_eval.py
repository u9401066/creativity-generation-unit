"""H13 evaluation of the inquiry memory on a held-out corpus with planted structure.

The corpus (questions + ground truth) is written independently of the implementation and tuning data.
Ground-truth labels are used only for scoring; they are never sent to the server.

    uv run --no-sync python -m evals.inquiry.run_eval --corpus <corpus.json> --out evals/reports/inquiry-eval.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mcp import Client

from cgu.infrastructure.config import Settings
from cgu.interfaces.mcp.server import create_server
from evals.inquiry.scoring import (
    adjusted_rand_index,
    majority_label,
    precision_at_k,
    theme_recall,
    top_labels,
)

TZ_SUFFIX = ":00+08:00"
ROW_KEYS = ("inquiries", "items", "rows", "questions")
MEASUREMENT_KEYS = {"value", "method", "reference", "calibrated", "n"}


def norm_time(value: str) -> str:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.astimezone(UTC).strftime("%Y-%m-%dT%H:%M")


def corpus_time(at: str) -> str:
    return norm_time(at + TZ_SUFFIX)


def rows_of(data: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ROW_KEYS:
        value = data.get(key)
        if isinstance(value, list):
            return [row for row in value if isinstance(row, dict)]
    return []


def stray_floats(obj: Any, path: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(obj, float):
        found.append(path)
    elif isinstance(obj, dict):
        is_measurement = set(obj) == MEASUREMENT_KEYS
        for key, value in obj.items():
            if is_measurement and key == "value":
                continue
            found.extend(stray_floats(value, f"{path}.{key}"))
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            found.extend(stray_floats(value, f"{path}[{index}]"))
    return found


class Runner:
    def __init__(self, client: Client) -> None:
        self.client = client

    async def call(self, **arguments: Any) -> dict[str, Any]:
        result = await self.client.call_tool("cgu_inquiry", arguments)
        if result.is_error or result.structured_content is None:
            raise RuntimeError(f"tool error: {result.content}")
        data: dict[str, Any] = result.structured_content
        return data

    async def other(self, tool: str, **arguments: Any) -> dict[str, Any]:
        result = await self.client.call_tool(tool, arguments)
        if result.is_error or result.structured_content is None:
            raise RuntimeError(f"tool error: {tool} {result.content}")
        data: dict[str, Any] = result.structured_content
        return data


async def prepare_sessions(runner: Runner, sessions: dict[str, Any]) -> dict[str, str]:
    ids: dict[str, str] = {}
    for label, spec in sessions.items():
        opened = await runner.other(
            "cgu_session", action="open", topic=spec["topic"], domain=spec.get("domain")
        )
        session_id = str(opened["data"]["session_id"])
        ids[label] = session_id
        added = await runner.other(
            "cgu_ideas",
            action="add",
            session_id=session_id,
            ideas=[{"text": i["text"], "kind": i["kind"]} for i in spec["ideas"]],
        )
        for idea, view in zip(spec["ideas"], added["data"]["ideas"], strict=True):
            await runner.other(
                "cgu_feedback",
                action="record",
                session_id=session_id,
                idea_id=view["idea_id"],
                decision=idea["decision"],
            )
    return ids


def evidence_labels(source: dict[str, Any], by_id: dict[str, str]) -> list[str]:
    labels = []
    for ev in source.get("evidence", []):
        corpus_id = by_id.get(str(ev.get("inquiry_id")))
        if corpus_id:
            labels.append(corpus_id.split("-")[0])
    return labels


def find_number(obj: Any, key: str) -> int | None:
    if isinstance(obj, dict):
        if key in obj and isinstance(obj[key], int):
            return int(obj[key])
        for value in obj.values():
            found = find_number(value, key)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for value in obj:
            found = find_number(value, key)
            if found is not None:
                return found
    return None


def max_measurement(obj: Any) -> float:
    best = 0.0
    if isinstance(obj, dict):
        if set(obj) == MEASUREMENT_KEYS:
            return float(obj["value"])
        for value in obj.values():
            best = max(best, max_measurement(value))
    elif isinstance(obj, list):
        for value in obj:
            best = max(best, max_measurement(value))
    return best


async def run_once(corpus: dict[str, Any], size: int, workdir: Path) -> dict[str, Any]:
    items = sorted(corpus["items"], key=lambda item: item["at"])[:size]
    planted = corpus["planted"]
    settings = Settings(
        data_dir=workdir,
        provider="passthrough",
        embedding="ngram",
        network=False,
        log_level="WARNING",
    )
    server = create_server(settings)
    out: dict[str, Any] = {"size": len(items), "problems": []}
    async with Client(server, mode="2026-07-28") as client:
        runner = Runner(client)
        enable = await runner.call(
            action="settings",
            enable=True,
            consent={"granted": True, "note": "evaluation corpus; synthetic questions"},
        )
        out["enabled"] = bool(enable["data"].get("enabled"))
        session_ids = await prepare_sessions(runner, corpus["sessions"])

        captured = 0
        for item in items:
            args: dict[str, Any] = {
                "action": "capture",
                "text": item["text"],
                "project": "heldout",
                "source": "import",
                "occurred_at": item["at"] + TZ_SUFFIX,
            }
            if item.get("s"):
                args["session_id"] = session_ids[item["s"]]
            result = await runner.call(**args)
            captured += int(bool(result["data"].get("recorded")))
        out["captured"] = captured

        exported = rows_of((await runner.call(action="export"))["data"])
        time_to_corpus = {corpus_time(i["at"]): i["id"] for i in items}
        by_id: dict[str, str] = {}
        for row in exported:
            corpus_id = time_to_corpus.get(norm_time(str(row.get("occurred_at"))))
            if corpus_id:
                by_id[str(row["id"])] = corpus_id
        if len(by_id) != len(items):
            out["problems"].append(f"mapped {len(by_id)} of {len(items)} exported rows")

        started = time.perf_counter()
        themes_result = await runner.call(action="themes", min_size=3)
        out["themes_seconds"] = round(time.perf_counter() - started, 3)
        themes = themes_result["data"].get("themes", [])
        out["embedding"] = themes_result["data"].get("embedding")
        clusters: dict[str, set[str]] = {}
        for theme in themes:
            members = rows_of(
                (await runner.call(action="list", theme_id=theme["theme_id"], limit=500))["data"]
            )
            clusters[theme["theme_id"]] = {
                by_id[str(m["id"])] for m in members if str(m["id"]) in by_id
            }
        truth = {i["id"]: i["t"] for i in items}
        predicted: dict[str, str] = {}
        for theme_id, members in clusters.items():
            for member in members:
                predicted[member] = theme_id
        ids = [i["id"] for i in items]
        pred_labels = [predicted.get(i, f"u-{i}") for i in ids]
        true_labels = [truth[i] if truth[i] != "N" else f"N-{i}" for i in ids]
        out["themes"] = len(themes)
        out["ari_all"] = round(adjusted_rand_index(true_labels, pred_labels), 3)
        non_noise = [k for k, i in enumerate(ids) if truth[i] != "N"]
        out["ari_excluding_noise"] = round(
            adjusted_rand_index(
                [true_labels[k] for k in non_noise], [pred_labels[k] for k in non_noise]
            ),
            3,
        )
        out["theme_recall"] = {
            k: round(v, 3)
            for k, v in sorted(
                theme_recall({i: truth[i] for i in ids if truth[i] != "N"}, clusters).items()
            )
        }

        started = time.perf_counter()
        mined = await runner.call(action="mine", limit=5)
        out["mine_seconds"] = round(time.perf_counter() - started, 3)
        sources = mined["data"].get("sources", [])
        out["mine_warnings"] = mined["provenance"].get("warnings", [])
        out["source_counts"] = {
            kind: sum(1 for s in sources if s.get("kind") == kind)
            for kind in ("frame", "bridge", "stalled", "dormant")
        }
        out["stray_floats"] = stray_floats(mined) + stray_floats(themes_result)

        # frame habit
        habit = planted["frame_habit"]
        frame_hits = []
        for s in sources:
            if s.get("kind") != "frame":
                continue
            labels = evidence_labels(s, by_id)
            blob = json.dumps(s, ensure_ascii=False)
            frame_hits.append(
                {
                    "majority_theme": majority_label(labels),
                    "mentions_stem": habit["stem"] in blob,
                    "max_share_pct": round(max_measurement(s.get("measures", {})) * 100),
                }
            )
        out["frame"] = {
            "candidates": frame_hits,
            "habit_found": any(
                h["majority_theme"] == habit["theme"]
                and h["mentions_stem"]
                and h["max_share_pct"] >= habit["min_share_pct"]
                for h in frame_hits
            ),
        }

        # stalled
        stalled_cfg = planted["stalled"]
        stalled = []
        for s in sources:
            if s.get("kind") != "stalled":
                continue
            stalled.append(
                {
                    "majority_theme": majority_label(evidence_labels(s, by_id)),
                    "has_evidence_quality": "evidence_quality" in json.dumps(s, ensure_ascii=False),
                }
            )
        flagged = {s["majority_theme"] for s in stalled}
        out["stalled"] = {
            "flagged": sorted(str(f) for f in flagged),
            "expected_found": all(e in flagged for e in stalled_cfg["expected"])
            if any(i["t"] in stalled_cfg["expected"] for i in items) and len(items) >= 60
            else None,
            "false_positives": sorted(str(f) for f in flagged if f in stalled_cfg["not_expected"]),
            "all_carry_evidence_quality": all(s["has_evidence_quality"] for s in stalled),
        }

        # bridge
        pair = set(planted["bridge"]["pair"])
        bridges = []
        for s in sources:
            if s.get("kind") != "bridge":
                continue
            labels = evidence_labels(s, by_id)
            bridges.append(
                {
                    "themes": top_labels(labels, 2),
                    "co_occurrence": find_number(s, "co_occurrence"),
                }
            )
        planted_rank = next(
            (r + 1 for r, b in enumerate(bridges) if set(b["themes"]) == pair), None
        )
        out["bridge"] = {
            "candidates": bridges,
            "planted_rank": planted_rank,
            "precision_at_3": precision_at_k([(b["co_occurrence"] or 0) >= 2 for b in bridges], 3),
        }

        # dormant
        dormant_cfg = planted["dormant"]
        blob = json.dumps([s for s in sources if s.get("kind") == "dormant"], ensure_ascii=False)
        out["dormant"] = {
            "expected_found": dormant_cfg["expected_idea"][:12] in blob,
            "decoy_flagged": dormant_cfg["decoy_idea"][:12] in blob,
        }

        # recurrence
        family = {str(r["id"]): r.get("family_id") for r in exported}
        by_corpus = {v: k for k, v in by_id.items()}
        verbatim = [by_corpus[c] for c in planted["recurrence"]["verbatim"] if c in by_corpus]
        near = [by_corpus[c] for c in planted["recurrence"]["near"] if c in by_corpus]
        out["recurrence"] = {
            "verbatim_same_family": len({family[i] for i in verbatim}) == 1 if verbatim else None,
            "near_in_same_family": bool(
                verbatim and near and family[near[0]] == family[verbatim[0]]
            ),
        }

        # privacy
        dump = json.dumps(exported, ensure_ascii=False)
        leaked = [f for f in planted["privacy"]["forbidden"] if f in dump]
        out["privacy"] = {
            "leaked": leaked,
            "rows_with_redactions": sum(1 for r in exported if r.get("redactions")),
            "expected_redacted_rows": len(
                [c for c in planted["privacy"]["item_ids"] if c in time_to_corpus.values()]
            ),
        }

        # related
        probe = planted["related_probe"]
        related = await runner.call(action="related", query=probe["query"], k=5)
        similar = rows_of({"items": related["data"].get("similar_inquiries", [])})
        top3 = [by_id.get(str(r.get("id")), "").split("-")[0] for r in similar[:3]]
        adopted_blob = json.dumps(related["data"].get("adopted_ideas", []), ensure_ascii=False)
        out["related"] = {
            "top3_themes": top3,
            "adopted_idea_found": probe["expect_adopted_idea"][:10] in adopted_blob,
        }

        settings_view = (await runner.call(action="settings"))["data"]
        out["coverage"] = settings_view.get("coverage")
        out["funnel"] = settings_view.get("funnel")
    return out


async def main_async(args: argparse.Namespace) -> int:
    corpus = json.loads(Path(args.corpus).read_text(encoding="utf-8"))
    total = len(corpus["items"])
    sizes = [min(int(s), total) for s in args.sizes.split(",")]
    results = []
    for size in sizes:
        with tempfile.TemporaryDirectory(prefix="cgu-inquiry-eval-") as tmp:
            results.append(await run_once(corpus, size, Path(tmp)))
    report = {
        "corpus": Path(args.corpus).name,
        "items": total,
        "embedding_mode": "ngram (lexical, semantic=false)",
        "runs": results,
        "note": "synthetic, held-out, uncalibrated defaults; see docs/inquiry-memory-design.md section 2",
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for r in results:
        print(
            f"n={r['size']:>3}  themes={r['themes']}  ARI(all)={r['ari_all']}  "
            f"ARI(no-noise)={r['ari_excluding_noise']}  sources={r['source_counts']}  "
            f"problems={len(r['problems'])}"
        )
    print(f"report -> {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--sizes", default="20,40,80,117")
    parser.add_argument("--out", default="evals/reports/inquiry-eval.json")
    return asyncio.run(main_async(parser.parse_args(argv)))


if __name__ == "__main__":
    raise SystemExit(main())
