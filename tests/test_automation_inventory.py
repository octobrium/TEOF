from __future__ import annotations

from tools.maintenance import automation_inventory as inventory


def test_autonomy_modules_have_entries() -> None:
    entries = inventory.generate_inventory(stale_days=None)
    modules = {entry.module for entry in entries}
    # Sanity check a few core automation modules are tracked
    assert "tools.autonomy.frontier" in modules
    assert "tools.autonomy.critic" in modules
    assert "tools.autonomy.tms" in modules


def test_inventory_payload_has_expected_fields() -> None:
    entries = inventory.generate_inventory(stale_days=None)
    payload = inventory.to_payload(entries, stale_days=None)
    assert "modules" in payload
    sample = payload["modules"][0]
    assert {"module", "path", "test_count", "receipt_count", "last_receipt", "stale"} <= sample.keys()
