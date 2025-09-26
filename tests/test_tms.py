from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.autonomy import tms


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


@pytest.fixture()
def temp_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path
    (root / "memory").mkdir(parents=True, exist_ok=True)
    (root / "_plans").mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(tms, "ROOT", root)
    monkeypatch.setattr(tms, "STATE_PATH", root / "memory" / "state.json")
    monkeypatch.setattr(tms, "PLANS_DIR", root / "_plans")
    return root


def test_detect_conflicting_facts(temp_repo: Path) -> None:
    write_json(
        tms.STATE_PATH,
        {
            "facts": [
                {
                    "id": "fact-1",
                    "statement": "Value A",
                    "layer": "L4",
                    "confidence": 0.9,
                    "source_run": "runA",
                },
                {
                    "id": "fact-1",
                    "statement": "Value B",
                    "layer": "L4",
                    "confidence": 0.8,
                    "source_run": "runB",
                },
                {
                    "id": "fact-2",
                    "statement": "Stable",
                    "layer": "L2",
                    "confidence": 0.95,
                },
            ]
        },
    )

    conflicts = tms.detect_conflicts()
    ids = [c["id"] for c in conflicts]
    assert "fact-1" in ids
    conflict = next(c for c in conflicts if c["id"] == "fact-1")
    assert "Value A" in conflict["statements"]
    assert "Value B" in conflict["statements"]


def test_low_confidence_fact(temp_repo: Path) -> None:
    write_json(
        tms.STATE_PATH,
        {
            "facts": [
                {
                    "id": "fact-low",
                    "statement": "Needs verification",
                    "layer": "L2",
                    "confidence": 0.3,
                }
            ]
        },
    )
    conflicts = tms.detect_conflicts()
    assert any(c["type"] == "low_confidence_fact" for c in conflicts)


def test_receipt_and_plan(temp_repo: Path, tmp_path: Path) -> None:
    write_json(
        tms.STATE_PATH,
        {
            "facts": [
                {
                    "id": "fact-plan",
                    "statement": "Version A",
                    "layer": "L4",
                    "confidence": 0.9,
                },
                {
                    "id": "fact-plan",
                    "statement": "Version B",
                    "layer": "L4",
                    "confidence": 0.8,
                },
            ]
        },
    )
    conflicts = tms.detect_conflicts()
    out_path = tms.write_receipt(conflicts, tmp_path / "tms.json")
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["conflicts"]
    assert payload["receipt_sha256"]

    plan_path = tms._emit_plan(conflicts[0], out_path)
    assert plan_path.exists()
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    assert plan["plan_id"].startswith("TMS-fact-plan")

    rendered = tms.render_table(conflicts)
    assert "fact-plan" in rendered
