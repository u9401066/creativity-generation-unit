"""共用常數與小工具：條件定義、題庫載入、提示組裝、檔案 I/O。"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
EVALS_DIR = REPO_ROOT / "evals"
DEFAULT_SUITE = EVALS_DIR / "suites" / "domains.json"
DEFAULT_RUNS_DIR = EVALS_DIR / "runs"
DEFAULT_REPORTS_DIR = EVALS_DIR / "reports"
DEFAULT_PLUGIN_SOURCE = REPO_ROOT / "plugins" / "cgu"

DEFAULT_GEN_MODELS = ("claude-sonnet-5.5", "gpt-6-luna")
DEFAULT_JUDGE_MODELS = ("claude-opus-5.5", "gpt-6-sol")
JUDGE_FALLBACKS: dict[str, tuple[str, ...]] = {
    "claude-opus-5.5": ("claude-opus-5", "claude-opus-4.8"),
    "gpt-6-sol": ("gpt-6.1-sol", "gpt-5.6-sol"),
}

EXPLICIT_PREFIX = "請使用 `creative-ideation` skill 來處理以下需求。\n\n"
PROMPTED_PREFIX = "請先多方探索、列出至少五個差異明顯的方向，並檢查隱性假設，再收斂成最終建議。\n\n"

# plugin: 是否載入 plugin；prefix: 加在共同提示前的固定句
CONDITIONS: dict[str, dict[str, Any]] = {
    "baseline": {"plugin": False, "prefix": ""},
    "plugin": {"plugin": True, "prefix": ""},
    "plugin_explicit": {"plugin": True, "prefix": EXPLICIT_PREFIX},
    "baseline_prompted": {"plugin": False, "prefix": PROMPTED_PREFIX},
}
DEFAULT_CONDITIONS = ("baseline", "plugin", "plugin_explicit")
DEFAULT_PAIRS = (("baseline", "plugin"), ("baseline", "plugin_explicit"))

MODEL_FAMILIES = (("claude", "anthropic"), ("gpt", "openai"), ("gemini", "google"))


def utc_stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d-%H%M%S")


def iso_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", text).strip("_") or "x"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def model_family(model: str) -> str:
    low = model.lower()
    for prefix, family in MODEL_FAMILIES:
        if low.startswith(prefix):
            return family
    return "other"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text + "\n", encoding="utf-8")
    tmp.replace(path)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def load_suite(path: Path) -> list[dict[str, Any]]:
    data = read_json(path)
    tasks = data["tasks"] if isinstance(data, dict) else data
    seen: set[str] = set()
    for task in tasks:
        for key in ("id", "domain", "prompt"):
            if not str(task.get(key, "")).strip():
                raise ValueError(f"題庫項目缺少欄位 {key}: {task}")
        if task["id"] in seen:
            raise ValueError(f"題庫 id 重複: {task['id']}")
        seen.add(task["id"])
    return tasks


def base_prompt(task: dict[str, Any]) -> str:
    """所有條件共用的任務提示（含選用的背景資料）。"""
    prompt = task["prompt"].strip()
    context = str(task.get("context") or "").strip()
    return f"{prompt}\n\n【背景資料】\n{context}" if context else prompt


def condition_prompt(task: dict[str, Any], condition: str) -> str:
    return CONDITIONS[condition]["prefix"] + base_prompt(task)


def select_tasks(
    tasks: list[dict[str, Any]], ids: str | None, domains: str | None
) -> list[dict[str, Any]]:
    selected = tasks
    if ids and ids != "all":
        wanted = [t.strip() for t in ids.split(",") if t.strip()]
        unknown = set(wanted) - {t["id"] for t in tasks}
        if unknown:
            raise ValueError(f"找不到題目: {sorted(unknown)}")
        selected = [t for t in tasks if t["id"] in wanted]
    if domains:
        wanted_d = {d.strip() for d in domains.split(",") if d.strip()}
        selected = [t for t in selected if t["domain"] in wanted_d]
    return selected


def split_csv(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


def parse_pairs(value: str) -> list[tuple[str, str]]:
    pairs = []
    for item in split_csv(value):
        left, sep, right = item.partition(":")
        if not sep or left not in CONDITIONS or right not in CONDITIONS:
            raise ValueError(f"無效的 pair: {item}（格式 baseline:plugin）")
        pairs.append((left, right))
    return pairs


def repeat_dirname(task_id: str, repeat: int) -> str:
    return task_id if repeat == 0 else f"{task_id}__r{repeat}"
