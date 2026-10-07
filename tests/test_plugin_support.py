"""Shared helpers for the ``tests/test_plugin_*.py`` suite (no plugin assertions live here)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_DIR = REPO_ROOT / "plugins" / "cgu"
SKILLS_DIR = PLUGIN_DIR / "skills"
AGENTS_DIR = PLUGIN_DIR / "com.github.copilot" / "agents"
SCHEMA_DIR = REPO_ROOT / "tests" / "schemas" / "agent-plugins" / "1.0.0"
COPILOT_MARKETPLACE = REPO_ROOT / ".github" / "plugin" / "marketplace.json"
CODEX_MARKETPLACE = REPO_ROOT / ".agents" / "plugins" / "marketplace.json"

SKILL_NAMES = (
    "creative-ideation",
    "frame-audit",
    "maieutic-session",
    "idea-triage",
    "inquiry-mining",
)
AGENT_NAMES = (
    "creative-facilitator",
    "frame-auditor",
    "independent-ideator",
    "adversarial-critic",
)

_FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?(.*)\Z", re.DOTALL)
_KEY_VALUE_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):\s*(.*)$")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_scalar(raw: str) -> Any:
    raw = raw.strip()
    if raw == "":
        return ""
    if raw[0] == '"':
        return json.loads(raw)
    if raw[0] == "'" and raw[-1] == "'" and len(raw) >= 2:
        return raw[1:-1].replace("''", "'")
    if raw[0] == "[":
        return json.loads(raw)
    if raw in ("true", "false"):
        return raw == "true"
    return raw


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Parse the deliberately simple frontmatter used by this plugin.

    Only single-line ``key: value`` pairs are supported (JSON-style quoted strings and
    inline lists), so every client's lightweight parser can read the files too.
    """
    match = _FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError("file does not start with a '---' frontmatter block")
    meta: dict[str, Any] = {}
    for line in match.group(1).splitlines():
        if not line.strip():
            continue
        kv = _KEY_VALUE_RE.match(line)
        if not kv:
            raise ValueError(f"unsupported frontmatter line (keep it single-line): {line!r}")
        meta[kv.group(1)] = _parse_scalar(kv.group(2))
    return meta, match.group(2)


def read_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    return split_frontmatter(path.read_text(encoding="utf-8"))


def plugin_markdown_files() -> list[Path]:
    return sorted(PLUGIN_DIR.rglob("*.md"))


def skill_and_agent_files() -> list[Path]:
    files = [SKILLS_DIR / name / "SKILL.md" for name in SKILL_NAMES]
    files += [AGENTS_DIR / f"{name}.agent.md" for name in AGENT_NAMES]
    return files


def test_helpers_parse_frontmatter() -> None:
    meta, body = split_frontmatter(
        '---\nname: x\ndescription: "a: b"\ntools: ["a", "b"]\n---\nbody\n'
    )
    assert meta == {"name": "x", "description": "a: b", "tools": ["a", "b"]}
    assert body == "body\n"
