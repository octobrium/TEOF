from __future__ import annotations

from tools.autonomy.advisory.manifest import build_manifest_payload as build_advisory
from tools.autonomy.coord.manifest import build_manifest_payload as build_coord
from tools.autonomy.exec.manifest import build_manifest_payload as build_exec
from tools.autonomy.signal.manifest import build_manifest_payload as build_signal

PLAN = {
    "plan_id": "demo-plan",
    "summary": "Demo",
    "systemic_targets": ["S1"],
    "layer_targets": ["L5"],
    "priority": 1,
    "impact_score": 5,
}

STEP = {
    "id": "S1",
    "title": "Demo step",
    "status": "pending",
    "notes": "",
}


def _assert_manifest(payload: dict, service: str) -> None:
    assert payload["service"] == service
    assert payload["plan"]["id"] == PLAN["plan_id"]
    assert payload["step"]["id"] == STEP["id"]
    assert payload["commands"]
    assert payload["expected_receipts"]


def test_coord_manifest_payload() -> None:
    payload = build_coord(agent_id="codex-1", plan=PLAN, step=STEP)
    _assert_manifest(payload, "coordination")


def test_exec_manifest_payload() -> None:
    payload = build_exec(agent_id="codex-2", plan=PLAN, step=STEP)
    _assert_manifest(payload, "execution")


def test_signal_manifest_payload() -> None:
    payload = build_signal(agent_id="codex-3", plan=PLAN, step=STEP)
    _assert_manifest(payload, "signal")


def test_advisory_manifest_payload() -> None:
    payload = build_advisory(agent_id="codex-4", plan=PLAN, step=STEP)
    _assert_manifest(payload, "advisory")
