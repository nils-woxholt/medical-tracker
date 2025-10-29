from app.services.duration_validator import validate_duration, compute_duration, normalize_duration, DurationValidationError
import pytest
from datetime import datetime, timedelta, timezone

TZ = timezone.utc


def test_compute_duration_minutes_rounds_down():
    start = datetime(2025, 10, 29, 10, 0, tzinfo=TZ)
    end = datetime(2025, 10, 29, 11, 30, 30, tzinfo=TZ)  # 90m 30s -> floor to 90
    minutes = compute_duration(start, end)
    assert minutes == 90


def test_normalize_duration_requires_confirmation_over_720():
    start = datetime(2025, 10, 29, 0, 0, tzinfo=TZ)
    end = start + timedelta(minutes=800)
    normalized, needs_confirm = normalize_duration(
        provided_duration=None,
        started_at=start,
        ended_at=end,
        confirmation_flag=True,
    )
    assert normalized == 800
    assert needs_confirm is True


def test_normalize_duration_with_provided_duration_precedence():
    start = datetime(2025, 10, 29, 0, 0, tzinfo=TZ)
    end = start + timedelta(minutes=15)
    normalized, needs_confirm = normalize_duration(
        provided_duration=10,
        started_at=start,
        ended_at=end,
        confirmation_flag=False,
    )
    assert normalized == 10
    assert needs_confirm is False


def test_validate_duration_accepts_range_and_confirmation_flag():
    # within range
    validate_duration(1, confirmation_flag=False)
    validate_duration(720, confirmation_flag=False)
    # above 720 needs flag
    with pytest.raises(DurationValidationError):
        validate_duration(721, confirmation_flag=False)
    validate_duration(721, confirmation_flag=True)
    # max boundary (still needs confirmation flag)
    validate_duration(1440, confirmation_flag=True)
    # above max rejects
    with pytest.raises(DurationValidationError):
        validate_duration(1441, confirmation_flag=True)
