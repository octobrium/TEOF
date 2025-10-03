from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.impact import case_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def test_build_summary_flags_missing_requirements(tmp_path: Path) -> None:
    case_dir = tmp_path / "_report" / "usage" / "case-study" / "demo"
    consent = {
        "captured_at": "2025-09-27T19:55:34Z",
        "partner": "demo-client",
    }
    _write_json(case_dir / "consent.json", consent)
    _write_json(
        case_dir / "conductor-dry-run-20250927T195724Z.json",
        {
            "generated_at": "2025-09-27T19:57:24Z",
            "guardrails": {"diff_limit": 200, "tests": ["pytest"]},
            "task": {"id": "ND-014", "title": "Relay offering pilot", "status": "pending"},
        },
    )

    summary = case_study.build_summary("demo", root=tmp_path)

    assert summary["slug"] == "demo"
    missing = summary["missing_requirements"]
    # live_runs and command_logs are absent in this fixture
    assert "live_runs" in missing
    assert "command_logs" in missing
    consent_items = summary["artifact_status"]["consent"]["items"]
    assert consent_items[0]["captured_at"] == "2025-09-27T19:55:34Z"


def test_write_summary_creates_file(tmp_path: Path) -> None:
    summary = {
        "generated_at": "2025-10-03T07:00:00Z",
        "slug": "demo",
        "artifact_status": {},
        "missing_requirements": [],
        "notes": [],
        "case_dir": "_report/usage/case-study/demo",
    }
    destination = tmp_path / "_report" / "usage" / "case-study" / "demo" / "summary.json"
    case_study.write_summary(summary, destination)
    stored = json.loads(destination.read_text(encoding="utf-8"))
    assert stored["slug"] == "demo"


def test_cli_summarize_writes_to_out(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    case_dir = tmp_path / "_report" / "usage" / "case-study" / "demo"
    _write_json(case_dir / "consent.json", {"captured_at": "2025-09-27T19:55:34Z"})
    _write_json(case_dir / "conductor-dry-run-20250927T195724Z.json", {"generated_at": "2025-09-27T19:57:24Z"})

    out_path = Path("_report/usage/case-study/demo/summary.json")
    rc = case_study.main(
        [
            "summarize",
            "--slug",
            "demo",
            "--out",
            str(out_path),
            "--root",
            str(tmp_path),
        ]
    )

    assert rc == 0
    captured = capsys.readouterr().out.strip()
    assert captured.startswith("wrote _report/usage/case-study/demo/summary.json")
    stored = json.loads((tmp_path / out_path).read_text(encoding="utf-8"))
    assert stored["slug"] == "demo"
