from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.autonomy import critic


@pytest.fixture()
def temp_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path
    (root / "_plans").mkdir(parents=True, exist_ok=True)
    (root / "memory").mkdir(parents=True, exist_ok=True)
    (root / "_bus" / "claims").mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(critic, "ROOT", root)
    monkeypatch.setattr(critic, "BACKLOG_PATH", root / "_plans" / "next-development.todo.json")
    monkeypatch.setattr(critic, "STATE_PATH", root / "memory" / "state.json")
    monkeypatch.setattr(critic, "CLAIMS_DIR", root / "_bus" / "claims")
    return root


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def test_detects_missing_receipts(temp_repo: Path) -> None:
    write_json(
        critic.BACKLOG_PATH,
        {
            "items": [
                {"id": "ND-200", "title": "Needs receipts", "status": "pending", "layer": "L5"},
                {"id": "ND-201", "status": "pending", "receipts": ["docs/example.md"]},
            ]
        },
    )
    write_json(critic.STATE_PATH, {"facts": []})

    anomalies = critic.detect_anomalies()
    ids = [a["id"] for a in anomalies]
    assert "ND-200" in ids
    assert all(a["type"] == "missing_receipts" for a in anomalies if a["id"] == "ND-200")


def test_detects_low_confidence_facts(temp_repo: Path) -> None:
    write_json(critic.BACKLOG_PATH, {"items": []})
    write_json(
        critic.STATE_PATH,
        {
            "facts": [
                {"id": "fact-1", "statement": "Low confidence", "layer": "L2", "confidence": 0.4},
                {"id": "fact-2", "confidence": 0.9},
            ]
        },
    )

    anomalies = critic.detect_anomalies()
    assert any(a["type"] == "low_confidence_fact" and a["id"] == "fact-1" for a in anomalies)
    assert all(a["id"] != "fact-2" for a in anomalies)


def test_receipt_and_emit_bus(temp_repo: Path, tmp_path: Path) -> None:
    write_json(
        critic.BACKLOG_PATH,
        {
            "items": [
                {"id": "ND-300", "title": "Repair this", "status": "pending", "layer": "L5"}
            ]
        },
    )
    write_json(critic.STATE_PATH, {"facts": []})

    anomalies = critic.detect_anomalies()
    out_path = critic.write_receipt(anomalies, tmp_path / "critic.json")
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["anomalies"]
    assert payload["receipt_sha256"]

    claim_path = critic._emit_bus_claim(anomalies[0], out_path)
    assert claim_path.exists()
    claim = json.loads(claim_path.read_text(encoding="utf-8"))
    assert claim["receipt"].endswith("critic.json")

    table = critic.render_table(anomalies)
    assert "ND-300" in table
