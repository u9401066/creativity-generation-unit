"""統計工具：Wilson 區間、Cohen's kappa 等（僅標準函式庫）。"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Iterable, Sequence

Z95 = 1.959963984540054


def wilson_interval(successes: float, n: int, z: float = Z95) -> tuple[float, float] | None:
    """二項比例的 Wilson 區間；n == 0 時回傳 None。

    successes 允許小數（例如把平手計為 0.5 時），此時區間只是近似。
    """
    if n <= 0:
        return None
    if successes < 0 or successes > n:
        raise ValueError("successes 必須介於 0 與 n 之間")
    p = successes / n
    z2 = z * z
    denom = 1.0 + z2 / n
    centre = (p + z2 / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def proportion(successes: float, n: int) -> float | None:
    return successes / n if n > 0 else None


def mean(values: Iterable[float]) -> float | None:
    vals = list(values)
    return sum(vals) / len(vals) if vals else None


def median(values: Iterable[float]) -> float | None:
    vals = sorted(values)
    if not vals:
        return None
    mid = len(vals) // 2
    return vals[mid] if len(vals) % 2 else (vals[mid - 1] + vals[mid]) / 2


def cohen_kappa(pairs: Sequence[tuple[str, str]]) -> float | None:
    """兩位評審對同一批項目的 Cohen's kappa；無資料或期望一致率為 1 時回傳 None。"""
    n = len(pairs)
    if n == 0:
        return None
    observed = sum(1 for a, b in pairs if a == b) / n
    ca = Counter(a for a, _ in pairs)
    cb = Counter(b for _, b in pairs)
    expected = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    if math.isclose(expected, 1.0):
        return None
    return (observed - expected) / (1 - expected)


def fmt_rate(value: float | None, digits: int = 1) -> str:
    return "n/a" if value is None else f"{value * 100:.{digits}f}%"


def fmt_interval(interval: tuple[float, float] | None) -> str:
    if interval is None:
        return "n/a"
    return f"[{interval[0] * 100:.1f}%, {interval[1] * 100:.1f}%]"
