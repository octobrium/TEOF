from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from teof import bootloader
from tools.impact import ttd_trend


def _write_entry(path: Path, ts: datetime, observation: float, recursion: float, trust: float, readiness: str) -> None:
    payload = {
        "ts": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "manager": "codex-test",
        "metrics": {
            "observation.capacity": {
                "plan_to_first_receipt_median": observation,
            },
            "recursion.depth": {
                "open_ratio": recursion,
            },
            "optional.safe": {
                "overall_trust": trust,
            },
            "integrity.gap": {
                "readiness_status": readiness,
            },
            "sustainability.signal": {
                "quickstart_age_hours": observation / 100.0,
                "readiness_status": readiness,
            },
        },
    }
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def test_ttd_trend_json(tmp_path: Path, capsys) -> None:
    log = tmp_path / "ttd.jsonl"
    now = datetime(2025, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
    entries = [
        (now - timedelta(days=2), 4000.0, 0.2, 0.65, "amber"),
        (now - timedelta(days=1), 3500.0, 0.18, 0.69, "amber"),
        (now, 3000.0, 0.15, 0.75, "green"),
    ]
    contents = "".join(
        json.dumps(
            {
                "ts": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "manager": "codex-test",
                "metrics": {
                    "observation.capacity": {"plan_to_first_receipt_median": obs},
                    "recursion.depth": {"open_ratio": rec},
                    "optional.safe": {"overall_trust": trust},
                    "integrity.gap": {"readiness_status": readiness},
                    "sustainability.signal": {
                        "quickstart_age_hours": obs / 100.0,
                        "readiness_status": readiness,
                    },
                },
            }
        )
        + "\n"
        for ts, obs, rec, trust, readiness in entries
    )
    log.write_text(contents, encoding="utf-8")

    args = ["--input", str(log), "--format", "json"]
    rc = ttd_trend.main(args)
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    metrics = out["metrics"]
    oc = metrics["observation.capacity"]
    assert oc["latest"] == entries[-1][1]
    assert oc["trend"] == "down"
    assert out["alerts"] == []


def test_ttd_trend_table_and_alert(tmp_path: Path, capsys) -> None:
    log = tmp_path / "ttd.jsonl"
    ts = datetime(2025, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
    entries = [
        {
            "ts": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "manager": "codex-test",
            "metrics": {
                "observation.capacity": {"plan_to_first_receipt_median": 1000},
                "recursion.depth": {"open_ratio": 0.3},
                "optional.safe": {"overall_trust": 0.6},
                "integrity.gap": {"readiness_status": "red"},
                "sustainability.signal": {
                    "quickstart_age_hours": 15.0,
                    "readiness_status": "red",
                },
            },
        }
    ]
    log.write_text("\n".join(json.dumps(entry) for entry in entries) + "\n", encoding="utf-8")

    rc = ttd_trend.main(["--input", str(log), "--format", "table"])
    assert rc == 0
    output = capsys.readouterr().out
    assert "Alerts:" in output
    assert "integrity.gap" in output


def test_ttd_trend_out_file(tmp_path: Path, capsys) -> None:
    log = tmp_path / "ttd.jsonl"
    ts = datetime(2025, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
    entries = [
        {
            "ts": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "manager": "codex-test",
            "metrics": {
                "observation.capacity": {"plan_to_first_receipt_median": 1000},
                "recursion.depth": {"open_ratio": 0.3},
                "optional.safe": {"overall_trust": 0.8},
                "integrity.gap": {"readiness_status": "green"},
                "sustainability.signal": {
                    "quickstart_age_hours": 9.0,
                    "readiness_status": "green",
                },
            },
        }
    ]
    log.write_text("\n".join(json.dumps(entry) for entry in entries) + "\n", encoding="utf-8")
    out_path = tmp_path / "summary.json"
    rc = ttd_trend.main(["--input", str(log), "--format", "json", "--out", str(out_path)])
    assert rc == 0
    captured = capsys.readouterr().out
    assert out_path.read_text(encoding="utf-8")
    assert "wrote summary" in captured


def test_bootloader_ttd_trend(tmp_path: Path, monkeypatch, capsys) -> None:
    log = tmp_path / "ttd.jsonl"
    ts = datetime(2025, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
    entry = {
        "ts": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "manager": "codex-test",
        "metrics": {
            "observation.capacity": {"plan_to_first_receipt_median": 2000},
            "recursion.depth": {"open_ratio": 0.2},
            "optional.safe": {"overall_trust": 0.72},
            "integrity.gap": {"readiness_status": "green"},
            "sustainability.signal": {
                "quickstart_age_hours": 8.0,
                "readiness_status": "green",
            },
        },
    }
    log.write_text(json.dumps(entry) + "\n", encoding="utf-8")

    monkeypatch.setattr(ttd_trend, "ROOT", tmp_path)
    monkeypatch.setattr(bootloader, "ROOT", tmp_path)

    parser = bootloader.build_parser()
    args = parser.parse_args(["ttd-trend", "--input", "ttd.jsonl", "--format", "json"])
    rc = bootloader.cmd_ttd_trend(args)
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["entry_count"] == 1


def test_ttd_trend_main_rejects_nonpositive_window() -> None:
    with pytest.raises(SystemExit) as excinfo:
        ttd_trend.main(["--window", "0"])
    assert excinfo.value.code == "--window must be positive"


def test_ttd_trend_main_rejects_negative_days() -> None:
    with pytest.raises(SystemExit) as excinfo:
        ttd_trend.main(["--days", "-1"])
    assert excinfo.value.code == "--days must be non-negative"


def test_bootloader_ttd_trend_validates_arguments(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ttd_trend, "ROOT", tmp_path)
    monkeypatch.setattr(bootloader, "ROOT", tmp_path)
    parser = bootloader.build_parser()

    args_window = parser.parse_args(["ttd-trend", "--window", "0"])
    with pytest.raises(SystemExit) as excinfo_window:
        bootloader.cmd_ttd_trend(args_window)
    assert excinfo_window.value.code == "--window must be positive"

    args_days = parser.parse_args(["ttd-trend", "--days", "-1"])
    with pytest.raises(SystemExit) as excinfo_days:
        bootloader.cmd_ttd_trend(args_days)
    assert excinfo_days.value.code == "--days must be non-negative"
