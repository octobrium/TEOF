from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.agent import autonomy_latency


class StubBus:
    def __init__(self) -> None:
        self.calls = []

    def handle_log(self, args):  # type: ignore[override]
        self.calls.append(args)
        return 0


def write_summary(tmp_path: Path, slow_plans: list[list[object]]) -> None:
    summary = {
        "generated_at": "2025-09-21T18:14:27Z",
        "metrics": {
            "plans_total": 5,
            "plans_missing_receipts": 0,
            "missing_plan_ids": [],
            "slow_plans": slow_plans,
        },
    }
    summary_path = tmp_path / "_report" / "usage" / "receipts-hygiene-summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary), encoding="utf-8")


def test_autonomy_latency_alerts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write_summary(
        tmp_path,
        [
            ["plan-fast", 100.0, None],
            ["plan-slow", 200000.0, 100000.0],
        ],
    )

    def fake_load_hygiene():
        return json.loads((tmp_path / "_report" / "usage" / "receipts-hygiene-summary.json").read_text())

    def fake_load_logs(limit=None):
        return []

    def fake_summarise(hygiene, logs):
        return {
            "hygiene": hygiene["metrics"],
            "batch_logs": {"entries": 0, "warn_count": 0, "fail_count": 0},
            "top_slow_plans": [plan[0] for plan in hygiene["metrics"]["slow_plans"][:3]],
        }

    stub_bus = StubBus()

    monkeypatch.setattr(autonomy_latency.autonomy_status, "load_hygiene", fake_load_hygiene)
    monkeypatch.setattr(autonomy_latency.autonomy_status, "load_batch_logs", fake_load_logs)
    monkeypatch.setattr(autonomy_latency.autonomy_status, "summarise", fake_summarise)
    monkeypatch.setattr(autonomy_latency.bus_event, "handle_log", stub_bus.handle_log)

    output_path = tmp_path / "latency.json"
    result = autonomy_latency.check_latency(
        fail_threshold=3600.0,
        warn_threshold=1800.0,
        dry_run=False,
        output=output_path,
    )
    alerts = result["alerts"]
    assert len(alerts) == 1
    payload = alerts[0]
    assert payload["plan_id"] == "plan-slow"
    assert payload["severity"] == "fail"
    assert stub_bus.calls
    bus_args = stub_bus.calls[0]
    assert bus_args.summary.startswith("Autonomy latency")
    assert bus_args.plan == "plan-slow"
    assert bus_args.severity == "high"
    assert result["receipt_path"] == output_path
    data = json.loads(output_path.read_text())
    assert data["slow_count"] == 1
    assert data["counts"]["fail"] == 1


def test_autonomy_latency_dry_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    write_summary(tmp_path, [["plan-slow", 90000.0, None]])

    def fake_load_hygiene():
        return json.loads((tmp_path / "_report" / "usage" / "receipts-hygiene-summary.json").read_text())

    def fake_load_logs(limit=None):
        return []

    def fake_summarise(hygiene, logs):
        return {
            "hygiene": hygiene["metrics"],
            "batch_logs": {"entries": 0, "warn_count": 0, "fail_count": 0},
            "top_slow_plans": [],
        }

    monkeypatch.setattr(autonomy_latency.autonomy_status, "load_hygiene", fake_load_hygiene)
    monkeypatch.setattr(autonomy_latency.autonomy_status, "load_batch_logs", fake_load_logs)
    monkeypatch.setattr(autonomy_latency.autonomy_status, "summarise", fake_summarise)

    result = autonomy_latency.check_latency(
        fail_threshold=3600.0,
        warn_threshold=1800.0,
        dry_run=True,
        write=False,
    )
    alerts = result["alerts"]
    assert len(alerts) == 1
    assert result["receipt_path"] is None
    output = capsys.readouterr().out
    assert "plan-slow" in output


def test_autonomy_latency_warn(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write_summary(tmp_path, [["plan-slow", 200000.0, None]])

    def fake_load_hygiene():
        return json.loads((tmp_path / "_report" / "usage" / "receipts-hygiene-summary.json").read_text())

    monkeypatch.setattr(autonomy_latency.autonomy_status, "load_hygiene", fake_load_hygiene)
    monkeypatch.setattr(autonomy_latency.autonomy_status, "load_batch_logs", lambda limit=None: [])

    def fake_summarise(hygiene, logs):
        return {
            "hygiene": {
                "slow_plans": hygiene["metrics"]["slow_plans"],
                "slow_plan_alerts": {
                    "alerts": [],
                    "warn_threshold_seconds": 100000.0,
                    "fail_threshold_seconds": 300000.0,
                },
            },
            "batch_logs": {"entries": 0, "warn_count": 0, "fail_count": 0},
            "top_slow_plans": [],
        }

    monkeypatch.setattr(autonomy_latency.autonomy_status, "summarise", fake_summarise)

    result = autonomy_latency.check_latency(
        warn_threshold=100000.0,
        fail_threshold=300000.0,
        dry_run=True,
        write=False,
    )
    alerts = result["alerts"]
    assert len(alerts) == 1
    assert alerts[0]["severity"] == "warn"
