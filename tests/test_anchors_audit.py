from __future__ import annotations

import json
from pathlib import Path

from tools.governance import anchors_audit


def _write(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_audit_flags_missing_prev_hash(tmp_path: Path) -> None:
    anchors_payload = {
        "policy": "append-only",
        "events": [
            {"ts": "2025-01-01T00:00:00Z", "note": "initial"},
            {"ts": "2025-01-02T00:00:00Z", "note": "missing prev"},
            {
                "ts": "2025-01-03T00:00:00Z",
                "note": "has prev",
                "prev_content_hash": "abc123",
            },
        ],
    }
    anchors_path = tmp_path / "anchors.json"
    _write(anchors_path, anchors_payload)

    report = anchors_audit.audit_anchors(anchors_payload)
    assert report["event_count"] == 3
    assert report["issues"]["events_missing_prev_content_hash"] == [1]

    out_dir = tmp_path / "reports"
    written = anchors_audit.write_report(report, out_dir=out_dir)
    assert written.exists()
    written_payload = json.loads(written.read_text(encoding="utf-8"))
    assert written_payload["issues"]["events_missing_prev_content_hash"] == [1]


def test_cli_no_write(tmp_path: Path, capsys) -> None:
    anchors_payload = {
        "policy": "append-only",
        "events": [
            {"ts": "2025-02-01T00:00:00Z", "note": "init"},
        ],
    }
    anchors_path = tmp_path / "anchors.json"
    _write(anchors_path, anchors_payload)

    exit_code = anchors_audit.main([
        "--anchors",
        str(anchors_path),
        "--no-write",
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["event_count"] == 1
    assert data["issues"].get("events_missing_prev_content_hash", []) == []
