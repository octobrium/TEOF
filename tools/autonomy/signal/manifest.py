"""Signal service manifest builder."""

from __future__ import annotations

from typing import Any, Dict, Sequence

from tools.autonomy.service_manifest import BaseServiceManifestBuilder


class SignalManifestBuilder(BaseServiceManifestBuilder):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(service="signal", **kwargs)

    def default_commands(self) -> list[dict[str, Any]]:
        commands = super().default_commands()
        commands.append(
            {
                "label": "systemic_radar",
                "description": "Run systemic radar streaming snapshot",
                "cmd": ["python3", "-m", "tools.autonomy.systemic_radar", "--summary"],
            }
        )
        return commands

    def expected_receipts(self, plan_id: str, step_id: str, agent_id: str) -> list[dict[str, str]]:
        base = f"_report/autonomy/signal/{agent_id}/{plan_id}"
        receipts = [
            {
                "description": "Signal dashboard snapshot",
                "path": f"{base}/dashboards/<timestamp>.json",
            },
            {
                "description": "Systemic radar history",
                "path": "_report/usage/systemic-radar/systemic-radar-latest.json",
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
    return SignalManifestBuilder().build_manifest(agent_id=agent_id, plan=plan, step=step, commands=commands)


__all__ = ["SignalManifestBuilder", "build_manifest_payload"]
