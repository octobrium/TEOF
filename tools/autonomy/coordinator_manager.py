"""Coordinator manifest builder for autonomous agent orchestration.

Generates a structured manifest describing the next plan step a worker
agent should execute. The manifest captures canonical plan metadata,
recommended guardrail commands (status, scan, tasks), and the receipts
the worker must emit. Designed as the first building block for the
autonomous coordinator layer described in plan
`2025-10-19-autonomy-coordinator`.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, Sequence

from tools.autonomy.shared import load_json, write_receipt_payload


ROOT = Path(__file__).resolve().parents[2]
PLANS_DIR = ROOT / "_plans"
MANIFEST_FILE = ROOT / "AGENT_MANIFEST.json"
MANIFEST_OUTPUT_DIR = ROOT / "_report" / "agent"


def _utc_now() -> str:
    return dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_agent_id(candidate: Path | None = None) -> str:
    path = candidate if candidate is not None else MANIFEST_FILE
    manifest = load_json(path)
    if not isinstance(manifest, dict) or not manifest.get("agent_id"):
        raise SystemExit("::error:: unable to determine agent_id; run session_boot or provide --agent-id")
    return str(manifest["agent_id"])


def _load_plan(plan_id: str) -> Dict[str, Any]:
    plan_path = PLANS_DIR / f"{plan_id}.plan.json"
    if not plan_path.exists():
        raise SystemExit(f"::error:: plan not found: {plan_id}")
    data = load_json(plan_path)
    if not isinstance(data, dict):
        raise SystemExit(f"::error:: invalid plan payload: {plan_id}")
    return data


def _select_step(plan: Dict[str, Any], step_id: str) -> Dict[str, Any]:
    steps = plan.get("steps") or []
    for step in steps:
        if isinstance(step, dict) and step.get("id") == step_id:
            return step
    raise SystemExit(f"::error:: step '{step_id}' not found in plan '{plan.get('plan_id')}')")


def _default_commands() -> list[dict[str, Any]]:
    return [
        {
            "label": "pre_status",
            "description": "Capture current repository status snapshot",
            "cmd": ["python3", "-m", "teof", "foreman", "--say", "show the status"],
        },
        {
            "label": "alignment_scan",
            "description": "Run alignment scan summary before/after edits",
            "cmd": ["python3", "-m", "teof", "foreman", "--say", "run the alignment scan"],
        },
        {
            "label": "tasks_snapshot",
            "description": "List active tasks to monitor claim distribution",
            "cmd": ["python3", "-m", "teof", "foreman", "--say", "list today’s tasks"],
        },
    ]


def _expected_receipts(plan_id: str, step_id: str, agent_id: str) -> list[dict[str, str]]:
    base = f"_report/agent/{agent_id}/{plan_id}"
    return [
        {
            "description": "Worker run summary",
            "path": f"{base}/runs/<timestamp>.json",
        },
        {
            "description": "Plan step update",
            "path": f"_plans/{plan_id}.plan.json",
        },
        {
            "description": "Scan history entry",
            "path": "_report/usage/scan-history.jsonl",
        },
        {
            "description": "Manager review note",
            "path": f"_bus/messages/{plan_id}-{step_id}.jsonl",
        },
    ]


def build_manifest(
    *,
    agent_id: str,
    plan: Dict[str, Any],
    step: Dict[str, Any],
    commands: Sequence[dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    generated_at = _utc_now()
    plan_id = str(plan.get("plan_id"))
    step_id = str(step.get("id"))
    manifest: Dict[str, Any] = {
        "version": 1,
        "generated_at": generated_at,
        "manager_agent": agent_id,
        "plan": {
            "id": plan_id,
            "summary": plan.get("summary"),
            "systemic_targets": plan.get("systemic_targets", []),
            "layer_targets": plan.get("layer_targets", []),
            "priority": plan.get("priority"),
            "impact_score": plan.get("impact_score"),
        },
        "step": {
            "id": step_id,
            "title": step.get("title"),
            "status": step.get("status"),
            "notes": step.get("notes"),
        },
        "commands": list(commands or _default_commands()),
        "expected_receipts": _expected_receipts(plan_id, step_id, agent_id),
        "guardrails": {
            "require_session_boot": True,
            "run_scan_before": True,
            "run_scan_after": True,
            "ensure_plan_update": True,
        },
    }
    return manifest


def _manifest_output_path(agent_id: str, out_dir: Path | None = None) -> Path:
    base_dir = out_dir if out_dir is not None else MANIFEST_OUTPUT_DIR / agent_id / "manifests"
    base_dir.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    return base_dir / f"manifest-{timestamp}.json"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, help="Plan id to orchestrate (without .plan.json suffix)")
    parser.add_argument("--step", required=True, help="Plan step identifier (e.g., step-1)")
    parser.add_argument("--agent-id", help="Override agent id (defaults to AGENT_MANIFEST.json)")
    parser.add_argument("--out", type=Path, help="Explicit output path for the manifest JSON")
    parser.add_argument("--commands-json", type=Path, help="Optional JSON file describing custom command list")
    return parser.parse_args(argv)


def _load_commands(path: Path | None) -> Sequence[dict[str, Any]] | None:
    if path is None:
        return None
    data = load_json(path)
    if not isinstance(data, list):
        raise SystemExit("::error:: commands-json must contain a JSON array of command descriptors")
    commands: list[dict[str, Any]] = []
    for item in data:
        if not isinstance(item, dict) or "cmd" not in item:
            raise SystemExit("::error:: each command must be an object with a 'cmd' field")
        item = dict(item)
        item["cmd"] = list(item["cmd"])
        commands.append(item)
    return commands


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    agent_id = args.agent_id or _load_agent_id()
    plan = _load_plan(args.plan)
    step = _select_step(plan, args.step)
    commands = _load_commands(args.commands_json)

    manifest = build_manifest(agent_id=agent_id, plan=plan, step=step, commands=commands)

    out_path = args.out if args.out is not None else _manifest_output_path(agent_id)
    receipt_path = write_receipt_payload(out_path, manifest)
    try:
        display_path = receipt_path.relative_to(ROOT)
    except ValueError:
        display_path = receipt_path
    print(f"coordinator_manager: wrote {display_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
