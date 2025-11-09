"""CLI wrapper around the coordination manifest builder."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from tools.autonomy.coord import CoordinatorManifestBuilder
from tools.autonomy.shared import load_json


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
    builder = CoordinatorManifestBuilder()
    agent_id = args.agent_id or builder.load_agent_id()
    plan = builder.load_plan(args.plan)
    step = builder.select_step(plan, args.step)
    commands = _load_commands(args.commands_json)

    manifest = builder.build_manifest(agent_id=agent_id, plan=plan, step=step, commands=commands)

    receipt_path = builder.write_manifest(manifest, agent_id, args.out)
    try:
        display_path = receipt_path.relative_to(builder.root)
    except ValueError:
        display_path = receipt_path
    print(f"coordinator_manager: wrote {display_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
