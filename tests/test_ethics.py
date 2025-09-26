from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.autonomy import ethics_gate


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def test_detects_high_risk_without_guard(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ethics_gate, "ROOT", tmp_path)
    monkeypatch.setattr(ethics_gate, "BACKLOG_PATH", tmp_path / "_plans" / "next-development.todo.json")
    monkeypatch.setattr(ethics_gate, "TASKS_PATH", tmp_path / "agents" / "tasks" / "tasks.json")
    (ethics_gate.BACKLOG_PATH.parent).mkdir(parents=True, exist_ok=True)
    (ethics_gate.TASKS_PATH.parent).mkdir(parents=True, exist_ok=True)

    write_json(
        ethics_gate.BACKLOG_PATH,
        {
            "items": [
                {"id": "ND-500", "title": "High-risk without consent", "layer": "L6"},
                {"id": "ND-501", "title": "Has consent", "systemic_scale": 9, "receipts": ["docs/consent/permit.md"]},
            ]
        },
    )
    write_json(ethics_gate.TASKS_PATH, {"tasks": []})

    violations = ethics_gate.detect_violations()
    ids = [v["id"] for v in violations]
    assert "ND-500" in ids
    assert "ND-501" not in ids


def test_receipt_and_bus_emission(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path
    (root / "_plans").mkdir(parents=True, exist_ok=True)
    (root / "agents" / "tasks").mkdir(parents=True, exist_ok=True)
    (root / "_bus" / "claims").mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(ethics_gate, "ROOT", root)
    monkeypatch.setattr(ethics_gate, "BACKLOG_PATH", root / "_plans" / "next-development.todo.json")
    monkeypatch.setattr(ethics_gate, "TASKS_PATH", root / "agents" / "tasks" / "tasks.json")
    monkeypatch.setattr(ethics_gate, "CLAIMS_DIR", root / "_bus" / "claims")

    write_json(
        ethics_gate.BACKLOG_PATH,
        {
            "items": [
                {"id": "ND-600", "title": "Needs consent", "systemic_scale": 8}
            ]
        },
    )
    write_json(ethics_gate.TASKS_PATH, {"tasks": []})

    violations = ethics_gate.detect_violations()
    receipt_path = ethics_gate.write_receipt(violations, root / "receipt.json")
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert payload["violations"]
    assert payload["receipt_sha256"]

    claim_path = ethics_gate._emit_bus_claim(violations[0], receipt_path)
    claim = json.loads(claim_path.read_text(encoding="utf-8"))
    assert claim["receipt"].endswith("receipt.json")

    table = ethics_gate.render_table(violations)
    assert "ND-600" in table
