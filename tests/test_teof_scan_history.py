from __future__ import annotations

import json
from pathlib import Path

import pytest

import teof.bootloader as bootloader
from teof.commands import scan_history as scan_history_mod


def _write_history(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    entries = [
        {
            "ts": "2025-11-09T06:20:00Z",
            "components": ["frontier", "critic", "tms", "ethics"],
            "counts": {"frontier": 5, "critic": 1, "tms": 0, "ethics": 0},
            "format": "table",
            "summary": False,
            "emit_bus": True,
            "emit_plan": False,
        },
        {
            "ts": "2025-11-09T06:25:00Z",
            "components": ["frontier", "critic", "tms"],
            "counts": {"frontier": 3, "critic": 0, "tms": 1, "ethics": 0},
            "format": "json",
            "summary": True,
            "emit_bus": False,
            "emit_plan": True,
        },
    ]
    with path.open("w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry))
            handle.write("\n")


def _patch_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, history_path: Path) -> None:
    monkeypatch.setattr(scan_history_mod, "ROOT", tmp_path, raising=False)
    monkeypatch.setattr(scan_history_mod, "DEFAULT_HISTORY", history_path, raising=False)


def test_scan_history_table_default_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    history_path = tmp_path / "_report" / "usage" / "systemic-scan" / "ratchet-history.jsonl"
    _write_history(history_path)
    _patch_root(tmp_path, monkeypatch, history_path)

    exit_code = bootloader.main(["scan_history", "--limit", "1"])
    assert exit_code == 0
    output = capsys.readouterr().out
    assert "ts" in output.splitlines()[0]
    assert "2025-11-09T06:25:00Z" in output
    assert "F:3 C:0 T:1 E:0" in output
    assert "SJP" in output  # summary + json output + plan emission


def test_scan_history_json_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    history_path = tmp_path / "history.jsonl"
    _write_history(history_path)
    _patch_root(tmp_path, monkeypatch, tmp_path / "_report" / "usage" / "scan-history.jsonl")

    exit_code = bootloader.main(["scan_history", "--format", "json", "--path", str(history_path), "--limit", "2"])
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["count"] == 2
    assert payload["path"] == str(history_path)
    assert payload["summary"] is False
    assert payload["summary_counts"]["frontier"] == 8
    assert payload["entries"][0]["ts"] == "2025-11-09T06:25:00Z"


def test_scan_history_component_filter(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    history_path = tmp_path / "history.jsonl"
    _write_history(history_path)
    _patch_root(tmp_path, monkeypatch, history_path)

    exit_code = bootloader.main(
        [
            "scan_history",
            "--component",
            "critic",
            "--component",
            "ethics",
        ]
    )
    assert exit_code == 0
    output = capsys.readouterr().out
    # Only first entry includes ethics
    assert "2025-11-09T06:20:00Z" in output
    assert "2025-11-09T06:25:00Z" not in output


def test_scan_history_emits_receipt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    history_path = tmp_path / "history.jsonl"
    _write_history(history_path)
    _patch_root(tmp_path, monkeypatch, history_path)
    receipt_dir = tmp_path / "_report" / "usage" / "scan-history" / "receipts"
    monkeypatch.setattr(scan_history_mod, "RECEIPT_DIR", receipt_dir, raising=False)

    exit_code = bootloader.main(["scan_history", "--limit", "1", "--emit-receipt"])
    assert exit_code == 0

    receipts = sorted(receipt_dir.glob("scan_history-*.json"))
    assert receipts, "receipt file should be created"
    payload = json.loads(receipts[0].read_text(encoding="utf-8"))
    assert payload["command"] == "scan_history"
    assert payload["query"]["limit"] == 1
    assert payload["summary_counts"]["frontier"] >= 0


def test_scan_history_summary_table(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    history_path = tmp_path / "history.jsonl"
    _write_history(history_path)
    _patch_root(tmp_path, monkeypatch, history_path)

    exit_code = bootloader.main(["scan_history", "--summary", "--component", "critic"])
    assert exit_code == 0
    output = capsys.readouterr().out
    assert "entries: 2 (filter: critic)" in output
    assert "- frontier: 8" in output
    assert "- tms: 1" in output


def test_scan_history_summary_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    history_path = tmp_path / "history.jsonl"
    _write_history(history_path)
    _patch_root(tmp_path, monkeypatch, history_path)

    exit_code = bootloader.main(["scan_history", "--summary", "--format", "json", "--limit", "1"])
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["summary"] is True
    assert payload["entries"] == []
    assert payload["summary_counts"]["frontier"] == 3
