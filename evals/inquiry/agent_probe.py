"""Real-agent probe for the inquiry memory: isolated Copilot CLI, local plugin copy, pre-populated memory.

It answers three concrete questions with real model calls (not a statistical experiment):
  mining   - does inquiry-mining run end to end, and does the answer match the planted structure?
  implicit - does the skill trigger without being named?
  ideation - with memory on, does creative-ideation use the user's history and avoid the idea the user
             already abandoned (H11)? The same prompt runs against an empty memory as the control.

    uv run --no-sync python -m evals.inquiry.agent_probe --corpus <corpus.json> --copilot-bin <copilot.cmd>
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from mcp import Client

from cgu.infrastructure.config import Settings
from cgu.interfaces.mcp.server import create_server
from evals.copilot_cli import parse_events
from evals.inquiry.run_eval import TZ_SUFFIX, Runner, prepare_sessions
from evals.runner import rewrite_mcp_config

REPO = Path(__file__).resolve().parents[2]
PLUGIN = REPO / "plugins" / "cgu"
MODELS = ("claude-sonnet-5.5", "gpt-6-luna")
PROMPTS = {
    "mining": "請使用 inquiry-mining skill：我最近都在問什麼？有哪些可以當成創意來源？",
    "implicit": "我最近問的問題是不是一直卡在同一件事？幫我回頭看看我自己問過什麼，找出可以突破的地方。",
    "ideation": (
        "請使用 creative-ideation skill。我想做一個用手機追蹤術後病人疼痛恢復的研究，"
        "沒有研究助理、只有既有病歷資料，請幫我發想 2 個不同的切入點。"
    ),
}
ABANDONED_MARKERS = ("穿戴", "AI 預測")


async def populate(data_dir: Path, corpus: dict[str, Any]) -> None:
    """Fill the memory (sessions, ideas, feedback, captured questions) like a user's past months."""
    settings = Settings(
        data_dir=data_dir,
        provider="passthrough",
        embedding="ngram",
        network=False,
        log_level="WARNING",
    )
    async with Client(create_server(settings), mode="2026-07-28") as client:
        runner = Runner(client)
        await runner.call(
            action="settings",
            enable=True,
            consent={"granted": True, "note": "agent probe; synthetic questions"},
        )
        sessions = await prepare_sessions(runner, corpus["sessions"])
        for item in sorted(corpus["items"], key=lambda i: i["at"]):
            args: dict[str, Any] = {
                "action": "capture",
                "text": item["text"],
                "project": "heldout",
                "source": "import",
                "occurred_at": item["at"] + TZ_SUFFIX,
            }
            if item.get("s"):
                args["session_id"] = sessions[item["s"]]
            await runner.call(**args)


def build_profile(work: Path, data_dir: Path, venv: str) -> tuple[Path, dict[str, str]]:
    home = work / "home"
    home.mkdir(parents=True)
    plugin = work / "plugin"
    shutil.copytree(PLUGIN, plugin, ignore=shutil.ignore_patterns("__pycache__"))
    config = json.loads((plugin / "mcp.json").read_text(encoding="utf-8"))
    config = rewrite_mcp_config(config, repo_root=REPO, data_dir=data_dir, uv_no_sync=True)
    env = config["mcpServers"]["cgu"]["env"]
    env.update(
        {
            "UV_PROJECT_ENVIRONMENT": venv,
            "CGU_EMBEDDING": "ngram",
            "CGU_NETWORK": "off",
            "PYTHONUTF8": "1",
        }
    )
    (plugin / "mcp.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    token = subprocess.run(
        ["gh", "auth", "token"], capture_output=True, text=True, check=True
    ).stdout
    env_vars = {**os.environ, "COPILOT_HOME": str(home), "COPILOT_GITHUB_TOKEN": token.strip()}
    return plugin, env_vars


def run_copilot(binary: str, prompt: str, model: str, cwd: Path, env: dict[str, str]) -> str:
    result = subprocess.run(
        [
            binary,
            "-p",
            prompt,
            "--model",
            model,
            "-s",
            "--allow-all-tools",
            "--no-ask-user",
            "--disable-builtin-mcps",
            "--output-format",
            "json",
        ],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=1200,
    )
    return result.stdout


def summarize(stdout: str) -> dict[str, Any]:
    run = parse_events(stdout)
    errors = 0
    for call in run.tool_calls:
        if call.get("success") is False:
            errors += 1
    return {
        "skills": run.skills_invoked,
        "cgu_calls": dict(run.cgu_tool_counts),
        "cgu_connected": run.cgu_connected,
        "tool_errors": errors,
        "answer": run.answer,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--copilot-bin", required=True)
    parser.add_argument("--venv", required=True, help="UV_PROJECT_ENVIRONMENT of a synced dev env")
    parser.add_argument("--out", default="evals/reports/inquiry-agent-probe.json")
    parser.add_argument("--models", default=",".join(MODELS))
    parser.add_argument("--only", default=None, help="comma list of prompt names")
    args = parser.parse_args(argv)
    corpus = json.loads(Path(args.corpus).read_text(encoding="utf-8"))
    wanted = args.only.split(",") if args.only else list(PROMPTS)
    report: dict[str, Any] = {"runs": []}
    for model in args.models.split(","):
        for memory in (True, False):
            for name in wanted:
                if not memory and name != "ideation":
                    continue
                with tempfile.TemporaryDirectory(prefix="cgu-probe-") as tmp:
                    work = Path(tmp)
                    data_dir = work / "data"
                    data_dir.mkdir()
                    if memory:
                        asyncio.run(populate(data_dir, corpus))
                    plugin, env = build_profile(work, data_dir, args.venv)
                    subprocess.run(
                        [args.copilot_bin, "plugin", "install", str(plugin)],
                        env=env,
                        capture_output=True,
                        check=True,
                    )
                    cwd = work / "cwd"
                    cwd.mkdir()
                    stdout = run_copilot(args.copilot_bin, PROMPTS[name], model, cwd, env)
                    summary = summarize(stdout)
                    summary.update(model=model, prompt=name, memory=memory)
                    answer = summary["answer"]
                    summary["mentions_abandoned_idea"] = all(m in answer for m in ABANDONED_MARKERS)
                    report["runs"].append(summary)
                    print(
                        f"{model:<18} {name:<9} memory={memory!s:<5} skills={summary['skills']} "
                        f"cgu={sum(summary['cgu_calls'].values())} errors={summary['tool_errors']}"
                    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"report -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
