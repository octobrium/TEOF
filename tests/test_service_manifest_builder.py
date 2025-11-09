from __future__ import annotations

from pathlib import Path

import pytest

from tools.autonomy.service_manifest import BaseServiceManifestBuilder


class DemoBuilder(BaseServiceManifestBuilder):
    def __init__(self) -> None:
        super().__init__(service="demo", root=Path.cwd())


def test_expected_receipts_and_guardrails(tmp_path: Path) -> None:
    builder = DemoBuilder()
    plan = {"plan_id": "demo-plan", "summary": "Demo summary"}
    step = {"id": "S1", "title": "Demo step", "status": "queued", "notes": ""}

    payload = builder.build_manifest(agent_id="codex-tier2", plan=plan, step=step)

    assert payload["service"] == "demo"
    assert payload["guardrails"] == builder.guardrails()

    receipts = payload["expected_receipts"]
    assert any(entry["path"].startswith("_report/autonomy/demo/") for entry in receipts)
    assert any(entry["path"].startswith("_plans/demo-plan") for entry in receipts)
    assert any(entry["path"].endswith("S1.jsonl") for entry in receipts)


def test_write_manifest(tmp_path: Path) -> None:
    builder = DemoBuilder()
    plan = {"plan_id": "demo-plan"}
    step = {"id": "S1"}

    payload = builder.build_manifest(agent_id="codex-tier2", plan=plan, step=step)
    path = builder.write_manifest(payload, agent_id="codex-tier2", out_path=tmp_path / "manifest.json")

    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "receipt_sha256" in text
