from __future__ import annotations

import json
from pathlib import Path

import teof.bootloader as bootloader


def _write_inputs(root: Path) -> tuple[Path, Path, Path]:
    ledger = root / "impact-log.jsonl"
    ledger.write_text(
        "\n".join(
            [
                json.dumps({"slug": "relay-launch", "title": "Relay launch"}),
                json.dumps({"slug": "partner-onboarding", "title": "Partner onboarding"}),
            ]
        ),
        encoding="utf-8",
    )

    plans_dir = root / "plans"
    plans_dir.mkdir(parents=True, exist_ok=True)
    (plans_dir / "2025-11-09-impact-bridge.plan.json").write_text(
        json.dumps(
            {
                "plan_id": "2025-11-09-impact-bridge",
                "impact_ref": "relay-launch",
                "links": [{"type": "queue", "ref": "queue/056-impact-bridge.md"}],
            }
        ),
        encoding="utf-8",
    )

    backlog = root / "todo.json"
    backlog.write_text(
        json.dumps(
            {
                "version": 0,
                "items": [
                    {
                        "id": "ND-056",
                        "title": "Impact Bridge Dashboard",
                        "plan_suggestion": "2025-11-09-impact-bridge",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return ledger, plans_dir, backlog


def test_teof_impact_bridge_cli_json(tmp_path: Path, monkeypatch, capsys) -> None:
    ledger, plans_dir, backlog = _write_inputs(tmp_path)
    report_dir = tmp_path / "reports"

    exit_code = bootloader.main(
        [
            "impact_bridge",
            "--impact-log",
            str(ledger),
            "--plans-dir",
            str(plans_dir),
            "--backlog",
            str(backlog),
            "--report-dir",
            str(report_dir),
        ]
    )
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Impact Bridge Stats:" in out
    assert "impact bridge summary" in out
    summary_files = sorted(report_dir.glob("impact-bridge-*.json"))
    markdown_files = sorted(report_dir.glob("impact-bridge-dashboard-*.md"))
    assert summary_files and markdown_files
    payload = json.loads(summary_files[-1].read_text(encoding="utf-8"))
    assert payload["stats"]["ledger_entries"] == 2
    assert payload["stats"]["plans_linked"] == 1


def test_teof_impact_bridge_cli_json_format(tmp_path: Path, capsys) -> None:
    ledger, plans_dir, backlog = _write_inputs(tmp_path)
    orphans_out = tmp_path / "orphans.json"

    exit_code = bootloader.main(
        [
            "impact_bridge",
            "--impact-log",
            str(ledger),
            "--plans-dir",
            str(plans_dir),
            "--backlog",
            str(backlog),
            "--orphans-out",
            str(orphans_out),
            "--no-write",
            "--format",
            "json",
        ]
    )
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["stats"]["ledger_entries"] == 2
    assert payload["stats"]["plans_linked"] == 1
    assert payload["receipts"]["summary"] is None
    orphan_payload = json.loads(orphans_out.read_text(encoding="utf-8"))
    assert orphan_payload["orphan_impact_ref"] == []
    assert orphan_payload["missing_impact_ref"] == []
