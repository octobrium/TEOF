from __future__ import annotations

import json
from pathlib import Path

from tools.agent.confidence_report import ConfidenceEntry
from tools.agent import confidence_watch


def _write_entries(path: Path, entries: list[ConfidenceEntry]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(
            {
                "ts": entry.ts,
                "agent": entry.agent,
                "confidence": entry.confidence,
                **({"note": entry.note} if entry.note is not None else {}),
            },
            sort_keys=True,
        )
        + "\n"
        for entry in entries
    ]
    path.write_text("".join(lines), encoding="utf-8")


def test_summarise_agent_triggers_alert() -> None:
    entries = [
        ConfidenceEntry(ts=f"2025-10-06T0{i}:00:00Z", agent="codex-4", confidence=0.95, note=None)
        for i in range(5)
    ]
    summary = confidence_watch.summarise_agent(
        "codex-4",
        entries,
        warn_threshold=0.9,
        window=5,
        min_count=3,
        alert_ratio=0.6,
    )
    assert summary.alert is True
    assert summary.high_count == 5
    assert summary.window_total == 5


def test_scan_agents_and_report(tmp_path: Path) -> None:
    base = tmp_path / "_report" / "agent"
    entries = [
        ConfidenceEntry(ts="2025-10-06T00:00:00Z", agent="codex-4", confidence=0.95, note="prep"),
        ConfidenceEntry(ts="2025-10-06T01:00:00Z", agent="codex-4", confidence=0.92, note=None),
        ConfidenceEntry(ts="2025-10-06T02:00:00Z", agent="codex-4", confidence=0.88, note=None),
        ConfidenceEntry(ts="2025-10-06T03:00:00Z", agent="codex-4", confidence=0.91, note="loop"),
        ConfidenceEntry(ts="2025-10-06T04:00:00Z", agent="codex-4", confidence=0.94, note=None),
    ]
    log_path = base / "codex-4" / "confidence.jsonl"
    _write_entries(log_path, entries)

    summaries = confidence_watch.scan_agents(
        base,
        warn_threshold=0.9,
        window=4,
        min_count=3,
        alert_ratio=0.6,
    )
    assert len(summaries) == 1
    summary = summaries[0]
    assert summary.agent == "codex-4"
    assert summary.alert is True
    assert summary.high_count == 3
    assert summary.latest_ts == "2025-10-06T04:00:00Z"

    report = confidence_watch.build_report(
        summaries,
        warn_threshold=0.9,
        window=4,
        min_count=3,
        alert_ratio=0.6,
    )
    assert report["alerts"] == ["codex-4"]

    out_dir = tmp_path / "reports"
    path = confidence_watch._write_report(report, out_dir)
    assert path.exists()
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["alerts"] == ["codex-4"]


def test_cli_json_output(tmp_path: Path, capsys) -> None:
    base = tmp_path / "_report" / "agent"
    entries = [
        ConfidenceEntry(ts="2025-10-06T00:00:00Z", agent="codex-5", confidence=0.7, note=None),
        ConfidenceEntry(ts="2025-10-06T01:00:00Z", agent="codex-5", confidence=0.75, note="note"),
        ConfidenceEntry(ts="2025-10-06T02:00:00Z", agent="codex-5", confidence=0.8, note=None),
    ]
    log_path = base / "codex-5" / "confidence.jsonl"
    _write_entries(log_path, entries)

    exit_code = confidence_watch.main(
        [
            "--dir",
            str(base),
            "--warn-threshold",
            "0.9",
            "--format",
            "json",
        ]
    )
    assert exit_code == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["alerts"] == []
    assert payload["agents"][0]["agent"] == "codex-5"
    assert payload["agents"][0]["alert"] is False


def test_cli_fail_on_alert(tmp_path: Path) -> None:
    base = tmp_path / "_report" / "agent"
    entries = [
        ConfidenceEntry(ts=f"2025-10-06T0{i}:00:00Z", agent="codex-7", confidence=0.93, note=None)
        for i in range(6)
    ]
    log_path = base / "codex-7" / "confidence.jsonl"
    _write_entries(log_path, entries)

    exit_code = confidence_watch.main(
        [
            "--dir",
            str(base),
            "--warn-threshold",
            "0.9",
            "--window",
            "5",
            "--min-count",
            "5",
            "--format",
            "json",
            "--fail-on-alert",
        ]
    )
    assert exit_code == 1


def test_run_watch_returns_report(tmp_path: Path) -> None:
    base = tmp_path / "_report" / "agent"
    entries = [
        ConfidenceEntry(ts="2025-10-06T00:00:00Z", agent="codex-9", confidence=0.4, note="warmup"),
        ConfidenceEntry(ts="2025-10-06T01:00:00Z", agent="codex-9", confidence=0.6, note=None),
    ]
    log_path = base / "codex-9" / "confidence.jsonl"
    _write_entries(log_path, entries)

    report_dir = tmp_path / "reports"
    summaries, report, path = confidence_watch.run_watch(
        base_dir=base,
        warn_threshold=0.9,
        window=0,
        min_count=1,
        alert_ratio=0.5,
        report_dir=report_dir,
    )
    assert len(summaries) == 1
    assert report["alerts"] == []
    assert path is not None and path.exists()
    recorded = json.loads(path.read_text(encoding="utf-8"))
    assert recorded["agents"][0]["agent"] == "codex-9"
