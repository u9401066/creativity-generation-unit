"""Copilot CLI 的呼叫封裝、JSONL 事件解析與離線假後端。"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

CGU_SERVER_NAME = "cgu"
_CGU_TOOL_RE = re.compile(r"^cgu[-_]", re.IGNORECASE)


def default_copilot_bin() -> str:
    env = os.environ.get("COPILOT_BIN")
    if env:
        return env
    name = "copilot.cmd" if os.name == "nt" else "copilot"
    candidate = Path(tempfile.gettempdir()) / "cgu-copilot" / "node_modules" / ".bin" / name
    return str(candidate) if candidate.exists() else "copilot"


def resolve_command(copilot_bin: str) -> list[str]:
    """把 npm 的 .cmd 殼層換成 node + npm-loader.js，避免 cmd.exe 破壞換行與特殊字元。"""
    found = shutil.which(copilot_bin) or copilot_bin
    path = Path(found)
    if os.name == "nt" and path.suffix.lower() in {".cmd", ".bat"}:
        loader = path.parent.parent / "@github" / "copilot" / "npm-loader.js"
        if loader.exists():
            local_node = path.parent / "node.exe"
            node = str(local_node) if local_node.exists() else (shutil.which("node") or "node")
            return [node, str(loader)]
    return [found]


def get_github_token() -> str:
    token = os.environ.get("COPILOT_GITHUB_TOKEN", "").strip()
    if token:
        return token
    try:
        proc = subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True, timeout=30, check=False
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"無法取得 GitHub token（gh auth token 失敗）: {exc}") from exc
    token = proc.stdout.strip()
    if proc.returncode != 0 or not token:
        raise RuntimeError(
            "無法取得 GitHub token：請設定 COPILOT_GITHUB_TOKEN 或先執行 gh auth login"
        )
    return token


@dataclass
class CliRequest:
    prompt: str
    model: str
    cwd: Path
    home: Path
    log_dir: Path
    otel_path: Path
    timeout: float
    plugin_dir: Path | None = None
    additional_mcp_config: Path | None = None
    reasoning_effort: str | None = None
    extra_args: tuple[str, ...] = ()
    tags: dict[str, Any] = field(default_factory=dict)


@dataclass
class CliResult:
    exit_code: int | None
    stdout: str
    stderr: str
    duration_s: float
    timed_out: bool = False
    otel_text: str | None = None


Backend = Callable[[CliRequest], CliResult]


def build_args(req: CliRequest) -> list[str]:
    args = [
        "-p",
        req.prompt,
        "--model",
        req.model,
        "-s",
        "--allow-all-tools",
        "--no-ask-user",
        "--disable-builtin-mcps",
        "--no-custom-instructions",
        "--no-auto-update",
        "--output-format",
        "json",
        "--secret-env-vars",
        "COPILOT_GITHUB_TOKEN",
        "--log-dir",
        str(req.log_dir),
        "-C",
        str(req.cwd),
    ]
    if req.reasoning_effort:
        args += ["--reasoning-effort", req.reasoning_effort]
    if req.plugin_dir is not None:
        args += ["--plugin-dir", str(req.plugin_dir)]
    if req.additional_mcp_config is not None:
        args += ["--additional-mcp-config", f"@{req.additional_mcp_config}"]
    args += list(req.extra_args)
    return args


def build_env(req: CliRequest, token: str) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "COPILOT_HOME": str(req.home),
            "COPILOT_GITHUB_TOKEN": token,
            "COPILOT_OTEL_FILE_EXPORTER_PATH": str(req.otel_path),
            "COPILOT_AUTO_UPDATE": "false",
            "NO_COLOR": "1",
            "PYTHONUTF8": "1",
        }
    )
    return env


def kill_tree(proc: subprocess.Popen[str]) -> None:
    if proc.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
            capture_output=True,
            check=False,
        )
    else:
        import signal

        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except OSError:
            proc.kill()


class CopilotBackend:
    def __init__(self, copilot_bin: str | None = None, token: str | None = None) -> None:
        self.command = resolve_command(copilot_bin or default_copilot_bin())
        self._token = token

    @property
    def token(self) -> str:
        if self._token is None:
            self._token = get_github_token()
        return self._token

    def version(self) -> str:
        try:
            proc = subprocess.run(
                [*self.command, "--version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return "unknown"
        lines = (proc.stdout or proc.stderr).strip().splitlines()
        return lines[0] if lines else "unknown"

    def __call__(self, req: CliRequest) -> CliResult:
        for path in (req.home, req.cwd, req.log_dir, req.otel_path.parent):
            path.mkdir(parents=True, exist_ok=True)
        cmd = [*self.command, *build_args(req)]
        env = build_env(req, self.token)
        popen_kwargs: dict[str, Any] = {}
        if os.name != "nt":
            popen_kwargs["start_new_session"] = True
        started = time.monotonic()
        proc = subprocess.Popen(
            cmd,
            cwd=str(req.cwd),
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            **popen_kwargs,
        )
        timed_out = False
        try:
            stdout, stderr = proc.communicate(timeout=req.timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            kill_tree(proc)
            stdout, stderr = proc.communicate()
        duration = time.monotonic() - started
        otel_text = None
        if req.otel_path.exists():
            otel_text = req.otel_path.read_text(encoding="utf-8", errors="replace")
        return CliResult(
            exit_code=None if timed_out else proc.returncode,
            stdout=stdout or "",
            stderr=stderr or "",
            duration_s=duration,
            timed_out=timed_out,
            otel_text=otel_text,
        )


# ---------------------------------------------------------------- 事件解析


@dataclass
class ParsedRun:
    answer: str = ""
    exit_code: int | None = None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    skills_invoked: list[str] = field(default_factory=list)
    skills_loaded: list[dict[str, str]] = field(default_factory=list)
    mcp_servers: dict[str, dict[str, str]] = field(default_factory=dict)
    tools_available: list[str] = field(default_factory=list)
    model_turns: int = 0
    premium_requests: float | None = None
    api_duration_ms: float | None = None
    session_duration_ms: float | None = None
    total_nano_aiu: float | None = None
    errors: list[str] = field(default_factory=list)
    bad_lines: int = 0

    @property
    def cgu_calls(self) -> list[dict[str, Any]]:
        return [c for c in self.tool_calls if is_cgu_call(c)]

    @property
    def cgu_tool_counts(self) -> dict[str, int]:
        counts = Counter(c.get("mcp_tool") or c["name"] for c in self.cgu_calls)
        return dict(sorted(counts.items()))

    @property
    def cgu_connected(self) -> bool:
        info = self.mcp_servers.get(CGU_SERVER_NAME)
        return bool(info and info.get("status") == "connected")

    @property
    def cgu_tools_available(self) -> list[str]:
        return [t for t in self.tools_available if _CGU_TOOL_RE.match(t)]


def is_cgu_call(call: dict[str, Any]) -> bool:
    server = (call.get("mcp_server") or "").lower()
    if server:
        return server == CGU_SERVER_NAME
    return bool(_CGU_TOOL_RE.match(call.get("name") or ""))


def parse_events(text: str) -> ParsedRun:
    """解析 `--output-format json` 的 JSONL；容忍未知或缺漏欄位。"""
    run = ParsedRun()
    calls: dict[str, dict[str, Any]] = {}
    messages: list[dict[str, Any]] = []
    deltas: dict[str, list[str]] = {}
    tools_seen: dict[str, None] = {}

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            run.bad_lines += 1
            continue
        if not isinstance(event, dict):
            run.bad_lines += 1
            continue
        etype = event.get("type", "")
        data = event.get("data") if isinstance(event.get("data"), dict) else {}

        if etype == "assistant.message":
            if not data.get("parentToolCallId"):
                messages.append(data)
        elif etype == "assistant.message_delta":
            deltas.setdefault(str(data.get("messageId", "")), []).append(
                str(data.get("deltaContent", ""))
            )
        elif etype == "assistant.turn_start":
            run.model_turns += 1
        elif etype == "tool.execution_start":
            call = {
                "id": data.get("toolCallId"),
                "name": data.get("toolName", ""),
                "mcp_server": data.get("mcpServerName"),
                "mcp_tool": data.get("mcpToolName"),
                "mcp_source": data.get("mcpConfigSource"),
                "success": None,
            }
            if call["name"] == "skill":
                skill = (data.get("arguments") or {}).get("skill")
                if skill:
                    run.skills_invoked.append(str(skill))
            run.tool_calls.append(call)
            if call["id"]:
                calls[call["id"]] = call
        elif etype == "tool.execution_complete":
            call = calls.get(data.get("toolCallId"))
            if call is not None:
                call["success"] = bool(data.get("success"))
        elif etype == "session.mcp_server_status_changed":
            name = data.get("serverName")
            if name:
                run.mcp_servers.setdefault(name, {})["status"] = str(data.get("status", ""))
        elif etype == "session.mcp_servers_loaded":
            for server in data.get("servers", []) or []:
                info = run.mcp_servers.setdefault(server.get("name", "?"), {})
                info["status"] = str(server.get("status", info.get("status", "")))
                if server.get("source"):
                    info["source"] = str(server["source"])
        elif etype == "session.skills_loaded":
            skills = data.get("skills") or []
            if skills:
                run.skills_loaded = [
                    {"name": str(s.get("name", "")), "source": str(s.get("source", ""))}
                    for s in skills
                ]
        elif etype == "session.usage_checkpoint":
            if data.get("totalNanoAiu") is not None:
                run.total_nano_aiu = float(data["totalNanoAiu"])
            for state in data.get("promptCacheBreakState", []) or []:
                for model_info in (state.get("models") or {}).values():
                    for tool in model_info.get("tools", []) or []:
                        name = tool.get("name") if isinstance(tool, dict) else tool
                        if name:
                            tools_seen[str(name)] = None
        elif etype == "result":
            run.exit_code = event.get("exitCode")
            usage = event.get("usage") or {}
            run.premium_requests = usage.get("premiumRequests")
            run.api_duration_ms = usage.get("totalApiDurationMs")
            run.session_duration_ms = usage.get("sessionDurationMs")
        elif etype in {"session.error", "error"}:
            run.errors.append(str(data.get("message") or data or event)[:500])

    run.tools_available = list(tools_seen)
    run.answer = _final_answer(messages, deltas)
    return run


def _final_answer(messages: list[dict[str, Any]], deltas: dict[str, list[str]]) -> str:
    # A run can emit several main-thread final_answer messages (e.g. an answer followed by a
    # correction after a review sub-agent returns); keeping only the last would drop the answer.
    finals = [
        str(m.get("content") or "").strip()
        for m in messages
        if m.get("phase") == "final_answer" and not m.get("toolRequests")
    ]
    finals = [c for c in finals if c]
    if finals:
        return "\n\n".join(finals)
    for msg in reversed(messages):
        content = str(msg.get("content") or "").strip()
        if content and not msg.get("toolRequests"):
            return content
    for msg in reversed(messages):
        content = str(msg.get("content") or "").strip()
        if content:
            return content
    for pieces in reversed(list(deltas.values())):
        joined = "".join(pieces).strip()
        if joined:
            return joined
    return ""


@dataclass
class OtelUsage:
    chat_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    cost: float = 0.0

    def as_dict(self) -> dict[str, float | int]:
        return {
            "chat_calls": self.chat_calls,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_read_tokens": self.cache_read_tokens,
            "cache_write_tokens": self.cache_write_tokens,
            "cost": self.cost,
        }


def parse_otel_usage(text: str | None) -> OtelUsage | None:
    """加總 OTel 檔案匯出器裡 `chat <model>` span 的 token 用量；無資料回傳 None。"""
    if not text:
        return None
    usage = OtelUsage()
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        attrs = item.get("attributes") if isinstance(item, dict) else None
        if item.get("type") != "span" or not isinstance(attrs, dict):
            continue
        if attrs.get("gen_ai.operation.name") != "chat":
            continue
        usage.chat_calls += 1
        usage.input_tokens += int(attrs.get("gen_ai.usage.input_tokens") or 0)
        usage.output_tokens += int(attrs.get("gen_ai.usage.output_tokens") or 0)
        usage.cache_read_tokens += int(attrs.get("gen_ai.usage.cache_read.input_tokens") or 0)
        usage.cache_write_tokens += int(attrs.get("gen_ai.usage.cache_write.input_tokens") or 0)
        usage.cost += float(attrs.get("github.copilot.cost") or 0.0)
    return usage if usage.chat_calls else None


# ---------------------------------------------------------------- 離線假後端


def _h(*parts: str) -> int:
    return int(hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:8], 16)


def make_events(
    answer: str, *, model: str, plugin: bool, skill: str | None, cgu_tools: list[str]
) -> list[dict[str, Any]]:
    """產生與真實 CLI 同形狀的最小 JSONL，供 dry-run 與測試使用。"""
    events: list[dict[str, Any]] = []

    def add(etype: str, data: dict[str, Any]) -> None:
        events.append({"type": etype, "data": data, "id": f"fake-{len(events)}"})

    if plugin:
        add("session.mcp_server_status_changed", {"serverName": "cgu", "status": "connected"})
        add(
            "session.mcp_servers_loaded",
            {"servers": [{"name": "cgu", "status": "connected", "source": "plugin"}]},
        )
        add(
            "session.skills_loaded",
            {"skills": [{"name": "creative-ideation", "source": "plugin"}]},
        )
    tool_names = ["powershell", "view", "skill"] + [f"cgu-{t}" for t in cgu_tools]
    add(
        "session.usage_checkpoint",
        {
            "totalNanoAiu": 1.0,
            "promptCacheBreakState": [
                {"models": {model: {"tools": [{"name": n} for n in tool_names]}}}
            ],
        },
    )
    turn = 0
    if skill:
        add("assistant.turn_start", {"turnId": str(turn)})
        add(
            "assistant.message",
            {
                "content": "",
                "toolRequests": [{"toolCallId": "skill-1", "name": "skill"}],
                "turnId": str(turn),
            },
        )
        add(
            "tool.execution_start",
            {"toolCallId": "skill-1", "toolName": "skill", "arguments": {"skill": skill}},
        )
        add("tool.execution_complete", {"toolCallId": "skill-1", "success": True})
        turn += 1
    for i, tool in enumerate(cgu_tools):
        cid = f"cgu-{i}"
        add("assistant.turn_start", {"turnId": str(turn)})
        add(
            "tool.execution_start",
            {
                "toolCallId": cid,
                "toolName": f"cgu-{tool}",
                "mcpServerName": "cgu",
                "mcpToolName": tool,
                "mcpConfigSource": "plugin",
            },
        )
        add("tool.execution_complete", {"toolCallId": cid, "success": True})
        turn += 1
    add("assistant.turn_start", {"turnId": str(turn)})
    add("assistant.message", {"content": answer, "toolRequests": [], "turnId": str(turn)})
    events.append(
        {
            "type": "result",
            "exitCode": 0,
            "usage": {"premiumRequests": 1, "totalApiDurationMs": 1000, "sessionDurationMs": 1500},
        }
    )
    return events


def make_otel(input_tokens: int, output_tokens: int, calls: int = 1) -> str:
    rows = []
    for _ in range(calls):
        rows.append(
            {
                "type": "span",
                "name": "chat fake",
                "attributes": {
                    "gen_ai.operation.name": "chat",
                    "gen_ai.usage.input_tokens": input_tokens,
                    "gen_ai.usage.output_tokens": output_tokens,
                    "github.copilot.cost": 1.0,
                },
            }
        )
    return "\n".join(json.dumps(r) for r in rows)


class FakeBackend:
    """不連網的假後端：依 (條件, 模型, 題目) 決定性地產生答案與事件。"""

    def __init__(self, judge_bias: str | None = None) -> None:
        self.judge_bias = judge_bias
        self.calls: list[CliRequest] = []

    def __call__(self, req: CliRequest) -> CliResult:
        self.calls.append(req)
        role = req.tags.get("role", "generate")
        if role == "judge":
            answer = self._judge_answer(req)
            plugin = False
            skill = None
            cgu_tools: list[str] = []
        else:
            condition = str(req.tags.get("condition", "baseline"))
            task = str(req.tags.get("task_id", "t"))
            plugin = req.plugin_dir is not None or condition.startswith("plugin")
            seed = _h(condition, req.model, task, str(req.tags.get("repeat", 0)))
            repeats = 4 + (seed % 5) + (6 if plugin else 0)
            tag = _h(condition) % 1000
            body = "\n".join(
                f"- 變體 {tag} 第 {i + 1} 點：針對 {task} 的具體建議與驗證步驟。"
                for i in range(repeats)
            )
            answer = f"## 假答案 ({req.model})\n{body}"
            use_tools = plugin and seed % 3 != 0
            cgu_tools = ["spark", "diverge"] if use_tools else []
            skill = "creative-ideation" if condition == "plugin_explicit" or use_tools else None
        events = make_events(
            answer, model=req.model, plugin=plugin, skill=skill, cgu_tools=cgu_tools
        )
        stdout = "\n".join(json.dumps(e, ensure_ascii=False) for e in events) + "\n"
        return CliResult(
            exit_code=0,
            stdout=stdout,
            stderr="",
            duration_s=0.01,
            otel_text=make_otel(1000 + len(answer), len(answer) // 2, calls=1 + len(cgu_tools)),
        )

    def _judge_answer(self, req: CliRequest) -> str:
        label = "A" if _h(req.prompt, req.model) % 2 == 0 else "B"
        if self.judge_bias in {"A", "B"}:
            label = self.judge_bias
        crit = dict.fromkeys(("novelty", "practicality", "reframing", "decidability"), label)
        return json.dumps(
            {
                "criteria": crit,
                "overconfidence": {"A": "low", "B": "medium"},
                "overall_winner": label,
                "reason": "dry-run 假評審的決定性回覆。",
            },
            ensure_ascii=False,
        )
