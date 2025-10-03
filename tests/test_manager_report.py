import json
from pathlib import Path
from typing import Any

import pytest

from tools.agent import manager_report, bus_event, bus_status


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = tmp_path
    events_dir = root / "_bus" / "events"
    messages_dir = root / "_bus" / "messages"
    assignments_dir = root / "_bus" / "assignments"
    claims_dir = root / "_bus" / "claims"
    usage_dir = root / "_report" / "usage"

    events_dir.mkdir(parents=True)
    messages_dir.mkdir(parents=True)
    assignments_dir.mkdir(parents=True)
    claims_dir.mkdir(parents=True)
    usage_dir.mkdir(parents=True)
    (root / "agents").mkdir()
    (root / "_report" / "manager").mkdir(parents=True)

    tasks_path = root / "agents" / "tasks" / "tasks.json"
    tasks_path.parent.mkdir(parents=True, exist_ok=True)
    tasks_path.write_text(json.dumps({"tasks": []}), encoding="utf-8")

    monkeypatch.setattr(manager_report, "ROOT", root)
    monkeypatch.setattr(manager_report, "ASSIGN_DIR", assignments_dir)
    monkeypatch.setattr(manager_report, "CLAIMS_DIR", claims_dir)
    monkeypatch.setattr(manager_report, "MESSAGES_DIR", messages_dir)
    monkeypatch.setattr(manager_report, "REPORT_DIR", root / "_report" / "manager")
    monkeypatch.setattr(manager_report, "TASKS_FILE", tasks_path)

    event_log = events_dir / "events.jsonl"
    monkeypatch.setattr(bus_event, "ROOT", root)
    monkeypatch.setattr(bus_event, "EVENT_LOG", event_log)
    manifest_path = root / "AGENT_MANIFEST.json"
    manifest_path.write_text(
        json.dumps({"agent_id": "codex-manager", "desired_roles": ["manager"]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(bus_event, "MANIFEST_PATH", manifest_path)

    monkeypatch.setattr(bus_status, "ROOT", root)
    monkeypatch.setattr(bus_status, "CLAIMS_DIR", claims_dir)
    monkeypatch.setattr(bus_status, "EVENT_LOG", event_log)
    monkeypatch.setattr(bus_status, "ASSIGNMENTS_DIR", assignments_dir)
    monkeypatch.setattr(bus_status, "MANIFEST_PATTERN", "AGENT_MANIFEST.json")

    auth_json = usage_dir / "external-authenticity.json"
    auth_md = usage_dir / "external-authenticity.md"
    auth_json.write_text(
        json.dumps(
            {
                "total_feeds": 1,
                "overall_avg_trust": 0.92,
                "tiers": [
                    {
                        "tier": "primary_truth",
                        "weight": 1.0,
                        "feed_count": 1,
                        "avg_adjusted_trust": 0.92,
                    }
                ],
                "attention_feeds": [],
            }
        ),
        encoding="utf-8",
    )
    auth_md.write_text(
        "# External Authenticity Dashboard\n\n- Overall adjusted trust: 0.92\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(manager_report, "AUTH_JSON", auth_json)
    monkeypatch.setattr(manager_report, "AUTH_MD", auth_md)

    summary_dir = root / "_report" / "planner" / "validate"
    summary_dir.mkdir(parents=True, exist_ok=True)
    summary_payload = {
        "generated_at": "2025-09-21T00:30:00Z",
        "strict": True,
        "exit_code": 0,
        "plans": [
            {
                "path": "_plans/sample.plan.json",
                "ok": True,
                "errors": [],
                "plan_id": "PLAN-002",
                "queue_warnings": [
                    {
                        "plan_id": "PLAN-002",
                        "queue_ref": "queue/999-sync.md",
                        "issue": "layer_mismatch",
                        "message": "PLAN-002 layer mismatch with queue/999-sync.md",
                    }
                ],
            }
        ],
    }
    (summary_dir / "summary-latest.json").write_text(
        json.dumps(summary_payload, indent=2),
        encoding="utf-8",
    )

    return root


def test_manager_report_writes_file(repo: Path):
    report_dir = repo / "_report" / "manager"
    rc = manager_report.main(["--manager", "codex-manager"])
    assert rc == 0
    reports = list(report_dir.glob("manager-report-*.md"))
    assert reports, "manager report file should be created"
    latest = sorted(reports)[-1]
    content = latest.read_text(encoding="utf-8")
    assert "Planner Queue Warnings" in content
    assert "PLAN-002" in content


def test_manager_report_logs_heartbeat(repo: Path):
    events_path = repo / "_bus" / "events" / "events.jsonl"
    rc = manager_report.main([
        "--manager",
        "codex-manager",
        "--log-heartbeat",
        "--heartbeat-summary",
        "codex-manager heartbeat",
        "--heartbeat-shift",
        "mid",
    ])
    assert rc == 0
    entries = [
        json.loads(line)
        for line in events_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    heartbeat = next(
        entry
        for entry in entries
        if entry.get("agent_id") == "codex-manager" and entry.get("summary") == "codex-manager heartbeat"
    )
    assert heartbeat.get("shift") == "mid"


def test_manager_report_bus_status_roundtrip(repo: Path, capsys):
    rc = manager_report.main([
        "--manager",
        "codex-manager",
        "--log-heartbeat",
        "--heartbeat-summary",
        "codex-manager heartbeat",
        "--heartbeat-shift",
        "mid",
    ])
    assert rc == 0
    capsys.readouterr()

    out_rc = bus_status.main(["--preset", "manager", "--limit", "5", "--json"])
    assert out_rc == 0
    payload = json.loads(capsys.readouterr().out)
    active = payload["manager_status"].get("active", [])
    assert active and active[0]["summary"] == "codex-manager heartbeat"
    assert active[0]["meta"].get("shift") == "mid"


def test_manager_report_includes_metrics(repo: Path):
    metrics_dir = repo / "_report" / "reconciliation" / "sample"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    metrics_file = metrics_dir / "metrics.jsonl"
    metrics_file.write_text(
        "\n".join(
            [
                json.dumps({
                    "matches": True,
                    "difference_count": 0,
                    "missing_receipt_count": 0,
                    "capability_diff_count": 0,
                }),
                json.dumps({
                    "matches": False,
                    "difference_count": 2,
                    "missing_receipt_count": 1,
                    "capability_diff_count": 1,
                }),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    rc = manager_report.main([
        "--manager",
        "codex-manager",
        "--include-metrics",
        "--metrics-dir",
        str(metrics_dir),
    ])
    assert rc == 0
    report_path = sorted((repo / "_report" / "manager").glob("manager-report-*.md"))[-1]
    content = report_path.read_text(encoding="utf-8")
    assert "Reconciliation Metrics" in content
    assert "Differences: 2" in content


def test_manager_report_includes_plan_validation_issues(repo: Path):
    report_dir = repo / "_report" / "manager"
    report_dir.mkdir(parents=True, exist_ok=True)

    def fake_plan_issues() -> list[dict[str, Any]]:
        return [
            {
                "plan": "_plans/2025-10-10-test.plan.json",
                "errors": ["layer must be one of L0-L6"],
            }
        ]

    original = manager_report.collect_plan_validation_issues
    manager_report.collect_plan_validation_issues = fake_plan_issues  # type: ignore[assignment]
    try:
        rc = manager_report.main(["--manager", "codex-manager"])
    finally:
        manager_report.collect_plan_validation_issues = original  # type: ignore[assignment]

    assert rc == 0
    reports = sorted(report_dir.glob("manager-report-*.md"))
    assert reports
    content = reports[-1].read_text(encoding="utf-8")
    assert "## Plan Validation Issues" in content
    assert "_plans/2025-10-10-test.plan.json" in content
    assert "layer must be one of L0-L6" in content


def test_manager_report_includes_authenticity(repo: Path):
    rc = manager_report.main(["--manager", "codex-manager"])
    assert rc == 0
    report_path = sorted((repo / "_report" / "manager").glob("manager-report-*.md"))[-1]
    content = report_path.read_text(encoding="utf-8")
    assert "External Authenticity" in content
    assert "primary_truth" in content
