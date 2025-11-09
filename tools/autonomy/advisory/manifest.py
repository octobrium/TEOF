"""Advisory service manifest builder."""

from __future__ import annotations

from typing import Any, Dict, Sequence

from tools.autonomy.service_manifest import BaseServiceManifestBuilder


class AdvisoryManifestBuilder(BaseServiceManifestBuilder):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(service="advisory", **kwargs)

    def default_commands(self) -> list[dict[str, Any]]:
        commands = super().default_commands()
        commands.extend(
            [
                {
                    "label": "decision_cycle",
                    "description": "Run decision cycle summariser",
                    "cmd": ["python3", "-m", "tools.autonomy.decision_cycle", "--plan", "{plan_id}"],
                },
                {
                    "label": "next_step",
                    "description": "Generate next-step advisory note",
                    "cmd": ["python3", "-m", "tools.autonomy.next_step", "--plan", "{plan_id}"],
                },
            ]
        )
        return commands

    def expected_receipts(self, plan_id: str, step_id: str, agent_id: str) -> list[dict[str, str]]:
        base = f"_report/autonomy/advisory/{agent_id}/{plan_id}"
        receipts = [
            {
                "description": "Advisory report",
                "path": f"{base}/reports/<timestamp>.json",
            },
            {
                "description": "Decision cycle reflection",
                "path": "memory/reflections/latest-advisory.json",
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
    return AdvisoryManifestBuilder().build_manifest(agent_id=agent_id, plan=plan, step=step, commands=commands)


__all__ = ["AdvisoryManifestBuilder", "build_manifest_payload"]
