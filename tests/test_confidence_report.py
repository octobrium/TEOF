from __future__ import annotations

import json
from pathlib import Path

from tools.agent import confidence_report


def write_entry(path: Path, *, ts: str, agent: str, confidence: float, note: str | None = None) -> None:
    payload: dict[str, object] = {"ts": ts, "agent": agent, "confidence": confidence}
    if note:
        payload["note"] = note
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload) + "\n")


def test_confidence_report_table(tmp_path: Path, capsys) -> None:
    log_dir = tmp_path / "_report" / "agent" / "codex-4"
    log_dir.mkdir(parents=True)
    log_path = log_dir / "confidence.jsonl"

    write_entry(log_path, ts="2025-10-06T20:00:00Z", agent="codex-4", confidence=0.6)
    write_entry(log_path, ts="2025-10-06T21:00:00Z", agent="codex-4", confidence=0.95, note="ttd trend")

    rc = confidence_report.main([
        "--agent",
        "codex-4",
        "--dir",
        str(tmp_path / "_report" / "agent"),
        "--warn-threshold",
        "0.9",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Total entries: 2" in out
    assert "Entries ≥ 0.90: 1" in out
    assert "warning" in out.lower()


def test_confidence_report_json(tmp_path: Path, capsys) -> None:
    log_dir = tmp_path / "_report" / "agent" / "codex-4"
    log_dir.mkdir(parents=True)
    log_path = log_dir / "confidence.jsonl"

    write_entry(log_path, ts="2025-10-06T20:00:00Z", agent="codex-4", confidence=0.2)

    rc = confidence_report.main([
        "--agent",
        "codex-4",
        "--dir",
        str(tmp_path / "_report" / "agent"),
        "--format",
        "json",
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["count"] == 1
    assert abs(data["average"] - 0.2) < 1e-9
