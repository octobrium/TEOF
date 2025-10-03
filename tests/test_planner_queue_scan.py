import json
from pathlib import Path

import pytest

from tools.planner import queue_scan
from tools.planner import queue_warnings


@pytest.fixture
def summary_repo(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    summary_dir = root / "_report" / "planner" / "validate"
    summary_dir.mkdir(parents=True)
    summary_payload = {
        "generated_at": "2025-10-03T06:00:00Z",
        "strict": True,
        "exit_code": 0,
        "plans": [
            {
                "path": "_plans/example.plan.json",
                "ok": True,
                "errors": [],
                "plan_id": "PLAN-XYZ",
                "queue_warnings": [
                    {
                        "plan_id": "PLAN-XYZ",
                        "queue_ref": "queue/030-test.md",
                        "issue": "ocers_mismatch",
                        "message": "PLAN-XYZ ocers mismatch",
                    }
                ],
            }
        ],
    }
    (summary_dir / "summary-latest.json").write_text(
        json.dumps(summary_payload, indent=2),
        encoding="utf-8",
    )
    monkeypatch.setattr(queue_scan, "ROOT", root)
    monkeypatch.setattr(queue_warnings, "ROOT", root)
    return root


def test_queue_scan_writes_markdown(summary_repo, tmp_path, capsys):
    out_path = tmp_path / "custom.md"
    rc = queue_scan.main(["--format", "markdown", "--out", str(out_path)])
    assert rc == 0
    content = out_path.read_text(encoding="utf-8")
    assert "Planner Queue Warning Scan" in content
    assert "PLAN-XYZ" in content
    printed = capsys.readouterr().out
    assert str(out_path) in printed


def test_queue_scan_fail_on_warning(summary_repo):
    rc = queue_scan.main(["--fail-on-warning", "--format", "json"])
    assert rc == 1
    default_dir = queue_scan.ROOT / "_report" / "planner" / "queue-warnings"
    files = list(default_dir.glob("scan-*.json"))
    assert files
    data = json.loads(files[-1].read_text(encoding="utf-8"))
    assert data["warnings"]
