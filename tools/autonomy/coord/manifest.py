"""Coordinator manifest builder built on service manifest base."""

from __future__ import annotations

from typing import Any, Dict, Sequence

from tools.autonomy.service_manifest import BaseServiceManifestBuilder


class CoordinatorManifestBuilder(BaseServiceManifestBuilder):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(service="coordination", **kwargs)

    def default_commands(self) -> list[dict[str, Any]]:
        commands = super().default_commands()
        commands.append(
            {
                "label": "macro_hygiene",
                "description": "Run macro hygiene guard before dispatching workers",
                "cmd": [
                    "python3",
                    "-m",
                    "tools.autonomy.macro_hygiene",
                    "run",
                ],
            }
        )
        return commands

    def expected_receipts(self, plan_id: str, step_id: str, agent_id: str) -> list[dict[str, str]]:
        receipts = super().expected_receipts(plan_id, step_id, agent_id)
        receipts.insert(
            0,
            {
                "description": "Worker run summary",
                "path": f"_report/agent/{agent_id}/{plan_id}/runs/<timestamp>.json",
            },
        )
        return receipts


def build_manifest_payload(
    *,
    agent_id: str,
    plan: Dict[str, Any],
    step: Dict[str, Any],
    commands: Sequence[dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    return CoordinatorManifestBuilder().build_manifest(agent_id=agent_id, plan=plan, step=step, commands=commands)


__all__ = ["CoordinatorManifestBuilder", "build_manifest_payload"]
