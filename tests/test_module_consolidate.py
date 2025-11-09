from __future__ import annotations

import json
from pathlib import Path

from tools.autonomy import module_consolidate


def test_inventory_json(capsys) -> None:
    rc = module_consolidate.main(["inventory", "--format", "json"])
    assert rc == 0
    output = capsys.readouterr().out.strip()
    data = json.loads(output)
    assert data["services"]
    coordination = next(item for item in data["services"] if item["service"] == "coordination")
    assert coordination["module_count"] >= len(coordination["modules"])


def test_plan_apply_telemetry(tmp_path: Path) -> None:
    receipt_dir = tmp_path / "receipts"
    plan_path = tmp_path / "plan.json"
    rc = module_consolidate.main(
        [
            "plan",
            "--out",
            str(plan_path),
            "--service",
            "coordination",
            "--receipt-dir",
            str(receipt_dir),
        ]
    )
    assert rc == 0
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    assert plan["services"][0]["service"] == "coordination"

    rc = module_consolidate.main(["apply", "--plan", str(plan_path), "--dry-run"])
    assert rc == 0
    apply_receipt = plan_path.with_suffix(".json.apply.json")
    assert apply_receipt.exists()

    telemetry_path = tmp_path / "telemetry.json"
    rc = module_consolidate.main(
        [
            "telemetry",
            "--out",
            str(telemetry_path),
            "--receipt-dir",
            str(receipt_dir),
        ]
    )
    assert rc == 0
    telemetry = json.loads(telemetry_path.read_text(encoding="utf-8"))
    assert telemetry["services"]
    pointer = receipt_dir / "telemetry-latest.json"
    assert pointer.exists()

    # Guard validation succeeds even if plan services ⊂ telemetry services
    rc = module_consolidate.main(["guard", "--receipt-dir", str(receipt_dir)])
    assert rc == 0

    # Test guard detects missing plan pointer but can fall back to explicit receipts
    (receipt_dir / "plan-latest.json").unlink()
    rc = module_consolidate.main(["guard", "--receipt-dir", str(receipt_dir)])
    assert rc == 1
    rc = module_consolidate.main(
        [
            "guard",
            "--plan-receipt",
            str(plan_path),
            "--telemetry-receipt",
            str(telemetry_path),
            "--max-age-hours",
            "1000",
        ]
    )
    assert rc == 0
