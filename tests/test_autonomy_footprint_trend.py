from __future__ import annotations

from teof import status_report


def test_detect_sustained_autonomy_growth_positive():
    baseline = {"module_files": 10, "loc": 1000, "helper_defs": 50}
    entries = [
        {"generated_at": "2025-10-01T00:00:00Z", "module_files": 11, "loc": 1010, "helper_defs": 51},
        {"generated_at": "2025-10-02T00:00:00Z", "module_files": 12, "loc": 1025, "helper_defs": 52},
        {"generated_at": "2025-10-03T00:00:00Z", "module_files": 13, "loc": 1035, "helper_defs": 53},
    ]
    assert status_report.detect_sustained_autonomy_growth(entries, baseline)


def test_detect_sustained_autonomy_growth_negative():
    baseline = {"module_files": 10, "loc": 1000, "helper_defs": 50}
    entries = [
        {"generated_at": "2025-10-01T00:00:00Z", "module_files": 11, "loc": 1005, "helper_defs": 51},
        {"generated_at": "2025-10-02T00:00:00Z", "module_files": 11, "loc": 1004, "helper_defs": 52},
        {"generated_at": "2025-10-03T00:00:00Z", "module_files": 12, "loc": 1006, "helper_defs": 52},
    ]
    assert not status_report.detect_sustained_autonomy_growth(entries, baseline)


def test_detect_sustained_autonomy_growth_requires_baseline():
    entries = [
        {"generated_at": "2025-10-01T00:00:00Z", "module_files": 11, "loc": 1010, "helper_defs": 51},
        {"generated_at": "2025-10-02T00:00:00Z", "module_files": 12, "loc": 1025, "helper_defs": 52},
        {"generated_at": "2025-10-03T00:00:00Z", "module_files": 13, "loc": 1035, "helper_defs": 53},
    ]
    assert not status_report.detect_sustained_autonomy_growth(entries, None)
