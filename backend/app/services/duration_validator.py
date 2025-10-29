"""Duration validation logic (Feature 004).

Rules:
  - duration_minutes must be 1..1440
  - >720 and <=1440 requires confirmation flag True
  - >1440 invalid
"""

from __future__ import annotations

from typing import Optional

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
