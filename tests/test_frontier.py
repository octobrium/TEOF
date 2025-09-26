from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.autonomy import frontier


@pytest.fixture()
def temp_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path
    (root / "_plans").mkdir(parents=True, exist_ok=True)
    (root / "agents" / "tasks").mkdir(parents=True, exist_ok=True)
    (root / "memory").mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(frontier, "ROOT", root)
    monkeypatch.setattr(frontier, "BACKLOG_PATH", root / "_plans" / "next-development.todo.json")
    monkeypatch.setattr(frontier, "TASKS_PATH", root / "agents" / "tasks" / "tasks.json")
    monkeypatch.setattr(frontier, "STATE_PATH", root / "memory" / "state.json")
    return root


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def test_frontier_scoring_orders_candidates(temp_repo: Path) -> None:
    write_json(
        frontier.BACKLOG_PATH,
        {
            "items": [
                {
                    "id": "ND-900",
                    "title": "Ship governance report",
                    "status": "pending",
                    "layer": "L4",
                    "priority": "high",
                    "receipts": ["docs/gov/report.md"],
                },
                {
                    "id": "ND-901",
                    "title": "Archive completed plan",
                    "status": "done",
                },
            ]
        },
    )
    write_json(
        frontier.TASKS_PATH,
        {
            "tasks": [
                {
                    "id": "QUEUE-200",
                    "title": "Refresh bus dashboard",
                    "status": "active",
                    "priority": "medium",
                    "receipts": ["_report/bus/dashboard.json"],
                    "role": "engineer",
                }
            ]
        },
    )
    write_json(
        frontier.STATE_PATH,
        {
            "facts": [
                {
                    "id": "fact-1",
                    "statement": "Objectives ledger needs rollout",
                    "layer": "L2",
                    "confidence": 0.6,
                    "source_run": "20250920T120000Z-abcd12",
                }
            ]
        },
    )

    entries = frontier.compute_frontier(limit=10)
    ids = [entry.candidate.identifier for entry in entries]
    assert ids[0] == "ND-900"
    assert "QUEUE-200" in ids
    assert "fact-1" in ids
    # Verify score ordering for first candidate
    assert entries[0].score >= entries[1].score


def test_frontier_receipt_writing(temp_repo: Path, tmp_path: Path) -> None:
    # Minimal data to produce a single entry
    write_json(
        frontier.BACKLOG_PATH,
        {
            "items": [
                {
                    "id": "ND-910",
                    "title": "Draft frontier doc",
                    "status": "pending",
                    "layer": "L5",
                }
            ]
        },
    )
    write_json(frontier.TASKS_PATH, {"tasks": []})
    write_json(frontier.STATE_PATH, {"facts": []})

    entries = frontier.compute_frontier(limit=5)
    out_path = frontier.write_receipt(entries, tmp_path / "receipt.json", limit=5)
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["parameters"]["limit"] == 5
    assert payload["entries"]
    assert payload["receipt_sha256"]
    assert payload["entries"][0]["id"] == "ND-910"

    rendered = frontier.render_table(entries)
    assert "ND-910" in rendered
