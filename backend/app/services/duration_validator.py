"""Duration validation & normalization (Feature 004).

Rules:
  * duration_minutes must be 1..1440
  * >720 and <=1440 requires confirmation flag True
  * >1440 invalid

Helpers:
  * validate_duration(duration, confirmation_flag) -> None (raises DurationValidationError)
  * compute_duration(start, end) -> int | None
  * normalize_duration(duration, start, end, confirmation_flag) -> (final_duration, confirmation_required_bool)
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Tuple


class DurationValidationError(ValueError):
    """Raised when duration validation fails."""


def validate_duration(duration_minutes: int, confirmation_flag: Optional[bool]) -> None:
    if duration_minutes <= 0:
        raise DurationValidationError("Duration must be > 0 minutes")
    if duration_minutes > 1440:
        raise DurationValidationError("Duration exceeds 24h (1440 minutes) cap; split into multiple logs")
    if duration_minutes > 720 and confirmation_flag is not True:
        raise DurationValidationError(
            "Duration greater than 12h requires explicit confirmation"
        )


def compute_duration(started_at: Optional[datetime], ended_at: Optional[datetime]) -> Optional[int]:
    """Compute duration minutes if both timestamps provided; return None otherwise.

    Rounds down to whole minutes.
    """
    if not started_at or not ended_at:
        return None
    if ended_at < started_at:
        # Negative durations not allowed; treat as invalid sentinel.
        raise DurationValidationError("ended_at precedes started_at")
    delta = ended_at - started_at
    minutes = int(delta.total_seconds() // 60)
    # Minimum of 1 minute if same-minute event
    return minutes if minutes >= 1 else 1


def normalize_duration(
    provided_duration: Optional[int],
    started_at: Optional[datetime],
    ended_at: Optional[datetime],
    confirmation_flag: Optional[bool],
) -> Tuple[Optional[int], bool]:
    """Return normalized duration and whether long-duration confirmation was required.

    If provided_duration is None and both timestamps exist, compute it.
    Validates duration and raises if invalid.
    Returns (duration_minutes | None, long_duration_required_bool).
    """
    duration = provided_duration
    if duration is None:
        duration = compute_duration(started_at, ended_at)
    if duration is None:
        return None, False

    long_required = duration > 720
    validate_duration(duration, confirmation_flag)
    return duration, long_required
