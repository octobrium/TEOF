from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from tools.memory import gap_audit


def _write_memory_log(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(entry) for entry in entries]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_plan(path: Path, plan_id: str, created: str, receipts: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "plan_id": plan_id,
        "created": created,
        "status": "done",
        "steps": [
            {
                "id": "S1",
                "title": "demo",
                "status": "done",
                "receipts": receipts,
            }
        ],
        "receipts": [],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _setup_repo(
    repo: Path,
    monkeypatch,
    *,
    recorded_created: str = "2025-10-02T00:00:00Z",
    missing_created: str = "2025-10-03T00:00:00Z",
    fake_now: str | None = None,
) -> Path:
    _write_memory_log(
        repo / "memory" / "log.jsonl",
        [
            {
                "ts": "2025-10-01T00:00:00Z",
                "actor": "codex",
                "ref": "plan:demo-recorded",
                "artifacts": ["_report/demo/receipt.json"],
            }
        ],
    )
    plans_dir = repo / "_plans"
    plans_dir.mkdir(parents=True, exist_ok=True)
    _write_plan(plans_dir / "demo-recorded.plan.json", "demo-recorded", recorded_created, ["_report/demo/receipt.json"])
    _write_plan(plans_dir / "demo-missing.plan.json", "demo-missing", missing_created, ["_report/demo/missing.json"])

    out_path = repo / "_report" / "analysis" / "memory-gap" / "latest.json"
    monkeypatch.setattr(gap_audit, "ROOT", repo)
    monkeypatch.setattr(gap_audit, "MEMORY_LOG", repo / "memory" / "log.jsonl")
    monkeypatch.setattr(gap_audit, "PLANS_DIR", plans_dir)
    monkeypatch.setattr(gap_audit, "DEFAULT_OUT", out_path)

    if fake_now:
        target_dt = datetime.fromisoformat(fake_now.replace("Z", "+00:00"))

        class FakeDateTime(datetime):
            @classmethod
            def utcnow(cls) -> datetime:
                return target_dt

        monkeypatch.setattr(gap_audit, "datetime", FakeDateTime)
    return out_path


def test_gap_audit_marks_missing(tmp_path: Path, monkeypatch) -> None:
    out_path = _setup_repo(tmp_path, monkeypatch)
    result = gap_audit.main(["--since", "2025-10-01T00:00:00Z"])
    assert result == 0
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["total"] == 2
    missing = payload["missing"]
    assert len(missing) == 1
    assert missing[0]["plan_id"] == "demo-missing"


def test_gap_audit_respects_window_hours(tmp_path: Path, monkeypatch) -> None:
    out_path = _setup_repo(
        tmp_path,
        monkeypatch,
        recorded_created="2025-10-09T12:00:00Z",
        missing_created="2025-10-08T00:00:00Z",
        fake_now="2025-10-10T00:00:00Z",
    )
    result = gap_audit.main(["--window-hours", "24"])
    assert result == 0
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["total"] == 1
    assert payload["entries"][0]["plan_id"] == "demo-recorded"


def test_gap_audit_fail_on_missing(tmp_path: Path, monkeypatch) -> None:
    _setup_repo(tmp_path, monkeypatch)
    result = gap_audit.main(["--fail-on-missing"])
    assert result == 1


def test_run_audit_helper(tmp_path: Path, monkeypatch) -> None:
    out_path = _setup_repo(tmp_path, monkeypatch)
    summary, written = gap_audit.run_audit("2025-10-01T00:00:00Z", None, None, out_path)
    assert written == out_path
    assert summary["total"] == 2
    assert len(summary["missing"]) == 1
