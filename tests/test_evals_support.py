"""evals 測試共用設定：讓 `import evals` 可用，並提供建立假 run 目錄的小工具。"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def read_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def make_cell(
    run_dir: Path,
    condition: str,
    model: str,
    task_id: str,
    answer: str,
    *,
    repeat: int = 0,
    domain: str = "medical_research",
    **extra: Any,
) -> Path:
    from evals.common import repeat_dirname, slug

    cell_dir = run_dir / condition / slug(model) / repeat_dirname(task_id, repeat)
    cell_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "condition": condition,
        "model": model,
        "task_id": task_id,
        "domain": domain,
        "repeat": repeat,
        "status": "ok",
        "answer_chars": len(answer),
        **extra,
    }
    (cell_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    (cell_dir / "answer.md").write_text(answer + "\n", encoding="utf-8")
    (cell_dir / "prompt.txt").write_text(f"提示:{task_id}", encoding="utf-8")
    return cell_dir


def write_run_json(run_dir: Path, **extra: Any) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    data = {"run_id": run_dir.name, "suite": "missing-suite.json", "models": [], **extra}
    (run_dir / "run.json").write_text(json.dumps(data), encoding="utf-8")
