
#!/usr/bin/env python3
"""Wrapper for receipts tooling."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.receipts.check import checker as run_check
from tools.receipts.scaffold import format_created, scaffold_claim, scaffold_plan, ScaffoldError
from tools.receipts.status import cli_status
from tools.receipts.utils import resolve_plan_paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Receipts utilities")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="Ensure receipts referenced by plans exist")
    check.add_argument("paths", nargs="*", help="Optional plan paths to check")

    scaffold = sub.add_parser("scaffold", help="Create receipt scaffolds for plans or claims")
    scaffold_sub = scaffold.add_subparsers(dest="scaffold_command", required=True)

    scaffold_plan_cmd = scaffold_sub.add_parser("plan", help="Generate scaffold files for a plan")
    scaffold_plan_cmd.add_argument("--plan-id", required=True, help="Plan identifier (e.g. 2025-09-21-example)")
    scaffold_plan_cmd.add_argument("--agent", required=True, help="Agent id to place receipts under")
    scaffold_plan_cmd.add_argument("--include-design", action="store_true", help="Also create design.md if missing")
    scaffold_plan_cmd.add_argument("--slug", help="Optional subdirectory override instead of the plan id")

    scaffold_claim_cmd = scaffold_sub.add_parser("claim", help="Generate scaffold files for a task/claim")
    scaffold_claim_cmd.add_argument("--task", required=True, help="Task identifier (e.g. QUEUE-010)")
    scaffold_claim_cmd.add_argument("--agent", required=True, help="Agent id to place receipts under")
    scaffold_claim_cmd.add_argument("--plan-id", help="Plan identifier linked to the task")
    scaffold_claim_cmd.add_argument("--branch", help="Branch name to record in claim metadata")
    scaffold_claim_cmd.add_argument("--slug", help="Optional subdirectory override")
    scaffold_claim_cmd.add_argument("--include-design", action="store_true", help="Also create design.md if missing")


    status_cmd = sub.add_parser("status", help="Summarise stored receipts")
    status_cmd.add_argument("--format", choices=['table', 'json'], default='table', help="Output format (default: table)")
    status_cmd.add_argument("kinds", nargs='*', help="Optional receipt kinds to include (e.g. attest)")
    args = parser.parse_args(argv)
    if args.command == "check":
        plans = resolve_plan_paths(args.paths)
        plan_strings = [p.as_posix() for p in plans]
        return run_check(plan_strings)
    if args.command == "status":
        return cli_status(args.kinds, output_format=args.format)
    if args.command == "scaffold":
        try:
            if args.scaffold_command == "plan":
                result = scaffold_plan(
                    args.plan_id,
                    agent=args.agent,
                    include_design=args.include_design,
                    slug=args.slug,
                )
            else:
                result = scaffold_claim(
                    task_id=args.task,
                    agent=args.agent,
                    plan_id=args.plan_id,
                    branch=args.branch,
                    slug=args.slug,
                    include_design=args.include_design,
                )
        except ScaffoldError as exc:
            parser.error(str(exc))
        print(format_created(result.created))
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
