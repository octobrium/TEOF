from __future__ import annotations

import json
from pathlib import Path

from tools.autonomy import macro_hygiene


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_compute_status_reports_attention(tmp_path, monkeypatch, capsys):
    root = tmp_path
    plan_ready = root / "_plans" / "ready.plan.json"
    plan_ready.parent.mkdir(parents=True, exist_ok=True)
    _write(plan_ready, {"status": "done"})

    ready_file = root / "tools" / "demo.py"
    ready_file.parent.mkdir(parents=True, exist_ok=True)
    ready_file.write_text("# demo\n", encoding="utf-8")

    config = root / "docs" / "maintenance" / "macro-hygiene.objectives.json"
    _write(
        config,
        {
            "version": 1,
            "objectives": [
                {
                    "id": "ready",
                    "title": "Ready objective",
                    "checks": [
                        {"kind": "plan_done", "path": "_plans/ready.plan.json"},
                        {"kind": "path_exists", "path": "tools/demo.py"},
                    ],
                },
                {
                    "id": "attention",
                    "title": "Attention objective",
                    "checks": [{"kind": "plan_done", "path": "_plans/missing.plan.json"}],
                },
            ],
        },
    )

    receipt_path = root / "_report" / "usage" / "macro-hygiene-status.json"

    monkeypatch.setattr(macro_hygiene, "ROOT", root)
    monkeypatch.setattr(macro_hygiene, "CONFIG_PATH", config)
    monkeypatch.setattr(macro_hygiene, "DEFAULT_RECEIPT", receipt_path)

    status = macro_hygiene.compute_status(root=root)
    assert status["summary"]["ready"] == 1
    assert status["summary"]["attention"] == 1
    assert any(obj["id"] == "attention" and obj["status"] == "attention" for obj in status["objectives"])

    exit_code = macro_hygiene.main(["--human"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Macro hygiene objectives" in out
    assert receipt_path.exists()
    receipt_data = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt_data["summary"]["total"] == 2


def test_optional_checks_keep_ready(tmp_path, monkeypatch):
    root = tmp_path
    config = root / "docs" / "maintenance" / "macro-hygiene.objectives.json"
    _write(
        config,
        {
            "version": 1,
            "objectives": [
                {
                    "id": "optional-demo",
                    "title": "Optional demo",
                    "checks": [
                        {"kind": "path_exists", "path": "tools/required.py"},
                        {"kind": "path_exists", "path": "tools/optional.py", "optional": True},
                    ],
                }
            ],
        },
    )
    required = root / "tools" / "required.py"
    required.parent.mkdir(parents=True, exist_ok=True)
    required.write_text("# required\n", encoding="utf-8")

    monkeypatch.setattr(macro_hygiene, "ROOT", root)
    monkeypatch.setattr(macro_hygiene, "CONFIG_PATH", config)
    receipt = root / "_report" / "usage" / "macro-hygiene-status.json"
    monkeypatch.setattr(macro_hygiene, "DEFAULT_RECEIPT", receipt)

    status = macro_hygiene.compute_status(root=root)
    assert status["status"] == "ready"
    obj = status["objectives"][0]
    assert obj["optional_failures"]
    assert obj["optional_failures"][0]["path"] == "tools/optional.py"

    # Strict mode should mark the objective as attention.
    exit_code = macro_hygiene.main(["--strict", "--no-write"])
    assert exit_code == 0
