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
from tools.autonomy import ethics_gate as ethics_mod
from tools.autonomy import frontier as frontier_mod
from tools.autonomy import tms as tms_mod

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXAMPLES_DIR = ROOT / "docs" / "examples" / "brief" / "inputs"
ARTIFACT_ROOT = ROOT / "artifacts" / "ocers_out"
SCAN_COMPONENTS = ("frontier", "critic", "tms", "ethics")


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

    scan = sub.add_parser(
        "scan",
        help="Run frontier, critic, tms, and ethics loops in one pass",
    )
    scan.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Frontier entry limit (default: 10)",
    )
    scan.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format (default: table)",
    )
    scan.add_argument(
        "--out",
        type=Path,
        help="Directory to write receipts (files: frontier.json, critic.json, tms.json, ethics.json)",
    )
    scan.add_argument(
        "--emit-bus",
        action="store_true",
        help="Emit bus claims for critic/ethics results (requires --out)",
    )
    scan.add_argument(
        "--emit-plan",
        action="store_true",
        help="Emit plan skeletons for TMS conflicts (requires --out)",
    )
    scan.add_argument(
        "--summary",
        action="store_true",
        help="Print component counts instead of detailed tables",
    )
    scan.add_argument(
        "--only",
        action="append",
        choices=SCAN_COMPONENTS,
        help="Run only the specified component(s) (repeat flag for multiple)",
    )
    scan.add_argument(
        "--skip",
        action="append",
        choices=SCAN_COMPONENTS,
        help="Skip the specified component(s) (repeat flag for multiple)",
    )
    scan.set_defaults(func=cmd_scan)

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

    ethics = sub.add_parser(
        "ethics",
        help="Enforce high-risk automation guardrails",
    )
    ethics.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format",
    )
    ethics.add_argument(
        "--out",
        type=Path,
        help="Optional path to write ethics receipt JSON",
    )
    ethics.add_argument(
        "--emit-bus",
        action="store_true",
        help="Emit review claims for high-risk items missing consent receipts",
    )
    ethics.set_defaults(func=cmd_ethics)

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


def cmd_scan(args: argparse.Namespace) -> int:
    limit = max(0, getattr(args, "limit", 10))
    fmt = getattr(args, "format", "table")
    summary_only = bool(getattr(args, "summary", False)) and fmt == "table"
    out_dir = getattr(args, "out", None)
    if out_dir is not None and not out_dir.is_absolute():
        out_dir = ROOT / out_dir

    if args.emit_bus and out_dir is None:
        print("::error:: --emit-bus requires --out for provenance")
        return 2
    if args.emit_plan and out_dir is None:
        print("::error:: --emit-plan requires --out for provenance")
        return 2

    selected = set(SCAN_COMPONENTS)
    if getattr(args, "only", None):
        selected = set(args.only)
    if getattr(args, "skip", None):
        selected -= set(args.skip)
    if not selected:
        print("::error:: no components selected for scan")
        return 2

    frontier_entries = []
    critic_anomalies: list[dict[str, object]] = []
    tms_conflicts: list[dict[str, object]] = []
    ethics_violations: list[dict[str, object]] = []

    if "frontier" in selected:
        frontier_entries = frontier_mod.compute_frontier(limit=limit)
    if "critic" in selected:
        critic_anomalies = critic_mod.detect_anomalies()
    if "tms" in selected:
        tms_conflicts = tms_mod.detect_conflicts()
    if "ethics" in selected:
        ethics_violations = ethics_mod.detect_violations()

    receipts: dict[str, Path] = {}
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        if "frontier" in selected:
            receipts["frontier"] = frontier_mod.write_receipt(
                frontier_entries, out_dir / "frontier.json", limit=limit
            )
        if "critic" in selected:
            receipts["critic"] = critic_mod.write_receipt(
                critic_anomalies, out_dir / "critic.json"
            )
        if "tms" in selected:
            receipts["tms"] = tms_mod.write_receipt(tms_conflicts, out_dir / "tms.json")
        if "ethics" in selected:
            receipts["ethics"] = ethics_mod.write_receipt(ethics_violations, out_dir / "ethics.json")

    def _rel(path: Path) -> str:
        try:
            return path.relative_to(ROOT).as_posix()
        except ValueError:
            return path.as_posix()

    bus_emitted: dict[str, list[str]] = {}
    plans_emitted: list[str] = []

    if args.emit_bus and out_dir is not None:
        critic_receipt = receipts.get("critic")
        ethics_receipt = receipts.get("ethics")
        if critic_receipt is not None and "critic" in selected:
            emitted = []
            for anomaly in critic_anomalies:
                claim_path = critic_mod._emit_bus_claim(anomaly, critic_receipt)
                emitted.append(_rel(claim_path))
            if emitted:
                bus_emitted["critic"] = emitted
        if ethics_receipt is not None and "ethics" in selected:
            emitted = []
            for violation in ethics_violations:
                claim_path = ethics_mod._emit_bus_claim(violation, ethics_receipt)
                emitted.append(_rel(claim_path))
            if emitted:
                bus_emitted["ethics"] = emitted

    if args.emit_plan and out_dir is not None and "tms" in selected:
        tms_receipt = receipts.get("tms")
        if tms_receipt is not None:
            for conflict in tms_conflicts:
                plan_path = tms_mod._emit_plan(conflict, tms_receipt)
                plans_emitted.append(_rel(plan_path))

    counts = {
        "frontier": len(frontier_entries) if "frontier" in selected else 0,
        "critic": len(critic_anomalies) if "critic" in selected else 0,
        "tms": len(tms_conflicts) if "tms" in selected else 0,
        "ethics": len(ethics_violations) if "ethics" in selected else 0,
    }

    if fmt == "json":
        payload = {
            "generated_at": dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "counts": counts,
        }
        if "frontier" in selected:
            payload["frontier"] = [entry.as_dict() for entry in frontier_entries]
        if "critic" in selected:
            payload["critic"] = critic_anomalies
        if "tms" in selected:
            payload["tms"] = tms_conflicts
        if "ethics" in selected:
            payload["ethics"] = ethics_violations
        if receipts:
            payload["receipts"] = {name: _rel(path) for name, path in receipts.items()}
        if bus_emitted:
            payload["emitted_bus"] = bus_emitted
        if plans_emitted:
            payload["emitted_plans"] = plans_emitted
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    ordered = [comp for comp in SCAN_COMPONENTS if comp in selected]
    if summary_only:
        print("Counts:")
        for comp in ordered:
            print(f"- {comp}: {counts[comp]}")
    else:
        for idx, comp in enumerate(ordered):
            if idx:
                print()
            if comp == "frontier":
                print("== Frontier ==")
                print(frontier_mod.render_table(frontier_entries))
                print(f"entries: {counts['frontier']}")
            elif comp == "critic":
                print("== Critic ==")
                print(critic_mod.render_table(critic_anomalies))
                print(f"anomalies: {counts['critic']}")
            elif comp == "tms":
                print("== TMS ==")
                print(tms_mod.render_table(tms_conflicts))
                print(f"conflicts: {counts['tms']}")
            elif comp == "ethics":
                print("== Ethics ==")
                print(ethics_mod.render_table(ethics_violations))
                print(f"violations: {counts['ethics']}")

    if receipts:
        print("\nReceipts:")
        for name, path in receipts.items():
            print(f"- {name}: {_rel(path)}")

    if bus_emitted:
        print("\nBus claims:")
        for source, paths in bus_emitted.items():
            for item in paths:
                print(f"- {source}: {item}")

    if plans_emitted:
        print("\nPlans:")
        for path in plans_emitted:
            print(f"- {path}")

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


def cmd_ethics(args: argparse.Namespace) -> int:
    violations = ethics_mod.detect_violations()
    if args.format == "json":
        print(json.dumps(violations, ensure_ascii=False, indent=2))
    else:
        print(ethics_mod.render_table(violations))

    receipt_path = None
    if args.out:
        out_path = args.out if args.out.is_absolute() else (ROOT / args.out)
        receipt_path = ethics_mod.write_receipt(violations, out_path)
        print(f"wrote receipt → {receipt_path.relative_to(ROOT)}")

    if args.emit_bus:
        if receipt_path is None:
            print("::error:: --emit-bus requires --out for provenance")
            return 2
        emitted = []
        for violation in violations:
            claim_path = ethics_mod._emit_bus_claim(violation, receipt_path)
            emitted.append(claim_path.relative_to(ROOT).as_posix())
        if emitted:
            print("emitted bus claims:")
            for path in emitted:
                print(f"  - {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
