from app.services.severity_mapping import severity_label, impact_label, scale_bucket, ALL_BUCKETS, validate_scale
import pytest


def test_severity_label_boundaries():
    # Mild 1-3
    for n in range(1, 4):
        assert severity_label(n) == "Mild"
    # Moderate 4-6
    for n in range(4, 7):
        assert severity_label(n) == "Moderate"
    # Severe 7-8
    for n in range(7, 9):
        assert severity_label(n) == "Severe"
    # Critical 9-10
    for n in range(9, 11):
        assert severity_label(n) == "Critical"


def test_impact_label_same_mapping():
    for n in range(1, 11):
        assert impact_label(n) == severity_label(n)


def test_scale_bucket():
    for b in ALL_BUCKETS:
        for n in range(b.low, b.high + 1):
            name, low, high = scale_bucket(n)
            assert name == b.name
            assert low == b.low and high == b.high


def test_validate_scale_out_of_range():
    for bad in [-1, 0, 11, 99]:
        with pytest.raises(ValueError):
            validate_scale(bad)
