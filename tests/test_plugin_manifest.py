"""Structure and schema validation for the distributable Agent Plugins 1.0 package."""

from __future__ import annotations

import os
import re
import sys
import tomllib
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_plugin_support import (  # noqa: E402
    AGENTS_DIR,
    CODEX_MARKETPLACE,
    COPILOT_MARKETPLACE,
    PLUGIN_DIR,
    REPO_ROOT,
    SCHEMA_DIR,
    SKILLS_DIR,
    load_json,
)

jsonschema = pytest.importorskip("jsonschema", reason="jsonschema is a dev dependency")

PLUGIN_SCHEMA_ID = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
MCP_SCHEMA_ID = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"
ALLOWED_TOP_LEVEL = {"plugin.json", "mcp.json", "README.md", "skills", "com.github.copilot"}
MARKETPLACE_NAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9.-]{0,62}[a-z0-9])?$")
PLACEHOLDER_RE = re.compile(r"\$\{([^}]*)\}")


def _validator(schema_name: str) -> jsonschema.Draft202012Validator:
    schema = load_json(SCHEMA_DIR / schema_name)
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


def _errors(validator: jsonschema.Draft202012Validator, instance: object) -> list[str]:
    return [
        f"{'/'.join(map(str, e.path)) or '<root>'}: {e.message}"
        for e in validator.iter_errors(instance)
    ]


# --- vendored schemas -------------------------------------------------------------------


def test_vendored_schemas_are_the_1_0_0_documents() -> None:
    assert load_json(SCHEMA_DIR / "plugin.schema.json")["$id"] == PLUGIN_SCHEMA_ID
    assert load_json(SCHEMA_DIR / "mcp.schema.json")["$id"] == MCP_SCHEMA_ID


# --- plugin.json ------------------------------------------------------------------------


def test_plugin_json_is_schema_valid() -> None:
    manifest = load_json(PLUGIN_DIR / "plugin.json")
    assert _errors(_validator("plugin.schema.json"), manifest) == []


def test_plugin_json_identity_and_metadata() -> None:
    manifest = load_json(PLUGIN_DIR / "plugin.json")
    assert manifest["$schema"] == PLUGIN_SCHEMA_ID
    assert manifest["name"] == "cgu"
    assert manifest["version"] == "0.8.0"
    assert manifest["license"] == "Apache-2.0"
    assert manifest["author"] == {"name": "u9401066", "email": "u9401066@gap.kmu.edu.tw"}
    repo = "https://github.com/u9401066/creativity-generation-unit"
    assert manifest["homepage"] == repo
    assert manifest["repository"] == repo
    assert manifest["description"].strip()
    assert manifest["keywords"] and all(isinstance(k, str) and k for k in manifest["keywords"])


def test_plugin_json_has_no_component_path_fields() -> None:
    manifest = load_json(PLUGIN_DIR / "plugin.json")
    for forbidden in ("skills", "agents", "hooks", "commands", "mcpServers", "lspServers", "rules"):
        assert forbidden not in manifest, f"{forbidden} is not an Agent Plugins 1.0 manifest field"


def test_plugin_json_extension_paths_exist_and_stay_inside() -> None:
    manifest = load_json(PLUGIN_DIR / "plugin.json")
    extensions = manifest.get("extensions", {})
    assert set(extensions) <= {"com.openai"}, "only the documented OpenAI namespace is expected"

    def walk(value: object) -> list[str]:
        if isinstance(value, str):
            return [value] if value.startswith("./") else []
        if isinstance(value, dict):
            return [s for v in value.values() for s in walk(v)]
        if isinstance(value, list):
            return [s for v in value for s in walk(v)]
        return []

    for rel in walk(extensions):
        target = (PLUGIN_DIR / rel).resolve()
        assert target.is_relative_to(PLUGIN_DIR.resolve()), rel
        assert target.exists(), f"extension path does not exist: {rel}"


# --- mcp.json ---------------------------------------------------------------------------


def test_mcp_json_is_schema_valid() -> None:
    config = load_json(PLUGIN_DIR / "mcp.json")
    assert _errors(_validator("mcp.schema.json"), config) == []


def test_mcp_json_declares_cgu_stdio_server_via_uvx() -> None:
    config = load_json(PLUGIN_DIR / "mcp.json")
    assert config["$schema"] == MCP_SCHEMA_ID
    assert list(config["mcpServers"]) == ["cgu"]
    server = config["mcpServers"]["cgu"]
    assert server["type"] == "stdio"
    assert server["command"] == "uvx"
    assert server["args"] == [
        "--from",
        "git+https://github.com/u9401066/creativity-generation-unit@master",
        "cgu-server",
    ]
    assert server["env"] == {"CGU_PROVIDER": "passthrough", "CGU_DATA_DIR": "${PLUGIN_DATA}/cgu"}


def test_mcp_json_uses_only_reserved_placeholders_and_no_secrets() -> None:
    server = load_json(PLUGIN_DIR / "mcp.json")["mcpServers"]["cgu"]
    values = [*server["args"], *server["env"].values()]
    for value in values:
        for placeholder in PLACEHOLDER_RE.findall(value):
            assert placeholder in {"PLUGIN_ROOT", "PLUGIN_DATA"}, placeholder
    for key in server["env"]:
        assert not re.search(r"KEY|TOKEN|SECRET|PASSWORD", key, re.IGNORECASE), key


def test_mcp_entry_point_exists_in_pyproject() -> None:
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert "cgu-server" in pyproject["project"]["scripts"], (
        "mcp.json launches `cgu-server`; pyproject [project.scripts] must define it"
    )


# --- marketplaces -----------------------------------------------------------------------


def _marketplace_plugin_dirs(entries: list[dict], root: Path) -> list[Path]:
    dirs = []
    for entry in entries:
        source = entry["source"]
        rel = source if isinstance(source, str) else source["path"]
        dirs.append((root / rel).resolve())
    return dirs


def test_copilot_marketplace_is_valid_and_points_at_the_plugin() -> None:
    market = load_json(COPILOT_MARKETPLACE)
    assert MARKETPLACE_NAME_RE.match(market["name"])
    assert market["owner"]["name"]
    manifest = load_json(PLUGIN_DIR / "plugin.json")
    assert [p["name"] for p in market["plugins"]] == [manifest["name"]]
    entry = market["plugins"][0]
    assert entry["source"] == "./plugins/cgu"
    assert entry["version"] == manifest["version"]
    assert len(entry["description"]) <= 1024
    assert _marketplace_plugin_dirs(market["plugins"], REPO_ROOT) == [PLUGIN_DIR.resolve()]
    assert (PLUGIN_DIR / "plugin.json").is_file()


def test_codex_marketplace_is_valid_and_points_at_the_plugin() -> None:
    market = load_json(CODEX_MARKETPLACE)
    assert MARKETPLACE_NAME_RE.match(market["name"])
    manifest = load_json(PLUGIN_DIR / "plugin.json")
    assert [p["name"] for p in market["plugins"]] == [manifest["name"]]
    entry = market["plugins"][0]
    source = entry["source"]
    assert source == {"source": "local", "path": "./plugins/cgu"}
    assert entry["policy"]["installation"] in {"AVAILABLE", "INSTALLED_BY_DEFAULT", "NOT_AVAILABLE"}
    assert isinstance(entry["policy"]["authentication"], str) and entry["policy"]["authentication"]
    assert entry["category"]
    resolved = _marketplace_plugin_dirs(market["plugins"], REPO_ROOT)
    assert resolved == [PLUGIN_DIR.resolve()]
    assert resolved[0].is_relative_to(REPO_ROOT.resolve())


def test_both_marketplaces_share_one_marketplace_name() -> None:
    assert load_json(COPILOT_MARKETPLACE)["name"] == load_json(CODEX_MARKETPLACE)["name"]


# --- package boundaries -----------------------------------------------------------------


def test_plugin_root_contains_only_expected_entries() -> None:
    assert {p.name for p in PLUGIN_DIR.iterdir()} == ALLOWED_TOP_LEVEL


def test_skills_directory_has_only_immediate_skill_subdirectories() -> None:
    children = list(SKILLS_DIR.iterdir())
    assert children and all(c.is_dir() for c in children)
    for child in children:
        assert (child / "SKILL.md").is_file(), f"{child.name}/SKILL.md must be a regular file"


def test_everything_stays_inside_plugin_root_without_links() -> None:
    root = PLUGIN_DIR.resolve()
    for current, dirs, files in os.walk(PLUGIN_DIR):
        for name in [*dirs, *files]:
            path = Path(current) / name
            assert not path.is_symlink(), f"symlink in package: {path}"
            is_junction = getattr(path, "is_junction", None)
            assert not (is_junction and is_junction()), f"junction in package: {path}"
            assert path.resolve().is_relative_to(root), f"escapes package root: {path}"


def test_package_contains_no_hooks() -> None:
    """Decision D-20: hooks run local code and are not portable, so the plugin ships none."""
    hook_like = [
        p
        for p in PLUGIN_DIR.rglob("*")
        if p.name.lower() == "hooks" or "hooks" in p.name.lower().split(".")
    ]
    assert hook_like == [], f"unexpected hook files: {hook_like}"
    manifest = load_json(PLUGIN_DIR / "plugin.json")
    assert "hooks" not in manifest
    for namespace in manifest.get("extensions", {}).values():
        assert "hooks" not in namespace


def test_agents_live_only_in_the_copilot_namespace() -> None:
    assert list(PLUGIN_DIR.rglob("*.agent.md")) != []
    for agent in PLUGIN_DIR.rglob("*.agent.md"):
        assert agent.parent == AGENTS_DIR, agent


def test_package_has_no_machine_specific_paths() -> None:
    pattern = re.compile(r"[A-Za-z]:\\\\?(?:Users|workspace)|/home/\w+|/Users/\w+", re.IGNORECASE)
    for path in PLUGIN_DIR.rglob("*"):
        if path.is_file() and path.suffix in {".md", ".json"}:
            text = path.read_text(encoding="utf-8")
            assert not pattern.search(text), f"machine-specific path in {path}"
