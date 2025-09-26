#!/usr/bin/env python3
"""Repo-local TEOF CLI bootstrapper.

Provides a minimal subset of the production CLI so tests can invoke
`teof brief` without requiring a separate installation.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import shutil
import sys
from pathlib import Path
from typing import Iterable

from extensions.validator.scorers.ensemble import score_file
from . import status_report, tasks_report
from tools.autonomy import critic as critic_mod
from tools.autonomy import frontier as frontier_mod
from tools.autonomy import tms as tms_mod

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXAMPLES_DIR = ROOT / "docs" / "examples" / "brief" / "inputs"
ARTIFACT_ROOT = ROOT / "artifacts" / "ocers_out"


def _write_brief_outputs(output_dir: pathlib.Path) -> list[dict[str, object]]:
    """Score bundled brief inputs and write ensemble outputs."""
    files = sorted(EXAMPLES_DIR.glob("*.txt"))
    records: list[dict[str, object]] = []
    for path in files:
        result = score_file(path)
        out_path = output_dir / f"{path.stem}.ensemble.json"
        with out_path.open("w", encoding="utf-8") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        records.append({"input": path.name, "output": out_path.name, "result": result})
    return records


def cmd_brief(_: argparse.Namespace) -> int:
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    dest = ARTIFACT_ROOT / timestamp
    dest.mkdir(parents=True, exist_ok=True)

    records = _write_brief_outputs(dest)

    summary = {
        "generated_at": timestamp,
        "inputs": [record["input"] for record in records],
        "artifacts": [record["output"] for record in records],
    }
    with (dest / "brief.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    with (dest / "score.txt").open("w", encoding="utf-8") as handle:
        handle.write("ensemble_count=" + str(len(records)) + "\n")

    latest = ARTIFACT_ROOT / "latest"
    if latest.exists() or latest.is_symlink():
        if latest.is_symlink() or latest.is_file():
            latest.unlink()
        else:
            shutil.rmtree(latest)
    try:
        latest.symlink_to(dest, target_is_directory=True)
    except OSError:
        shutil.copytree(dest, latest)
    print(f"brief: wrote {dest.relative_to(ROOT)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="teof", description="TEOF CLI (repo-local subset)")
    sub = parser.add_subparsers(dest="command", required=True)

    brief = sub.add_parser(
        "brief", help="Run bundled brief example through the ensemble scorer"
    )
    brief.set_defaults(func=cmd_brief)

    status = sub.add_parser(
        "status",
        help="Generate repository status snapshot (default: print to stdout)",
    )
    status.add_argument(
        "--out",
        type=Path,
        help="Write the status snapshot to this path instead of stdout",
    )
    status.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress info logs (useful with --out)",
    )
    status.set_defaults(func=cmd_status)

    tasks = sub.add_parser(
        "tasks",
        help="Summarise repository tasks (table or JSON)",
    )
    tasks.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format (default: table)",
    )
    tasks.add_argument(
        "--all",
        action="store_true",
        help="Include completed tasks in the report",
    )
    tasks.set_defaults(func=cmd_tasks)

    frontier = sub.add_parser(
        "frontier",
        help="Score backlog/tasks/facts to surface next coordinates",
    )
    frontier.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of entries to show (default: 10)",
    )
    frontier.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format",
    )
    frontier.add_argument(
        "--out",
        type=Path,
        help="Optional path (relative to repo) to write receipt JSON",
    )
    frontier.set_defaults(func=cmd_frontier)

    critic = sub.add_parser(
        "critic",
        help="Detect anomalies and emit repair suggestions",
    )
    critic.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format",
    )
    critic.add_argument(
        "--out",
        type=Path,
        help="Optional path to write critic receipt JSON",
    )
    critic.add_argument(
        "--emit-bus",
        action="store_true",
        help="Emit repair tasks into _bus/claims (requires --out)",
    )
    critic.set_defaults(func=cmd_critic)

    tms = sub.add_parser(
        "tms",
        help="Detect fact conflicts (truth maintenance system)",
    )
    tms.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format",
    )
    tms.add_argument(
        "--out",
        type=Path,
        help="Optional path to write TMS receipt JSON",
    )
    tms.add_argument(
        "--emit-plan",
        action="store_true",
        help="Emit plan skeletons for detected conflicts",
    )
    tms.set_defaults(func=cmd_tms)

    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    func = getattr(args, "func", None)
    if not callable(func):
        parser.print_help()
        return 2
    return func(args)


def cmd_status(args: argparse.Namespace) -> int:
    out_path: Path | None = args.out
    quiet: bool = bool(getattr(args, "quiet", False))
    if out_path is not None:
        if not out_path.is_absolute():
            out_path = ROOT / out_path
        status_report.write_status(out_path, root=ROOT, quiet=quiet)
        return 0
    # stdout path
    content = status_report.generate_status(ROOT)
    if not quiet:
        print(content)
    else:
        # Quiet without --out still returns content for scripting expectations
        sys.stdout.write(content)
    return 0


def cmd_tasks(args: argparse.Namespace) -> int:
    include_done = bool(getattr(args, "all", False))
    output_format = getattr(args, "format", "table")

    records = tasks_report.collect_tasks(root=ROOT)
    filtered = tasks_report.filter_open_tasks(records, include_done=include_done)
    ordered = tasks_report.sort_tasks(filtered)
    warnings = tasks_report.compute_warnings(ordered)

    if output_format == "json":
        payload = tasks_report.to_payload(ordered, warnings=warnings)
        json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 0

    table = tasks_report.render_table(ordered)
    print(table)
    print("\nWarnings:")
    if warnings:
        for warning in warnings:
            print(f"- {warning}")
    else:
        print("- none")
    return 0


def cmd_frontier(args: argparse.Namespace) -> int:
    out_path = None
    if args.out is not None:
        out_path = args.out if args.out.is_absolute() else ROOT / args.out
    result = frontier_mod.compute_frontier(limit=max(0, args.limit))
    if args.format == "json":
        print(json.dumps([entry.as_dict() for entry in result], ensure_ascii=False, indent=2))
    else:
        print(frontier_mod.render_table(result))
    if out_path is not None:
        receipt_path = frontier_mod.write_receipt(result, out_path, limit=max(0, args.limit))
        print(f"wrote receipt → {receipt_path.relative_to(ROOT)}")
    return 0


def cmd_critic(args: argparse.Namespace) -> int:
    anomalies = critic_mod.detect_anomalies()
    if args.format == "json":
        print(json.dumps(anomalies, ensure_ascii=False, indent=2))
    else:
        print(critic_mod.render_table(anomalies))

    receipt_path = None
    if args.out:
        out_path = args.out if args.out.is_absolute() else (ROOT / args.out)
        receipt_path = critic_mod.write_receipt(anomalies, out_path)
        print(f"wrote receipt → {receipt_path.relative_to(ROOT)}")

    if args.emit_bus:
        if receipt_path is None:
            print("::error:: --emit-bus requires --out for provenance")
            return 2
        emitted = []
        for anomaly in anomalies:
            claim_path = critic_mod._emit_bus_claim(anomaly, receipt_path)
            emitted.append(claim_path.relative_to(ROOT).as_posix())
        if emitted:
            print("emitted bus claims:")
            for item in emitted:
                print(f"  - {item}")
    return 0


def cmd_tms(args: argparse.Namespace) -> int:
    conflicts = tms_mod.detect_conflicts()
    if args.format == "json":
        print(json.dumps(conflicts, ensure_ascii=False, indent=2))
    else:
        print(tms_mod.render_table(conflicts))

    receipt_path = None
    if args.out:
        out_path = args.out if args.out.is_absolute() else (ROOT / args.out)
        receipt_path = tms_mod.write_receipt(conflicts, out_path)
        print(f"wrote receipt → {receipt_path.relative_to(ROOT)}")

    if args.emit_plan:
        if receipt_path is None:
            print("::error:: --emit-plan requires --out for provenance")
            return 2
        emitted = []
        for conflict in conflicts:
            plan_path = tms_mod._emit_plan(conflict, receipt_path)
            emitted.append(plan_path.relative_to(ROOT).as_posix())
        if emitted:
            print("emitted plans:")
            for item in emitted:
                print(f"  - {item}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
