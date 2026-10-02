"""The dependency rules of docs/architecture.md section 2, enforced."""

from __future__ import annotations

import re
import sys

import pytest
from cgu_support import SRC, imported_modules

FORBIDDEN = {
    "domain": (
        "cgu.application",
        "cgu.infrastructure",
        "cgu.interfaces",
        "mcp",
        "mcp_types",
        "httpx",
        "sqlite3",
    ),
    "application": ("cgu.infrastructure", "cgu.interfaces", "mcp", "mcp_types"),
    "infrastructure": ("cgu.interfaces",),
}
ALLOWED_THIRD_PARTY = {"domain": {"pydantic", "numpy"}}


def _violations(layer: str) -> list[str]:
    bad: list[str] = []
    for path in sorted((SRC / layer).rglob("*.py")):
        for module in imported_modules(path):
            for forbidden in FORBIDDEN[layer]:
                if module == forbidden or module.startswith(forbidden + "."):
                    bad.append(f"{path.relative_to(SRC)} imports {module}")
    return bad


@pytest.mark.parametrize("layer", ["domain", "application", "infrastructure"])
def test_layer_does_not_import_outward(layer: str) -> None:
    assert _violations(layer) == []


def test_domain_depends_only_on_stdlib_pydantic_numpy_and_itself() -> None:
    stdlib = set(sys.stdlib_module_names)
    bad: list[str] = []
    for path in sorted((SRC / "domain").rglob("*.py")):
        for module in imported_modules(path):
            root = module.split(".")[0]
            if root in stdlib or root in ALLOWED_THIRD_PARTY["domain"]:
                continue
            if module == "cgu" or module.startswith("cgu.domain"):
                continue
            bad.append(f"{path.relative_to(SRC)} imports {module}")
    assert bad == []


def test_only_config_reads_the_environment() -> None:
    pattern = re.compile(r"os\.environ|os\.getenv|getenv\(")
    readers = [
        path.relative_to(SRC).as_posix()
        for path in SRC.rglob("*.py")
        if pattern.search(path.read_text(encoding="utf-8"))
    ]
    assert readers == ["infrastructure/config.py"]


def test_removed_dependencies_are_not_imported() -> None:
    removed = {
        "langgraph",
        "langchain",
        "openai",
        "instructor",
        "duckduckgo_search",
        "rich",
        "dotenv",
    }
    for path in SRC.rglob("*.py"):
        roots = {m.split(".")[0] for m in imported_modules(path)}
        assert not (roots & removed), f"{path.relative_to(SRC)} imports {roots & removed}"


def test_old_modules_are_gone() -> None:
    for name in ("agents", "core", "graph", "llm", "soup", "thinking", "tools"):
        assert not (SRC / name).exists()
    for name in ("brainstorm_protocol.py", "cli.py", "server.py"):
        assert not (SRC / name).exists()
