"""Execution service manifest builder."""

from __future__ import annotations

from typing import Any, Dict, Sequence

from tools.autonomy.service_manifest import BaseServiceManifestBuilder


class ExecutionManifestBuilder(BaseServiceManifestBuilder):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(service="execution", **kwargs)

    def default_commands(self) -> list[dict[str, Any]]:
        commands = super().default_commands()
        commands.extend(
            [
                {
                    "label": "conductor_dry_run",
                    "description": "Dry-run conductor with the target plan",
                    "cmd": [
                        "python3",
                        "-m",
                        "tools.autonomy.conductor",
                        "--plan",
                        "{plan_id}",
                        "--dry-run",
                    ],
                },
                {
                    "label": "auto_loop",
                    "description": "Execute auto_loop orchestration",
                    "cmd": ["python3", "-m", "tools.autonomy.auto_loop", "--plan", "{plan_id}"],
                },
            ]
        )
        return commands

    def expected_receipts(self, plan_id: str, step_id: str, agent_id: str) -> list[dict[str, str]]:
        base = f"_report/autonomy/execution/{agent_id}/{plan_id}"
        receipts = [
            {
                "description": "Execution run summary",
                "path": f"{base}/runs/<timestamp>.json",
            },
            {
                "description": "Execution telemetry",
                "path": "_report/usage/autonomy-module-consolidation/telemetry-latest.json",
            },
        ]
        receipts.extend(super().expected_receipts(plan_id, step_id, agent_id))
        return receipts


def build_manifest_payload(
    *,
    agent_id: str,
    plan: Dict[str, Any],
    step: Dict[str, Any],
    commands: Sequence[dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    return ExecutionManifestBuilder().build_manifest(agent_id=agent_id, plan=plan, step=step, commands=commands)


__all__ = ["ExecutionManifestBuilder", "build_manifest_payload"]
