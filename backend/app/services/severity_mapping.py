"""Severity / impact mapping utilities (Feature 004)."""

from __future__ import annotations

def severity_label(n: int) -> str:
    if n <= 3:
        return "Mild"
    if n <= 6:
        return "Moderate"
    if n <= 8:
        return "Severe"
    return "Critical"


impact_label = severity_label  # same scale mapping
