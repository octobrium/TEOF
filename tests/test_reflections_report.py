from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from teof import bootloader, reflections_report


def _write_reflection(root: Path, *, captured_at: str, title: str, layers: list[str], tags: list[str], **extras: str) -> None:
    reflections_dir = root / "memory" / "reflections"
    reflections_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, object] = {
        "captured_at": captured_at,
        "title": title,
        "layers": layers,
        "tags": tags,
        "summary": extras.get("summary"),
        "plan_suggestion": extras.get("plan_suggestion"),
        "signals": extras.get("signals"),
        "actions": extras.get("actions"),
        "notes": extras.get("notes"),
    }
    timestamp = captured_at.replace(":", "").replace("-", "").replace("+00:00", "Z")
    filename = f"reflection-{timestamp}.json"
    (reflections_dir / filename).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_collect_reflections_orders_newest_first(tmp_path: Path) -> None:
    now = datetime(2025, 10, 4, 12, 0, 0, tzinfo=timezone.utc)
    older = (now.replace(hour=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
    newer = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    _write_reflection(tmp_path, captured_at=older, title="Older", layers=["L1"], tags=["foo"])
    _write_reflection(tmp_path, captured_at=newer, title="Newer", layers=["L2"], tags=["bar"], plan_suggestion="PLAN-1")

    records = reflections_report.collect_reflections(root=tmp_path)
    assert [record.title for record in records] == ["Newer", "Older"]
    summary = reflections_report.summarize(records)
    assert summary["total"] == 2
    assert summary["by_layer"] == {"L1": 1, "L2": 1}


def test_render_table_and_filters(tmp_path: Path) -> None:
    stamp = "2025-10-05T00:00:00Z"
    _write_reflection(tmp_path, captured_at=stamp, title="Tagged", layers=["L3"], tags=["alpha"], plan_suggestion="PLAN-X")
    _write_reflection(tmp_path, captured_at="2025-10-04T00:00:00Z", title="Untagged", layers=["L2"], tags=[])

    records = reflections_report.collect_reflections(root=tmp_path)
    filtered = reflections_report.filter_reflections(records, tags=["alpha"])
    assert len(filtered) == 1
    assert filtered[0].title == "Tagged"

    table = reflections_report.render_table(filtered)
    assert "PLAN-X" in table
    assert "Tagged" in table


def test_cmd_reflections_outputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _write_reflection(
        tmp_path,
        captured_at="2025-10-05T12:00:00Z",
        title="Latest",
        layers=["L4", "L5"],
        tags=["workflow"],
        plan_suggestion="PLAN-42",
        summary="Validated loop",
    )
    _write_reflection(
        tmp_path,
        captured_at="2025-10-03T09:00:00Z",
        title="Older",
        layers=["L2"],
        tags=[],
    )

    monkeypatch.setattr(reflections_report, "ROOT", tmp_path)
    monkeypatch.setattr(bootloader, "ROOT", tmp_path)

    parser = bootloader.build_parser()
    args = parser.parse_args(["reflections", "--limit", "1"])
    rc = bootloader.cmd_reflections(args)
    assert rc == 0
    output = capsys.readouterr().out
    assert "Total reflections: 2" in output
    assert "PLAN-42" in output

    capsys.readouterr()
    args_json = parser.parse_args(["reflections", "--format", "json"])
    rc = bootloader.cmd_reflections(args_json)
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["summary"]["total"] == 2
    assert payload["reflections"][0]["title"] == "Latest"
