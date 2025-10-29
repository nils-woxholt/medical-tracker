"""Severity / impact mapping utilities (Feature 004).

Provides consistent categorical labels for numeric severity/impact (1..10).
Rules (spec):
 1-3  -> Mild
 4-6  -> Moderate
 7-8  -> Severe
 9-10 -> Critical

Exposed helpers:
  * severity_label(n) / impact_label(n)
  * validate_scale(n) -> None (raises ValueError if out of range)
  * scale_bucket(n) -> tuple(category, lower_bound, upper_bound)
  * ALL_BUCKETS constant for tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple


@dataclass(frozen=True)
class Bucket:
    name: str
    low: int
    high: int


ALL_BUCKETS: List[Bucket] = [
    Bucket("Mild", 1, 3),
    Bucket("Moderate", 4, 6),
    Bucket("Severe", 7, 8),
    Bucket("Critical", 9, 10),
]


def validate_scale(n: int) -> None:
    if n < 1 or n > 10:
        raise ValueError("numeric value must be between 1 and 10")


def _label(n: int) -> str:
    validate_scale(n)
    for b in ALL_BUCKETS:
        if b.low <= n <= b.high:
            return b.name
    # unreachable due to buckets covering 1..10
    raise RuntimeError("No bucket matched numeric value")


def severity_label(n: int) -> str:
    return _label(n)


def impact_label(n: int) -> str:
    return _label(n)


def scale_bucket(n: int) -> Tuple[str, int, int]:
    """Return (category, low, high) for provided numeric value."""
    validate_scale(n)
    for b in ALL_BUCKETS:
        if b.low <= n <= b.high:
            return b.name, b.low, b.high
    raise RuntimeError("Bucket not found")

