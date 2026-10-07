"""Skill-to-tool contract: skills and agents may only name tools/actions that really exist.

Two layers:
1. A static layer checked against ``docs/architecture.md`` (always runs).
2. A live layer that builds the real server with ``cgu.interfaces.mcp.server.create_server``
   and checks every mentioned tool/action against the registered input schemas. It is skipped
   (with a clear message) while ``cgu.interfaces`` is not importable yet; set
   ``CGU_REQUIRE_LIVE_CONTRACT=1`` to turn that skip into a failure (CI / release checks).
"""

from __future__ import annotations

import asyncio
import importlib
import os
import re
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_plugin_support import (  # noqa: E402
    PLUGIN_DIR,
    REPO_ROOT,
    SKILL_NAMES,
    plugin_markdown_files,
    skill_and_agent_files,
)

# Derived from docs/architecture.md section 4 (the binding contract).
ARCH_ACTIONS: dict[str, set[str]] = {
    "cgu_status": set(),
    "cgu_session": {"open", "get", "list", "export", "delete"},
    "cgu_frame": {"create", "get", "operators", "operate", "commit", "doubt"},
    "cgu_material": {"search", "add", "list"},
    "cgu_diverge": {"typical_set", "anti_typical", "fanout", "collide"},
    "cgu_ideas": {"add", "list", "measure"},
    "cgu_judge": {"plan", "record", "rank"},
    "cgu_evolve": {"map", "next", "submit", "resolve"},
    "cgu_feedback": {"record", "summary", "export", "delete"},
    "cgu_question_gate": {"check", "record"},
    "cgu_inquiry": {
        "settings",
        "capture",
        "list",
        "themes",
        "label",
        "mine",
        "related",
        "organize",
        "distill",
        "materials",
        "export",
        "delete",
    },
}
OPERATORS = {
    "explicate",
    "bracket",
    "negate",
    "tetralemma",
    "re_explicate",
    "swap_metaphor",
    "recut_unit",
    "shift_stakeholder",
    "invert_criterion",
    "genealogize",
    "thought_experiment",
}
IDEA_KINDS = {"typical", "candidate", "human", "prior_art"}
VARY_VALUES = {"prompt", "material", "operator", "model"}
DECISIONS = {"adopt", "modify", "abandon"}

TOOL_NAME_RE = re.compile(r"\bcgu_[a-z][a-z_]*\b")
CALL_RE = re.compile(r"\b(cgu_[a-z][a-z_]*)\(([^)]*)\)?")
ACTION_RE = re.compile(r"^\s*action\s*=\s*[\"']?([a-z_]+)[\"']?")


def _scan_files() -> list[Path]:
    files = {*skill_and_agent_files(), *plugin_markdown_files()}
    return sorted(files)


def _rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _mentioned_tools() -> Iterator[tuple[Path, str]]:
    for path in _scan_files():
        for name in TOOL_NAME_RE.findall(path.read_text(encoding="utf-8")):
            yield path, name


def _calls() -> Iterator[tuple[Path, str, str | None, str]]:
    """Yield (file, tool, action, args) for every ``cgu_x(...)`` call-like mention."""
    for path in _scan_files():
        for tool, args in CALL_RE.findall(path.read_text(encoding="utf-8")):
            match = ACTION_RE.match(args)
            yield path, tool, (match.group(1) if match else None), args


# --- static layer ---------------------------------------------------------------------


def test_static_contract_table_matches_architecture_doc() -> None:
    doc = REPO_ROOT / "docs" / "architecture.md"
    if not doc.is_file():
        pytest.skip("docs/architecture.md not present")
    text = doc.read_text(encoding="utf-8")
    documented = set(re.findall(r"^### 4\.\d+ `(cgu_[a-z_]+)\(", text, re.MULTILINE))
    assert documented == set(ARCH_ACTIONS), (
        "tests/test_plugin_contract.py ARCH_ACTIONS is out of sync with docs/architecture.md section 4"
    )


def test_every_mentioned_tool_is_a_documented_tool() -> None:
    unknown = {(_rel(p), n) for p, n in _mentioned_tools() if n not in ARCH_ACTIONS}
    assert not unknown, f"unknown tool names: {sorted(unknown)}"


def test_every_call_uses_a_documented_action() -> None:
    problems = []
    for path, tool, action, args in _calls():
        if tool not in ARCH_ACTIONS:
            continue
        if not ARCH_ACTIONS[tool]:
            if args.strip():
                problems.append(f"{_rel(path)}: {tool}({args}) takes no arguments")
            continue
        if action is None:
            problems.append(f"{_rel(path)}: {tool}({args}) must start with action=<name>")
        elif action not in ARCH_ACTIONS[tool]:
            problems.append(f"{_rel(path)}: {tool}(action={action}) is not an action of {tool}")
    assert not problems, "\n".join(problems)


def test_enumerated_argument_values_are_valid() -> None:
    checks = {
        "kind": IDEA_KINDS,
        "operator": OPERATORS,
        "decision": DECISIONS,
    }
    problems = []
    for path in _scan_files():
        text = path.read_text(encoding="utf-8")
        for arg, allowed in checks.items():
            for value in re.findall(rf"\b{arg}=([a-z_]+)\b", text):
                if value not in allowed:
                    problems.append(f"{_rel(path)}: {arg}={value}")
        for raw in re.findall(r"\bvary=\[([^\]]*)\]", text):
            for value in re.findall(r"[a-z_]+", raw):
                if value not in VARY_VALUES:
                    problems.append(f"{_rel(path)}: vary has {value}")
    assert not problems, "\n".join(problems)


@pytest.mark.parametrize(
    ("skill", "required"),
    [
        (
            "creative-ideation",
            {
                "cgu_status",
                "cgu_session",
                "cgu_frame",
                "cgu_diverge",
                "cgu_ideas",
                "cgu_material",
                "cgu_judge",
                "cgu_feedback",
            },
        ),
        ("frame-audit", {"cgu_frame", "cgu_question_gate", "cgu_diverge", "cgu_ideas"}),
        ("maieutic-session", {"cgu_question_gate", "cgu_ideas", "cgu_frame", "cgu_feedback"}),
        ("idea-triage", {"cgu_ideas", "cgu_judge", "cgu_feedback", "cgu_material"}),
        (
            "inquiry-mining",
            {"cgu_status", "cgu_inquiry", "cgu_session", "cgu_frame", "cgu_diverge", "cgu_ideas"},
        ),
    ],
)
def test_each_skill_uses_its_core_tools(skill: str, required: set[str]) -> None:
    text = (PLUGIN_DIR / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
    assert required <= set(TOOL_NAME_RE.findall(text))


def test_orchestrator_follows_the_documented_order() -> None:
    text = (PLUGIN_DIR / "skills" / "creative-ideation" / "SKILL.md").read_text(encoding="utf-8")
    sequence = [
        "cgu_session(action=open",
        "cgu_status()",
        "cgu_frame(action=create",
        "cgu_ideas(action=add",
        "cgu_diverge(action=typical_set",
        "cgu_frame(action=operate",
        "cgu_frame(action=doubt",
        "cgu_diverge(action=anti_typical",
        "cgu_ideas(action=measure",
        "cgu_judge(action=plan",
        "cgu_judge(action=record",
        "cgu_judge(action=rank",
        "cgu_feedback(action=record",
    ]
    positions = [text.index(token) for token in sequence]
    assert positions == sorted(positions), "creative-ideation steps are out of order"


def test_all_skills_are_covered_by_the_scan() -> None:
    scanned = {p.parent.name for p in _scan_files() if p.name == "SKILL.md"}
    assert scanned == set(SKILL_NAMES)


# --- live layer -----------------------------------------------------------------------


def _skip_or_fail(reason: str) -> None:
    if os.environ.get("CGU_REQUIRE_LIVE_CONTRACT"):
        pytest.fail(reason)
    pytest.skip(reason)


def _resolve(schema: Any, root: dict[str, Any]) -> Any:
    while isinstance(schema, dict) and "$ref" in schema:
        node: Any = root
        for part in schema["$ref"].lstrip("#/").split("/"):
            node = node[part]
        schema = node
    return schema


def _enum_values(schema: Any, root: dict[str, Any], depth: int = 0) -> set[str]:
    schema = _resolve(schema, root)
    if not isinstance(schema, dict) or depth > 8:
        return set()
    values: set[str] = set()
    if "enum" in schema:
        values |= {v for v in schema["enum"] if isinstance(v, str)}
    if isinstance(schema.get("const"), str):
        values.add(schema["const"])
    for key in ("anyOf", "oneOf", "allOf"):
        for sub in schema.get(key, []):
            values |= _enum_values(sub, root, depth + 1)
    return values


def _property_enums(schema: Any, root: dict[str, Any], prop: str, depth: int = 0) -> set[str]:
    """Collect enum values of every property called ``prop`` anywhere in the schema."""
    schema = _resolve(schema, root)
    if not isinstance(schema, dict) or depth > 10:
        return set()
    found: set[str] = set()
    for name, sub in schema.get("properties", {}).items():
        if name == prop:
            found |= _enum_values(sub, root)
        found |= _property_enums(sub, root, prop, depth + 1)
    for key in ("items", "additionalProperties"):
        if isinstance(schema.get(key), dict):
            found |= _property_enums(schema[key], root, prop, depth + 1)
    for key in ("anyOf", "oneOf", "allOf"):
        for sub in schema.get(key, []):
            found |= _property_enums(sub, root, prop, depth + 1)
    for definition in schema.get("$defs", {}).values():
        found |= _property_enums(definition, root, prop, depth + 1)
    return found


def _build_live_registry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> dict[str, dict[str, Any]]:
    try:
        server_module = importlib.import_module("cgu.interfaces.mcp.server")
        config_module = importlib.import_module("cgu.infrastructure.config")
    except ModuleNotFoundError as exc:
        if (exc.name or "").startswith("cgu"):
            _skip_or_fail(
                f"cgu.interfaces is not importable yet ({exc}); live contract not checked"
            )
        raise
    monkeypatch.setenv("CGU_DATA_DIR", str(tmp_path / "cgu-data"))
    monkeypatch.setenv("CGU_PROVIDER", "passthrough")
    monkeypatch.setenv("CGU_NETWORK", "off")
    monkeypatch.setenv("CGU_EMBEDDING", "ngram")
    settings = config_module.Settings.from_env()
    server = server_module.create_server(settings)
    tools = asyncio.run(server.list_tools())
    registry = {}
    for tool in tools:
        schema = getattr(tool, "input_schema", None) or getattr(tool, "inputSchema", None) or {}
        registry[tool.name] = schema
    return registry


def test_skills_only_reference_tools_and_actions_in_the_live_registry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    registry = _build_live_registry(tmp_path, monkeypatch)
    assert registry, "create_server registered no tools"

    missing_tools = {(_rel(p), n) for p, n in _mentioned_tools() if n not in registry}
    assert not missing_tools, (
        f"tools mentioned in skills/agents but not registered: {sorted(missing_tools)}"
    )

    problems = []
    for path, tool, action, _ in _calls():
        if tool not in registry or action is None:
            continue
        schema = registry[tool]
        allowed = _enum_values(schema.get("properties", {}).get("action", {}), schema)
        if not allowed:
            problems.append(
                f"{tool}: registry exposes no enum for 'action' (use Literal for actions)"
            )
        elif action not in allowed:
            problems.append(
                f"{_rel(path)}: {tool}(action={action}) not in registry enum {sorted(allowed)}"
            )
    assert not problems, "\n".join(sorted(set(problems)))


def test_live_registry_exposes_the_documented_tool_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    registry = _build_live_registry(tmp_path, monkeypatch)
    assert set(registry) == set(ARCH_ACTIONS)
    for tool, actions in ARCH_ACTIONS.items():
        if not actions:
            continue
        schema = registry[tool]
        live = _enum_values(schema.get("properties", {}).get("action", {}), schema)
        assert actions <= live, (
            f"{tool}: documented actions missing from registry: {sorted(actions - live)}"
        )


def test_live_idea_kinds_cover_what_skills_use(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    registry = _build_live_registry(tmp_path, monkeypatch)
    schema = registry["cgu_ideas"]
    live_kinds = _property_enums(schema, schema, "kind")
    if not live_kinds:
        pytest.skip("cgu_ideas schema does not expose a 'kind' enum")
    used = set()
    for path in _scan_files():
        used |= set(re.findall(r"\bkind=([a-z_]+)\b", path.read_text(encoding="utf-8")))
    assert used <= live_kinds, (
        f"skills use idea kinds the server does not accept: {sorted(used - live_kinds)}"
    )
