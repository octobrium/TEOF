from __future__ import annotations

from tools.maintenance import capability_inventory as inventory


def test_brief_command_has_tests() -> None:
    entries = inventory.generate_inventory(stale_days=None)
    brief = next(item for item in entries if item.name == "brief")
    assert brief.module_path.exists()
    assert brief.tests  # expecting brief command to be covered by tests


def test_inventory_payload_contains_all_commands() -> None:
    entries = inventory.generate_inventory(stale_days=None)
    names = {item.name for item in entries}
    assert set(inventory.COMMAND_MODULES).issubset(names)


def test_ttd_trend_receipt_detected() -> None:
    entries = inventory.generate_inventory(stale_days=None)
    trend = next(item for item in entries if item.name == "ttd_trend")
    assert trend.receipt_paths
