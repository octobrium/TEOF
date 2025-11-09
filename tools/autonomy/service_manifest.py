"""Shared utilities for service manifest builders used in consolidation."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Sequence

from teof._paths import repo_root

from tools.autonomy.shared import load_json, write_receipt_payload


def _utc_now() -> str:
    return dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class BaseServiceManifestBuilder:
    """Base helper for generating service manifests."""

    service: str
    root: Path = repo_root()
    plans_dir: Path | None = None
    manifest_file: Path | None = None
    manifest_output_dir: Path | None = None

    def __post_init__(self) -> None:
        self.plans_dir = self.plans_dir or (self.root / "_plans")
        self.manifest_file = self.manifest_file or (self.root / "AGENT_MANIFEST.json")
        self.manifest_output_dir = self.manifest_output_dir or (self.root / "_report" / "agent")

    # ------------------------------------------------------------------ loaders
    def load_agent_id(self, candidate: Path | None = None) -> str:
        manifest_path = candidate if candidate is not None else self.manifest_file
        manifest = load_json(manifest_path)
        if not isinstance(manifest, dict) or not manifest.get("agent_id"):
            raise SystemExit("::error:: unable to determine agent_id; run session_boot or provide --agent-id")
        return str(manifest["agent_id"])

    def load_plan(self, plan_id: str) -> Dict[str, Any]:
        plan_path = self.plans_dir / f"{plan_id}.plan.json"
        if not plan_path.exists():
            raise SystemExit(f"::error:: plan not found: {plan_id}")
        data = load_json(plan_path)
        if not isinstance(data, dict):
            raise SystemExit(f"::error:: invalid plan payload: {plan_id}")
        return data

    @staticmethod
    def select_step(plan: Dict[str, Any], step_id: str) -> Dict[str, Any]:
        steps = plan.get("steps") or []
        for step in steps:
            if isinstance(step, dict) and step.get("id") == step_id:
                return step
        raise SystemExit(f"::error:: step '{step_id}' not found in plan '{plan.get('plan_id')}')")

    # ------------------------------------------------------------------ defaults
    def default_commands(self) -> list[dict[str, Any]]:
        return [
            {
                "label": "status",
                "description": "Capture current repository status snapshot",
                "cmd": ["python3", "-m", "teof", "foreman", "--say", "show the status"],
            },
            {
                "label": "alignment_scan",
                "description": "Run alignment scan summary before/after edits",
                "cmd": ["python3", "-m", "teof", "foreman", "--say", "run the alignment scan"],
            },
        ]

    def expected_receipts(self, plan_id: str, step_id: str, agent_id: str) -> list[dict[str, str]]:
        base = f"_report/autonomy/{self.service}/{agent_id}/{plan_id}"
        return [
            {
                "description": "Service run summary",
                "path": f"{base}/runs/<timestamp>.json",
            },
            {
                "description": "Plan step update",
                "path": f"_plans/{plan_id}.plan.json",
            },
            {
                "description": "Manager review note",
                "path": f"_bus/messages/{plan_id}-{step_id}.jsonl",
            },
        ]

    def guardrails(self) -> dict[str, Any]:
        return {
            "require_session_boot": True,
            "run_scan_before": True,
            "run_scan_after": True,
            "ensure_plan_update": True,
        }

    # ------------------------------------------------------------------ manifest
    def build_manifest(
        self,
        *,
        agent_id: str,
        plan: Dict[str, Any],
        step: Dict[str, Any],
        commands: Sequence[dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        plan_id = str(plan.get("plan_id"))
        step_id = str(step.get("id"))
        payload: Dict[str, Any] = {
            "version": 1,
            "service": self.service,
            "generated_at": _utc_now(),
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
            "commands": list(commands or self.default_commands()),
            "expected_receipts": self.expected_receipts(plan_id, step_id, agent_id),
            "guardrails": self.guardrails(),
        }
        return payload

    def manifest_output_path(self, agent_id: str, out_dir: Path | None = None) -> Path:
        base_dir = out_dir if out_dir is not None else self.manifest_output_dir / agent_id / "manifests"
        base_dir.mkdir(parents=True, exist_ok=True)
        timestamp = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        return base_dir / f"manifest-{timestamp}.json"

    def write_manifest(self, payload: Dict[str, Any], agent_id: str, out_path: Path | None = None) -> Path:
        target = out_path or self.manifest_output_path(agent_id)
        return write_receipt_payload(target, payload)


__all__ = ["BaseServiceManifestBuilder"]
