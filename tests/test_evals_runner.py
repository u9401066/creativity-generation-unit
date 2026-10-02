"""evals.runner：條件、提示一致性、mcp.json 改寫、dry-run 流程、重試與續跑。"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest
from test_evals_support import REPO_ROOT, read_fixture

from evals import common, runner
from evals.copilot_cli import (
    CliRequest,
    CliResult,
    FakeBackend,
    build_args,
    default_copilot_bin,
    resolve_command,
)

SHIPPED_MCP = {
    "$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
    "mcpServers": {
        "cgu": {
            "type": "stdio",
            "command": "uvx",
            "args": ["--from", "git+https://example.invalid/cgu@master", "cgu-server"],
            "env": {"CGU_PROVIDER": "passthrough", "CGU_DATA_DIR": "${PLUGIN_DATA}/cgu"},
            "tools": ["*"],
        },
        "other": {"type": "stdio", "command": "keep-me", "args": []},
    },
}


@pytest.fixture
def plugin_src(tmp_path: Path) -> Path:
    src = tmp_path / "plugin-src"
    (src / "skills" / "creative-ideation").mkdir(parents=True)
    (src / "skills" / "creative-ideation" / "SKILL.md").write_text("---\nname: x\n---\n", "utf-8")
    (src / "plugin.json").write_text('{"name": "cgu", "version": "0.0.0"}', "utf-8")
    (src / "mcp.json").write_text(json.dumps(SHIPPED_MCP), "utf-8")
    (src / "__pycache__").mkdir()
    (src / "__pycache__" / "x.pyc").write_bytes(b"0")
    return src


# ---------------------------------------------------------------- 題庫與條件


def test_suite_shape() -> None:
    tasks = common.load_suite(common.DEFAULT_SUITE)
    assert len(tasks) == 6
    domains: dict[str, int] = {}
    for task in tasks:
        domains[task["domain"]] = domains.get(task["domain"], 0) + 1
        assert task["prompt"].strip()
        assert any("\u4e00" <= ch <= "\u9fff" for ch in task["prompt"])
    assert domains == {"medical_research": 2, "medical_product": 2, "admin_process": 2}
    assert len({t["id"] for t in tasks}) == 6


def test_prompts_identical_across_conditions_except_fixed_prefix() -> None:
    for task in common.load_suite(common.DEFAULT_SUITE):
        base = common.condition_prompt(task, "baseline")
        assert common.condition_prompt(task, "plugin") == base
        explicit = common.condition_prompt(task, "plugin_explicit")
        assert explicit == common.EXPLICIT_PREFIX + base
        assert "creative-ideation" in common.EXPLICIT_PREFIX
        if task.get("context"):
            assert task["context"].strip() in base


def test_suite_validation_rejects_duplicates_and_missing_fields(tmp_path: Path) -> None:
    path = tmp_path / "s.json"
    path.write_text(json.dumps({"tasks": [{"id": "a", "domain": "d", "prompt": "p"}] * 2}), "utf-8")
    with pytest.raises(ValueError):
        common.load_suite(path)
    path.write_text(json.dumps({"tasks": [{"id": "a", "domain": "d"}]}), "utf-8")
    with pytest.raises(ValueError):
        common.load_suite(path)


def test_iter_cells_keeps_conditions_adjacent() -> None:
    tasks = [{"id": "t1", "domain": "d", "prompt": "p"}, {"id": "t2", "domain": "d", "prompt": "p"}]
    cells = runner.iter_cells(tasks, ["m1", "m2"], ["baseline", "plugin"], 2)
    assert len(cells) == 2 * 2 * 2 * 2
    assert [c.condition for c in cells[:4]] == ["baseline", "plugin", "baseline", "plugin"]
    assert cells[0].rel_dir == Path("baseline") / "m1" / "t1"
    assert cells[-1].rel_dir == Path("plugin") / "m2" / "t2__r1"


# ---------------------------------------------------------------- mcp 改寫


def test_rewrite_mcp_config_points_cgu_to_local_checkout(tmp_path: Path) -> None:
    original = json.loads(json.dumps(SHIPPED_MCP))
    out = runner.rewrite_mcp_config(SHIPPED_MCP, repo_root=REPO_ROOT, data_dir=tmp_path / "d")
    assert original == SHIPPED_MCP
    cgu = out["mcpServers"]["cgu"]
    assert cgu["command"] == "uv"
    assert cgu["args"] == ["--directory", str(REPO_ROOT), "run", "cgu-server"]
    assert cgu["type"] == "stdio"
    assert cgu["tools"] == ["*"]
    assert cgu["env"]["CGU_PROVIDER"] == "passthrough"
    assert cgu["env"]["CGU_LLM_PROVIDER"] == "passthrough"
    assert cgu["env"]["CGU_DATA_DIR"] == str(tmp_path / "d")
    assert out["mcpServers"]["other"] == SHIPPED_MCP["mcpServers"]["other"]
    assert out["$schema"] == SHIPPED_MCP["$schema"]


def test_rewrite_mcp_config_variants(tmp_path: Path) -> None:
    out = runner.rewrite_mcp_config(
        {"servers": {"cgu": {"command": "x", "cwd": "${PLUGIN_ROOT}"}}},
        repo_root=REPO_ROOT,
        data_dir=tmp_path,
        uv_no_sync=True,
    )
    assert "mcpServers" not in out
    assert out["servers"]["cgu"]["args"] == [
        "--directory",
        str(REPO_ROOT),
        "run",
        "--no-sync",
        "cgu-server",
    ]
    assert "cwd" not in out["servers"]["cgu"]
    created = runner.rewrite_mcp_config(None, repo_root=REPO_ROOT, data_dir=tmp_path)
    assert created["mcpServers"]["cgu"]["command"] == "uv"


def test_prepare_plugin_local_rewrites_and_adds_dotfile(plugin_src: Path, tmp_path: Path) -> None:
    dest = tmp_path / "copy"
    info = runner.prepare_plugin(
        plugin_src, dest, mcp_source="local", repo_root=REPO_ROOT, data_dir=tmp_path / "data"
    )
    assert not (dest / "__pycache__").exists()
    assert (dest / "skills" / "creative-ideation" / "SKILL.md").exists()
    assert info["mcp_files"] == [".mcp.json", "mcp.json"]
    assert any(".mcp.json" in w for w in info["warnings"])
    for name in (".mcp.json", "mcp.json"):
        cgu = json.loads((dest / name).read_text("utf-8"))["mcpServers"]["cgu"]
        assert cgu["command"] == "uv"
    assert json.loads((plugin_src / "mcp.json").read_text("utf-8")) == SHIPPED_MCP


def test_prepare_plugin_git_source_is_as_shipped(plugin_src: Path, tmp_path: Path) -> None:
    dest = tmp_path / "copy"
    runner.prepare_plugin(
        plugin_src, dest, mcp_source="git", repo_root=REPO_ROOT, data_dir=tmp_path / "data"
    )
    assert json.loads((dest / "mcp.json").read_text("utf-8")) == SHIPPED_MCP
    assert (dest / ".mcp.json").read_bytes() == (dest / "mcp.json").read_bytes()


def test_prepare_plugin_without_shim_or_mcp(plugin_src: Path, tmp_path: Path) -> None:
    dest = tmp_path / "copy"
    info = runner.prepare_plugin(
        plugin_src,
        dest,
        mcp_source="git",
        repo_root=REPO_ROOT,
        data_dir=tmp_path,
        dotfile_shim=False,
    )
    assert info["mcp_files"] == ["mcp.json"]

    (plugin_src / "mcp.json").unlink()
    dest2 = tmp_path / "copy2"
    info2 = runner.prepare_plugin(
        plugin_src, dest2, mcp_source="local", repo_root=REPO_ROOT, data_dir=tmp_path
    )
    assert info2["mcp_files"] == [".mcp.json"]
    assert (
        json.loads((dest2 / ".mcp.json").read_text("utf-8"))["mcpServers"]["cgu"]["command"] == "uv"
    )

    with pytest.raises(FileNotFoundError):
        runner.prepare_plugin(
            tmp_path / "nope",
            tmp_path / "x",
            mcp_source="local",
            repo_root=REPO_ROOT,
            data_dir=tmp_path,
        )


# ---------------------------------------------------------------- CLI 命令


def test_build_args_isolation_flags_and_verbatim_prompt(tmp_path: Path) -> None:
    prompt = '第一行\n第二行 100% "引號" & ^ | <>'
    req = CliRequest(
        prompt=prompt,
        model="claude-sonnet-5.5",
        cwd=tmp_path / "cwd",
        home=tmp_path / "home",
        log_dir=tmp_path / "logs",
        otel_path=tmp_path / "o.jsonl",
        timeout=10,
        plugin_dir=tmp_path / "plugin",
        reasoning_effort="high",
    )
    args = build_args(req)
    assert args[args.index("-p") + 1] == prompt
    assert args[args.index("--model") + 1] == "claude-sonnet-5.5"
    for flag in (
        "--allow-all-tools",
        "--no-ask-user",
        "--disable-builtin-mcps",
        "--no-custom-instructions",
    ):
        assert flag in args
    assert args[args.index("--output-format") + 1] == "json"
    assert args[args.index("--secret-env-vars") + 1] == "COPILOT_GITHUB_TOKEN"
    assert args[args.index("--plugin-dir") + 1] == str(tmp_path / "plugin")
    assert args[args.index("--reasoning-effort") + 1] == "high"
    assert args[args.index("-C") + 1] == str(tmp_path / "cwd")
    req.plugin_dir = None
    req.reasoning_effort = None
    assert "--plugin-dir" not in build_args(req)
    assert "--reasoning-effort" not in build_args(req)


def test_default_copilot_bin_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COPILOT_BIN", "X:\\custom\\copilot.cmd")
    assert default_copilot_bin() == "X:\\custom\\copilot.cmd"
    monkeypatch.delenv("COPILOT_BIN")
    assert default_copilot_bin()


@pytest.mark.skipif(os.name != "nt", reason="只有 Windows 的 npm .cmd 殼層需要繞過")
def test_resolve_command_bypasses_cmd_shim(tmp_path: Path) -> None:
    bin_dir = tmp_path / "node_modules" / ".bin"
    loader_dir = tmp_path / "node_modules" / "@github" / "copilot"
    bin_dir.mkdir(parents=True)
    loader_dir.mkdir(parents=True)
    (bin_dir / "copilot.cmd").write_text("@echo off", "utf-8")
    (loader_dir / "npm-loader.js").write_text("", "utf-8")
    cmd = resolve_command(str(bin_dir / "copilot.cmd"))
    assert cmd[-1] == str(loader_dir / "npm-loader.js")
    assert len(cmd) == 2


def test_check_local_mcp_outcomes(tmp_path: Path) -> None:
    def fake(returncode: int, stderr: str):
        return lambda *a, **k: subprocess.CompletedProcess(a, returncode, "", stderr)

    ok, _ = runner.check_local_mcp(REPO_ROOT, tmp_path, run=fake(0, ""))
    assert ok
    bad, detail = runner.check_local_mcp(
        REPO_ROOT,
        tmp_path,
        run=fake(1, "Traceback...\nModuleNotFoundError: No module named 'cgu.server'"),
    )
    assert not bad
    assert "cgu.server" in detail
    locked, _ = runner.check_local_mcp(
        REPO_ROOT, tmp_path, run=fake(2, "error: failed to remove file")
    )
    assert not locked

    def timeout(*a, **k):
        raise subprocess.TimeoutExpired("uv", 1)

    still_running, _ = runner.check_local_mcp(REPO_ROOT, tmp_path, run=timeout)
    assert still_running


# ---------------------------------------------------------------- dry-run 流程


def dry_args(tmp_path: Path, plugin_src: Path, *extra: str) -> list[str]:
    return [
        "--dry-run",
        "--run-id",
        "t-run",
        "--out-root",
        str(tmp_path / "runs"),
        "--work-root",
        str(tmp_path / "work"),
        "--plugin-source",
        str(plugin_src),
        "--tasks",
        "mr-delirium,ap-grant-reimbursement",
        "--models",
        "m-one,m-two",
        "--jobs",
        "3",
        *extra,
    ]


def test_dry_run_creates_expected_layout(plugin_src: Path, tmp_path: Path) -> None:
    code = runner.main(dry_args(tmp_path, plugin_src, "--repeats", "2"))
    assert code == 0
    run_dir = tmp_path / "runs" / "t-run"
    metas = [json.loads(p.read_text("utf-8")) for p in run_dir.glob("*/*/*/meta.json")]
    assert len(metas) == 2 * 2 * 3 * 2
    assert (run_dir / "baseline" / "m-one" / "mr-delirium" / "answer.md").exists()
    assert (
        run_dir / "plugin_explicit" / "m-two" / "ap-grant-reimbursement__r1" / "events.jsonl"
    ).exists()
    run_info = json.loads((run_dir / "run.json").read_text("utf-8"))
    assert run_info["cells_ok"] == 24 and run_info["cells_failed"] == 0
    assert run_info["dry_run"] is True
    assert run_info["plugin_tree_sha256"]
    assert not (tmp_path / "work").exists()

    by_key: dict[tuple, dict] = {}
    for meta in metas:
        by_key.setdefault((meta["model"], meta["task_id"], meta["repeat"]), {})[
            meta["condition"]
        ] = meta
    for conds in by_key.values():
        assert len({m["base_prompt_sha256"] for m in conds.values()}) == 1
        assert conds["baseline"]["prompt_sha256"] == conds["plugin"]["prompt_sha256"]
        assert conds["plugin_explicit"]["prompt_sha256"] != conds["plugin"]["prompt_sha256"]
        assert conds["baseline"]["cgu_connected"] is False
        assert conds["plugin"]["cgu_connected"] is True
        assert conds["baseline"]["cgu_tool_calls"] == 0
        assert conds["plugin"]["usage"]["input_tokens"] > 0
        assert conds["plugin"]["status"] == "ok"
    assert any(m["cgu_tool_calls"] > 0 for m in metas if m["condition"] != "baseline")
    assert any("creative-ideation" in m["skills_invoked"] for m in metas)


def test_resume_skips_completed_cells(plugin_src: Path, tmp_path: Path) -> None:
    assert runner.main(dry_args(tmp_path, plugin_src)) == 0
    backend = FakeBackend()
    code = runner.main(
        [*dry_args(tmp_path, plugin_src), "--resume", str(tmp_path / "runs" / "t-run")],
        backend=backend,
    )
    assert code == 0
    assert backend.calls == []


def test_work_root_inside_repo_is_refused(plugin_src: Path, tmp_path: Path) -> None:
    args = dry_args(tmp_path, plugin_src)
    args[args.index("--work-root") + 1] = str(REPO_ROOT / "evals" / ".work-refused")
    assert runner.main(args) == 2
    assert not (REPO_ROOT / "evals" / ".work-refused").exists()


def test_unknown_condition_is_rejected(plugin_src: Path, tmp_path: Path) -> None:
    assert runner.main(dry_args(tmp_path, plugin_src, "--conditions", "baseline,nope")) == 2


class ScriptedBackend:
    """依序回傳預先設定的結果；用完後重複最後一個。"""

    def __init__(self, results: list[CliResult]) -> None:
        self.results = results
        self.calls = 0

    def __call__(self, req: CliRequest) -> CliResult:
        result = self.results[min(self.calls, len(self.results) - 1)]
        self.calls += 1
        return result


def ok_result(answer: str = "答案", *, plugin: bool = False) -> CliResult:
    events = read_fixture("copilot_events_baseline.jsonl")
    if plugin:
        events = read_fixture("copilot_events_plugin_mcp.jsonl")
    return CliResult(
        exit_code=0, stdout=events.replace("兩個 server", answer), stderr="", duration_s=1.0
    )


def run_single(tmp_path: Path, backend, plugin_src: Path, conditions: str, retries: int = 1):
    code = runner.main(
        [
            "--run-id",
            "s",
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
            "--conditions",
            conditions,
            "--retries",
            str(retries),
            "--skip-mcp-check",
        ],
        backend=backend,
    )
    meta_path = next((tmp_path / "runs" / "s").glob("*/*/*/meta.json"))
    return code, json.loads(meta_path.read_text("utf-8"))


def test_transient_failure_is_retried(plugin_src: Path, tmp_path: Path) -> None:
    backend = ScriptedBackend(
        [CliResult(exit_code=1, stdout="", stderr="boom", duration_s=0.1), ok_result()]
    )
    code, meta = run_single(tmp_path, backend, plugin_src, "baseline")
    assert code == 0
    assert meta["status"] == "ok"
    assert meta["attempts"] == 2
    assert meta["attempt_history"][0]["reason"] == "exit_code_1"
    assert backend.calls == 2


def test_persistent_timeout_fails_after_retries(plugin_src: Path, tmp_path: Path) -> None:
    backend = ScriptedBackend(
        [CliResult(exit_code=None, stdout="", stderr="", duration_s=5.0, timed_out=True)]
    )
    code, meta = run_single(tmp_path, backend, plugin_src, "baseline", retries=2)
    assert code == 1
    assert meta["status"] == "failed"
    assert meta["failure_reason"] == "timeout"
    assert meta["attempts"] == 3
    assert not list((tmp_path / "runs" / "s").glob("*/*/*/answer.md"))


def test_plugin_condition_without_cgu_connection_fails(plugin_src: Path, tmp_path: Path) -> None:
    backend = ScriptedBackend([ok_result()])
    code, meta = run_single(tmp_path, backend, plugin_src, "plugin", retries=0)
    assert code == 1
    assert meta["failure_reason"] == "cgu_mcp_not_connected"


def test_plugin_condition_with_cgu_connection_records_tool_usage(
    plugin_src: Path, tmp_path: Path
) -> None:
    backend = ScriptedBackend([ok_result(plugin=True)])
    code, meta = run_single(tmp_path, backend, plugin_src, "plugin", retries=0)
    assert code == 0
    assert meta["cgu_connected"] is True
    assert meta["cgu_tool_calls"] == 1
    assert meta["cgu_tools"] == {"list_methods": 1}
    assert meta["plugin"]["mcp_files"] == [".mcp.json", "mcp.json"]


def test_baseline_contamination_is_flagged(plugin_src: Path, tmp_path: Path) -> None:
    events = [
        {
            "type": "session.skills_loaded",
            "data": {"skills": [{"name": "leaky", "source": "project"}]},
        },
        {"type": "assistant.message", "data": {"content": "答案", "toolRequests": []}},
        {"type": "result", "exitCode": 0, "usage": {}},
    ]
    stdout = "\n".join(json.dumps(e) for e in events)
    backend = ScriptedBackend([CliResult(exit_code=0, stdout=stdout, stderr="", duration_s=1.0)])
    _, meta = run_single(tmp_path, backend, plugin_src, "baseline")
    assert "unexpected_skills_loaded:leaky" in meta["warnings"]
