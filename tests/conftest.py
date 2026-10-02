"""Fixtures for the CGU tests."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from cgu_support import make_open_cgu


@pytest.fixture
def open_cgu(tmp_path: Path) -> Callable[..., Any]:
    return make_open_cgu(tmp_path)
