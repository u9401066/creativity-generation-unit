"""Release packaging must exclude local state and ship reproducible installation examples."""

from __future__ import annotations

import json
import shutil
import subprocess
import tarfile
import tomllib
import zipfile
from pathlib import Path

from cgu import __version__
from cgu.interfaces.inquiry_cli import UVX_COMMAND

ROOT = Path(__file__).resolve().parents[1]
RELEASE_SOURCE = f"git+https://github.com/u9401066/creativity-generation-unit@v{__version__}"


def test_sdist_excludes_local_state_even_when_it_is_not_gitignored(tmp_path: Path) -> None:
    staging = tmp_path / "project"
    staging.mkdir()
    for name in ("pyproject.toml", "README.md", "LICENSE"):
        shutil.copy2(ROOT / name, staging / name)
    source = staging / "src" / "cgu"
    source.mkdir(parents=True)
    (source / "__init__.py").write_text(f'__version__ = "{__version__}"\n', encoding="utf-8")
    plugin = staging / "plugins" / "cgu"
    plugin.mkdir(parents=True)
    (plugin / "plugin.json").write_text('{"name":"cgu"}', encoding="utf-8")
    sentinels = [
        "data/.uv-cache/private.txt",
        ".asset-aware-mcp/assistant-assets.json",
        ".codex/skills/local/SKILL.md",
        ".vscode/mcp.json",
        "scratch_inquiry/result.txt",
        "evals/runs/private-session/events.jsonl",
    ]
    for name in sentinels:
        path = staging / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("local-only sentinel", encoding="utf-8")
    # No .gitignore: the packaging contract must protect arbitrary installed workspaces.
    uv = shutil.which("uv")
    assert uv is not None, "uv is required for the release packaging gate"
    out = tmp_path / "dist"
    result = subprocess.run(
        [uv, "build", "--directory", str(staging), "--out-dir", str(out)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    with tarfile.open(next(out.glob("*.tar.gz"))) as archive:
        paths = {
            Path(name).as_posix().split("/", 1)[1] for name in archive.getnames() if "/" in name
        }
    assert {"src/cgu/__init__.py", "plugins/cgu/plugin.json", "README.md"} <= paths
    assert not set(sentinels) & paths
    with zipfile.ZipFile(next(out.glob("*.whl"))) as archive:
        paths = set(archive.namelist())
    assert "cgu/__init__.py" in paths
    assert not any(name.startswith(("plugins/", "data/", ".codex/")) for name in paths)


def test_hook_fallback_and_installation_examples_pin_the_release() -> None:
    assert f"uvx --from {RELEASE_SOURCE} cgu inquiry hook" == UVX_COMMAND
    paths = ["plugins/cgu/mcp.json", "mcp-config/claude_desktop_config.json"]
    for name in paths:
        config = json.loads((ROOT / name).read_text(encoding="utf-8"))
        server = config["mcpServers"]["cgu"]
        assert server["args"] == ["--from", RELEASE_SOURCE, "cgu-server"]
        assert server["env"]["CGU_PROVIDER"] == "passthrough"
        assert "CGU_DATA_DIR" not in server["env"]
    for name in ("README.md", "README.zh-TW.md", "plugins/cgu/README.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert RELEASE_SOURCE in text and "creativity-generation-unit@master" not in text
    config = json.loads((ROOT / "mcp-config/vscode_mcp_settings.json").read_text(encoding="utf-8"))
    assert config["servers"]["cgu"]["env"] == {
        "CGU_PROVIDER": "passthrough",
        "CGU_EMBEDDING": "ngram",
    }
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert project["project"]["version"] == __version__
