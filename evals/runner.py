"""產生階段：對每個 (條件, 模型, 題目, 重複) 在隔離環境中呼叫 Copilot CLI 並保存結果。

用法：uv run --no-project python -m evals.runner --help
"""

from __future__ import annotations

import argparse
import concurrent.futures
import copy
import hashlib
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from evals import common
from evals.common import CONDITIONS, REPO_ROOT, condition_prompt, read_json, slug, write_json
from evals.copilot_cli import (
    Backend,
    CliRequest,
    CliResult,
    CopilotBackend,
    FakeBackend,
    ParsedRun,
    default_copilot_bin,
    parse_events,
    parse_otel_usage,
)

SCHEMA_VERSION = 1
MCP_FILENAMES = (".mcp.json", "mcp.json")
CONTAMINATION_MARKERS = (
    ".git",
    ".claude/skills",
    ".github/skills",
    ".github/agents",
    ".github/copilot-instructions.md",
    "AGENTS.md",
    ".mcp.json",
)
_SERVER_KEYS = ("mcpServers", "servers")
_PRINT_LOCK = threading.Lock()


# ---------------------------------------------------------------- plugin 副本與 mcp 改寫


def rewrite_mcp_config(
    config: dict[str, Any] | None,
    *,
    repo_root: Path,
    data_dir: Path,
    uv_no_sync: bool = False,
) -> dict[str, Any]:
    """把 `cgu` server 改成從本機 checkout 啟動，其他 server 條目原樣保留。"""
    cfg = copy.deepcopy(config) if config else {}
    key = next((k for k in _SERVER_KEYS if isinstance(cfg.get(k), dict)), "mcpServers")
    servers = cfg.setdefault(key, {})
    old = servers.get("cgu") if isinstance(servers.get("cgu"), dict) else {}
    drop = {"command", "args", "env", "cwd", "url", "headers"}
    entry = {k: v for k, v in old.items() if k not in drop}
    entry["type"] = "stdio"
    entry["command"] = "uv"
    run_args = ["run", *(["--no-sync"] if uv_no_sync else []), "cgu-server"]
    entry["args"] = ["--directory", str(repo_root), *run_args]
    env = dict(old.get("env") or {})
    env.update(
        {
            "CGU_PROVIDER": "passthrough",
            "CGU_LLM_PROVIDER": "passthrough",
            "CGU_DATA_DIR": str(data_dir),
        }
    )
    entry["env"] = env
    servers["cgu"] = entry
    return cfg


def prepare_plugin(
    source: Path,
    dest: Path,
    *,
    mcp_source: str,
    repo_root: Path,
    data_dir: Path,
    uv_no_sync: bool = False,
    dotfile_shim: bool = True,
) -> dict[str, Any]:
    """複製 plugin 並依 mcp_source 改寫 MCP 設定。

    Copilot CLI 1.0.91 實測可直接讀取 plugin 根目錄的 `mcp.json`（事件 `session.mcp_servers_loaded`
    顯示 source=plugin、status=connected）。`dotfile_shim` 只是給舊版 CLI 的後備：另存 `.mcp.json`。
    每個儲存格仍會解析 `mcp_servers_loaded`，plugin 條件若沒載入 MCP 會被標記，不會悄悄失去工具。
    """
    if not source.is_dir():
        raise FileNotFoundError(f"找不到 plugin 目錄: {source}")
    shutil.copytree(
        source,
        dest,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".git", "node_modules"),
    )
    info: dict[str, Any] = {"source": str(source), "mcp_source": mcp_source, "warnings": []}
    existing = [n for n in MCP_FILENAMES if (dest / n).is_file()]
    if mcp_source == "local":
        if not existing:
            info["warnings"].append("plugin 沒有 MCP 設定檔，已新建 .mcp.json 指向本機 checkout")
            write_json(
                dest / ".mcp.json",
                rewrite_mcp_config(
                    None, repo_root=repo_root, data_dir=data_dir, uv_no_sync=uv_no_sync
                ),
            )
            existing = [".mcp.json"]
        else:
            for name in existing:
                path = dest / name
                write_json(
                    path,
                    rewrite_mcp_config(
                        read_json(path),
                        repo_root=repo_root,
                        data_dir=data_dir,
                        uv_no_sync=uv_no_sync,
                    ),
                )
    elif not existing:
        info["warnings"].append("plugin 沒有 MCP 設定檔（--mcp-source git 時不會代為建立）")
    if dotfile_shim and ".mcp.json" not in existing and "mcp.json" in existing:
        shutil.copyfile(dest / "mcp.json", dest / ".mcp.json")
        info["warnings"].append("plugin 只有 mcp.json；已複製為 .mcp.json 以便 CLI 載入")
    info["mcp_files"] = [n for n in MCP_FILENAMES if (dest / n).is_file()]
    return info


def tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        if "__pycache__" in path.parts or ".git" in path.parts:
            continue
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


# ---------------------------------------------------------------- 儲存格執行


@dataclass
class Cell:
    condition: str
    model: str
    task: dict[str, Any]
    repeat: int

    @property
    def rel_dir(self) -> Path:
        name = common.repeat_dirname(self.task["id"], self.repeat)
        return Path(self.condition) / slug(self.model) / name

    @property
    def label(self) -> str:
        return (
            f"{self.condition}/{self.model}/{common.repeat_dirname(self.task['id'], self.repeat)}"
        )


@dataclass
class RunContext:
    run_dir: Path
    work_root: Path
    backend: Backend
    plugin_source: Path
    mcp_source: str = "local"
    timeout: float = 900.0
    retries: int = 1
    reasoning_effort: str | None = None
    uv_no_sync: bool = False
    dotfile_shim: bool = True
    keep_work: bool = False
    dry_run: bool = False
    resume: bool = False
    repo_root: Path = REPO_ROOT
    extra_args: tuple[str, ...] = ()
    run_id: str = ""


@dataclass
class Attempt:
    result: CliResult
    parsed: ParsedRun
    reason: str | None
    plugin_info: dict[str, Any] | None = None
    files_created: list[dict[str, Any]] = field(default_factory=list)
    usage: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "exit_code": self.result.exit_code,
            "timed_out": self.result.timed_out,
            "duration_s": round(self.result.duration_s, 2),
            "reason": self.reason,
        }


def iter_cells(
    tasks: list[dict[str, Any]], models: list[str], conditions: list[str], repeats: int
) -> list[Cell]:
    """條件相鄰排列，讓同一 (題目, 模型) 的各條件大致在同一時段執行。"""
    return [
        Cell(condition, model, task, repeat)
        for repeat in range(repeats)
        for task in tasks
        for model in models
        for condition in conditions
    ]


def list_files(root: Path, limit: int = 20) -> list[dict[str, Any]]:
    if not root.exists():
        return []
    out = []
    for path in sorted(p for p in root.rglob("*") if p.is_file())[:limit]:
        out.append({"path": path.relative_to(root).as_posix(), "bytes": path.stat().st_size})
    return out


def rmtree_quiet(path: Path) -> None:
    for _ in range(5):
        shutil.rmtree(path, ignore_errors=True)
        if not path.exists():
            return
        time.sleep(0.5)


def execute_attempt(cell: Cell, ctx: RunContext, prompt: str, attempt: int) -> Attempt:
    work = ctx.work_root / f"{slug(cell.label)}-a{attempt}"
    rmtree_quiet(work)
    work.mkdir(parents=True)
    cwd = work / "cwd"
    cwd.mkdir()
    needs_plugin = CONDITIONS[cell.condition]["plugin"]
    plugin_dir: Path | None = None
    plugin_info: dict[str, Any] | None = None
    if needs_plugin:
        if ctx.plugin_source.is_dir():
            plugin_dir = work / "plugin"
            data_dir = work / "cgu-data"
            data_dir.mkdir()
            plugin_info = prepare_plugin(
                ctx.plugin_source,
                plugin_dir,
                mcp_source=ctx.mcp_source,
                repo_root=ctx.repo_root,
                data_dir=data_dir,
                uv_no_sync=ctx.uv_no_sync,
                dotfile_shim=ctx.dotfile_shim,
            )
        elif ctx.dry_run:
            plugin_info = {
                "skipped": "plugin 來源不存在（dry-run）",
                "source": str(ctx.plugin_source),
            }
        else:
            raise FileNotFoundError(f"找不到 plugin 目錄: {ctx.plugin_source}")

    request = CliRequest(
        prompt=prompt,
        model=cell.model,
        cwd=cwd,
        home=work / "home",
        log_dir=work / "logs",
        otel_path=work / "otel" / "otel.jsonl",
        timeout=ctx.timeout,
        plugin_dir=plugin_dir,
        reasoning_effort=ctx.reasoning_effort,
        extra_args=ctx.extra_args,
        tags={
            "role": "generate",
            "condition": cell.condition,
            "task_id": cell.task["id"],
            "repeat": cell.repeat,
        },
    )
    result = ctx.backend(request)
    parsed = parse_events(result.stdout)
    otel = parse_otel_usage(result.otel_text)
    usage: dict[str, Any] = otel.as_dict() if otel else {}
    usage.update(
        {
            "premium_requests": parsed.premium_requests,
            "api_duration_ms": parsed.api_duration_ms,
            "session_duration_ms": parsed.session_duration_ms,
            "model_turns": parsed.model_turns,
        }
    )

    reason: str | None = None
    if result.timed_out:
        reason = "timeout"
    elif result.exit_code != 0:
        reason = f"exit_code_{result.exit_code}"
    elif parsed.exit_code not in (None, 0):
        reason = f"result_exit_code_{parsed.exit_code}"
    elif not parsed.answer:
        reason = "empty_answer"
    elif needs_plugin and plugin_dir is not None and not parsed.cgu_connected:
        reason = "cgu_mcp_not_connected"

    files = list_files(cwd)
    attempt_result = Attempt(result, parsed, reason, plugin_info, files, usage)
    if not ctx.keep_work:
        rmtree_quiet(work)
    return attempt_result


def collect_warnings(cell: Cell, attempt: Attempt, answer: str) -> list[str]:
    parsed = attempt.parsed
    warnings: list[str] = []
    needs_plugin = CONDITIONS[cell.condition]["plugin"]
    allowed_sources = {"builtin", "plugin"} if needs_plugin else {"builtin"}
    foreign = sorted(
        {s["name"] for s in parsed.skills_loaded if s["source"] not in allowed_sources}
    )
    if foreign:
        warnings.append(f"unexpected_skills_loaded:{','.join(foreign)}")
    foreign_mcp = sorted(
        name
        for name, info in parsed.mcp_servers.items()
        if info.get("status") == "connected"
        and info.get("source") != "builtin"
        and not (needs_plugin and name == "cgu")
    )
    if foreign_mcp:
        warnings.append(f"unexpected_mcp_servers_connected:{','.join(foreign_mcp)}")
    if needs_plugin and attempt.plugin_info and not parsed.cgu_tools_available:
        warnings.append("cgu_tools_not_listed_in_usage_checkpoint")
    if attempt.files_created and len(answer) < 400:
        warnings.append("short_answer_with_files_created")
    if not attempt.usage.get("input_tokens"):
        warnings.append("no_otel_token_usage")
    if parsed.bad_lines:
        warnings.append(f"unparsable_event_lines:{parsed.bad_lines}")
    if attempt.plugin_info:
        warnings.extend(attempt.plugin_info.get("warnings", []))
    return warnings


def run_cell(cell: Cell, ctx: RunContext) -> dict[str, Any]:
    cell_dir = ctx.run_dir / cell.rel_dir
    meta_path = cell_dir / "meta.json"
    if ctx.resume and meta_path.exists():
        previous = read_json(meta_path)
        if previous.get("status") == "ok":
            previous["skipped_resume"] = True
            return previous
    cell_dir.mkdir(parents=True, exist_ok=True)
    prompt = condition_prompt(cell.task, cell.condition)
    base = common.base_prompt(cell.task)
    (cell_dir / "prompt.txt").write_text(prompt, encoding="utf-8")

    history: list[dict[str, Any]] = []
    last: Attempt | None = None
    error: str | None = None
    for attempt_no in range(ctx.retries + 1):
        try:
            last = execute_attempt(cell, ctx, prompt, attempt_no)
        except FileNotFoundError as exc:
            error = str(exc)
            history.append({"reason": "plugin_source_missing"})
            break
        history.append(last.summary())
        if last.reason is None:
            break

    meta: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "run_id": ctx.run_id,
        "condition": cell.condition,
        "model": cell.model,
        "task_id": cell.task["id"],
        "domain": cell.task["domain"],
        "repeat": cell.repeat,
        "prompt_sha256": common.sha256_text(prompt),
        "base_prompt_sha256": common.sha256_text(base),
        "dry_run": ctx.dry_run,
        "attempts": len(history),
        "attempt_history": history,
        "total_duration_s": round(sum(h.get("duration_s", 0.0) for h in history), 2),
    }
    if last is None:
        meta.update(status="failed", failure_reason="plugin_source_missing", error=error)
        write_json(meta_path, meta)
        return meta

    parsed = last.parsed
    (cell_dir / "events.jsonl").write_text(last.result.stdout, encoding="utf-8")
    if last.result.stderr.strip():
        (cell_dir / "stderr.txt").write_text(last.result.stderr, encoding="utf-8")
    if last.result.otel_text:
        (cell_dir / "otel.jsonl").write_text(last.result.otel_text, encoding="utf-8")

    ok = last.reason is None
    answer = parsed.answer if ok else ""
    if ok:
        (cell_dir / "answer.md").write_text(answer + "\n", encoding="utf-8")
    meta.update(
        status="ok" if ok else "failed",
        failure_reason=last.reason,
        exit_code=last.result.exit_code,
        timed_out=last.result.timed_out,
        duration_s=round(last.result.duration_s, 2),
        answer_chars=len(answer),
        tool_calls_total=len(parsed.tool_calls),
        cgu_tool_calls=len(parsed.cgu_calls),
        cgu_tools=parsed.cgu_tool_counts,
        skills_invoked=parsed.skills_invoked,
        skills_loaded=parsed.skills_loaded,
        mcp_servers=parsed.mcp_servers,
        cgu_connected=parsed.cgu_connected,
        cgu_tools_available=parsed.cgu_tools_available,
        usage=last.usage,
        files_created=last.files_created,
        warnings=collect_warnings(cell, last, answer),
        plugin=last.plugin_info,
    )
    write_json(meta_path, meta)
    return meta


# ---------------------------------------------------------------- 主程式


def git_info(repo_root: Path) -> dict[str, Any]:
    def run(*args: str) -> str | None:
        try:
            proc = subprocess.run(
                ["git", "-C", str(repo_root), *args],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        return proc.stdout.strip() if proc.returncode == 0 else None

    status = run("status", "--porcelain")
    return {
        "commit": run("rev-parse", "HEAD"),
        "dirty": bool(status) if status is not None else None,
    }


def preflight_warnings(work_root: Path) -> list[str]:
    warnings = []
    home = Path.home()
    for rel in (".claude/skills", ".agents/skills"):
        if (home / rel).is_dir():
            warnings.append(
                f"使用者目錄存在 ~/{rel}，可能被 CLI 當作個人 skill 載入，污染 baseline"
            )
    for parent in [work_root, *work_root.parents]:
        for rel in CONTAMINATION_MARKERS:
            if (parent / rel).exists():
                warnings.append(f"工作目錄上層 {parent} 含 {rel}，可能被 CLI 當作專案設定載入")
                break
    return warnings


def check_local_mcp(
    repo_root: Path,
    data_dir: Path,
    *,
    uv_no_sync: bool = False,
    timeout: float = 180.0,
    run: Callable[..., Any] = subprocess.run,
) -> tuple[bool, str]:
    """以 stdin 關閉的方式啟動一次本機 cgu-server，提早發現 import 失敗或 uv 同步失敗。"""
    cmd = ["uv", "--directory", str(repo_root), "run", *(["--no-sync"] if uv_no_sync else [])]
    cmd.append("cgu-server")
    env = {
        **os.environ,
        "CGU_PROVIDER": "passthrough",
        "CGU_LLM_PROVIDER": "passthrough",
        "CGU_DATA_DIR": str(data_dir),
    }
    try:
        proc = run(
            cmd,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=env,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return True, "server 在 stdin 關閉後仍在執行，視為可啟動"
    except OSError as exc:
        return False, f"無法執行 uv: {exc}"
    stderr = (proc.stderr or "").strip()
    if proc.returncode != 0 and re.search(r"Traceback|error:|Error", stderr):
        return False, f"exit={proc.returncode}: {stderr[-600:]}"
    return True, f"exit={proc.returncode}"


def is_inside(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="執行 baseline / plugin 條件的產生階段")
    p.add_argument("--suite", type=Path, default=common.DEFAULT_SUITE)
    p.add_argument("--conditions", default=",".join(common.DEFAULT_CONDITIONS))
    p.add_argument("--models", default=",".join(common.DEFAULT_GEN_MODELS))
    p.add_argument("--tasks", default="all", help="逗號分隔的題目 id，或 all")
    p.add_argument("--domains", default=None, help="逗號分隔的領域過濾")
    p.add_argument("--repeats", type=int, default=1)
    p.add_argument("--jobs", type=int, default=3)
    p.add_argument("--timeout", type=float, default=900.0, help="每次 CLI 呼叫的逾時秒數")
    p.add_argument("--retries", type=int, default=1, help="暫時性失敗的重試次數")
    p.add_argument("--reasoning-effort", default=None)
    p.add_argument("--plugin-source", type=Path, default=common.DEFAULT_PLUGIN_SOURCE)
    p.add_argument("--mcp-source", choices=("local", "git"), default="local")
    p.add_argument("--uv-no-sync", action="store_true", help="本機 MCP 以 uv run --no-sync 啟動")
    p.add_argument("--skip-mcp-check", action="store_true", help="略過本機 cgu-server 啟動預檢")
    p.add_argument(
        "--mcp-dotfile-shim",
        action="store_true",
        help="另存 .mcp.json 副本（僅供舊版 CLI；1.0.91 已實測可直接讀 plugin 根目錄 mcp.json）",
    )
    p.add_argument("--out-root", type=Path, default=common.DEFAULT_RUNS_DIR)
    p.add_argument("--run-id", default=None)
    p.add_argument("--resume", type=Path, default=None, help="沿用既有 run 目錄，略過已成功的格子")
    p.add_argument("--work-root", type=Path, default=None)
    p.add_argument("--keep-work", action="store_true")
    p.add_argument("--limit", type=int, default=None, help="只跑前 N 格（煙霧測試）")
    p.add_argument("--copilot-bin", default=None)
    p.add_argument("--extra-copilot-arg", action="append", default=[])
    p.add_argument("--dry-run", action="store_true", help="使用假後端，不連網、不呼叫 CLI")
    return p


def main(argv: list[str] | None = None, backend: Backend | None = None) -> int:
    args = build_parser().parse_args(argv)
    conditions = common.split_csv(args.conditions)
    unknown = [c for c in conditions if c not in CONDITIONS]
    if unknown:
        print(f"未知條件: {unknown}；可用: {sorted(CONDITIONS)}", file=sys.stderr)
        return 2
    models = common.split_csv(args.models)
    tasks = common.select_tasks(common.load_suite(args.suite), args.tasks, args.domains)
    if not tasks:
        print("沒有符合的題目", file=sys.stderr)
        return 2

    run_id = args.run_id or ((args.resume.name) if args.resume else None)
    run_id = run_id or (("dry-" if args.dry_run else "") + common.utc_stamp())
    run_dir = args.resume or (args.out_root / run_id)
    work_root = args.work_root or (Path(tempfile.gettempdir()) / f"cgu-evals-{run_id}")
    if is_inside(work_root, REPO_ROOT):
        print(
            "work-root 不可位於 repo 內：CLI 會載入 repo 的 .claude/skills 與 AGENTS.md，污染 baseline",
            file=sys.stderr,
        )
        return 2
    needs_plugin = any(CONDITIONS[c]["plugin"] for c in conditions)
    if needs_plugin and not args.dry_run and not args.plugin_source.is_dir():
        print(f"找不到 plugin 目錄: {args.plugin_source}", file=sys.stderr)
        return 2

    if backend is None:
        backend = FakeBackend() if args.dry_run else CopilotBackend(args.copilot_bin)
    cells = iter_cells(tasks, models, conditions, args.repeats)
    if args.limit:
        cells = cells[: args.limit]

    ctx = RunContext(
        run_dir=run_dir,
        work_root=work_root,
        backend=backend,
        plugin_source=args.plugin_source,
        mcp_source=args.mcp_source,
        timeout=args.timeout,
        retries=args.retries,
        reasoning_effort=args.reasoning_effort,
        uv_no_sync=args.uv_no_sync,
        dotfile_shim=args.mcp_dotfile_shim,
        keep_work=args.keep_work,
        dry_run=args.dry_run,
        resume=args.resume is not None,
        extra_args=tuple(args.extra_copilot_arg),
        run_id=run_id,
    )
    work_root.mkdir(parents=True, exist_ok=True)

    if needs_plugin and args.mcp_source == "local" and not args.dry_run and not args.skip_mcp_check:
        check_dir = work_root / "mcp-check"
        check_dir.mkdir(parents=True, exist_ok=True)
        healthy, detail = check_local_mcp(REPO_ROOT, check_dir, uv_no_sync=args.uv_no_sync)
        print(
            f"本機 cgu-server 預檢：{'通過' if healthy else '失敗'}（{detail[:200]}）", flush=True
        )
        if not healthy:
            print(
                "本機 cgu-server 無法啟動，plugin 條件的 MCP 會連線失敗；請先修復環境，"
                "或加 --uv-no-sync、--skip-mcp-check、--mcp-source git。\n" + detail,
                file=sys.stderr,
            )
            rmtree_quiet(work_root)
            return 2
    run_dir.mkdir(parents=True, exist_ok=True)
    warnings = [] if args.dry_run else preflight_warnings(work_root)
    plugin_hash = (
        tree_sha256(args.plugin_source) if needs_plugin and args.plugin_source.is_dir() else None
    )
    config = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "started_at": common.iso_now(),
        "dry_run": args.dry_run,
        "suite": str(args.suite),
        "tasks": [t["id"] for t in tasks],
        "conditions": conditions,
        "models": models,
        "repeats": args.repeats,
        "mcp_source": args.mcp_source,
        "timeout": args.timeout,
        "retries": args.retries,
        "reasoning_effort": args.reasoning_effort,
        "plugin_source": str(args.plugin_source),
        "plugin_tree_sha256": plugin_hash,
        "git": git_info(REPO_ROOT),
        "copilot_version": backend.version() if isinstance(backend, CopilotBackend) else "fake",
        "copilot_bin": args.copilot_bin or default_copilot_bin(),
        "python": platform.python_version(),
        "cells_planned": len(cells),
        "preflight_warnings": warnings,
    }
    write_json(run_dir / "run.json", config)
    for w in warnings:
        print(f"[警告] {w}", file=sys.stderr)
    print(f"run: {run_dir}  cells: {len(cells)}  jobs: {args.jobs}", flush=True)

    results: list[dict[str, Any]] = []
    done = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        futures = {pool.submit(run_cell, cell, ctx): cell for cell in cells}
        for future in concurrent.futures.as_completed(futures):
            cell = futures[future]
            done += 1
            try:
                meta = future.result()
            except Exception as exc:  # 單格失敗不應中斷整批
                meta = {"status": "failed", "failure_reason": f"runner_error:{exc!r}"}
            results.append({**meta, "label": cell.label})
            with _PRINT_LOCK:
                print(
                    f"[{done}/{len(cells)}] {cell.label} -> {meta.get('status')}"
                    f" ({meta.get('failure_reason') or 'ok'}, {meta.get('duration_s', '?')}s)",
                    flush=True,
                )

    failed = [r for r in results if r.get("status") != "ok"]
    config.update(
        finished_at=common.iso_now(),
        cells_ok=len(results) - len(failed),
        cells_failed=len(failed),
        failed=[{"label": r["label"], "reason": r.get("failure_reason")} for r in failed],
    )
    write_json(run_dir / "run.json", config)
    if not args.keep_work:
        rmtree_quiet(work_root)
    print(f"完成：成功 {config['cells_ok']}，失敗 {config['cells_failed']}  -> {run_dir}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
