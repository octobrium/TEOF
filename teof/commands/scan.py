from __future__ import annotations

import datetime as dt
import json
from argparse import Namespace
from pathlib import Path
from functools import partial
from typing import Callable, Dict, List

from tools.autonomy import critic as critic_mod
from tools.autonomy import ethics_gate as ethics_mod
from tools.autonomy import frontier as frontier_mod
from tools.autonomy import tms as tms_mod

from ._utils import DEFAULT_ROOT, relpath
SCAN_COMPONENTS = ("frontier", "critic", "tms", "ethics")


def _scan_root() -> Path:
    for module in (frontier_mod, critic_mod, tms_mod, ethics_mod):
        root = getattr(module, "ROOT", None)
        if root is not None:
            return Path(root)
    return DEFAULT_ROOT


def _rel(base: Path) -> Callable[[Path], str]:
    return partial(relpath, base=base)


def run(args: Namespace) -> int:
    limit = max(0, getattr(args, "limit", 10))
    fmt = getattr(args, "format", "table")
    summary_only = bool(getattr(args, "summary", False)) and fmt == "table"
    base_root = _scan_root()
    rel = _rel(base_root)
    out_dir = getattr(args, "out", None)
    if out_dir is not None and not out_dir.is_absolute():
        out_dir = base_root / out_dir

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
    critic_anomalies: List[dict[str, object]] = []
    tms_conflicts: List[dict[str, object]] = []
    ethics_violations: List[dict[str, object]] = []

    if "frontier" in selected:
        frontier_entries = frontier_mod.compute_frontier(limit=limit)
    if "critic" in selected:
        critic_anomalies = critic_mod.detect_anomalies()
    if "tms" in selected:
        tms_conflicts = tms_mod.detect_conflicts()
    if "ethics" in selected:
        ethics_violations = ethics_mod.detect_violations()

    receipts: Dict[str, Path] = {}
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

    bus_emitted: Dict[str, List[str]] = {}
    plans_emitted: List[str] = []

    if args.emit_bus and out_dir is not None:
        critic_receipt = receipts.get("critic")
        ethics_receipt = receipts.get("ethics")
        if critic_receipt is not None and "critic" in selected:
            emitted = []
            for anomaly in critic_anomalies:
                claim_path = critic_mod.emit_bus_claim(anomaly, critic_receipt)
                emitted.append(rel(claim_path))
            if emitted:
                bus_emitted["critic"] = emitted
        if ethics_receipt is not None and "ethics" in selected:
            emitted = []
            for violation in ethics_violations:
                claim_path = ethics_mod.emit_bus_claim(violation, ethics_receipt)
                emitted.append(rel(claim_path))
            if emitted:
                bus_emitted["ethics"] = emitted

    if args.emit_plan and out_dir is not None and "tms" in selected:
        tms_receipt = receipts.get("tms")
        if tms_receipt is not None:
            for conflict in tms_conflicts:
                plan_path = tms_mod.emit_plan(conflict, tms_receipt)
                plans_emitted.append(rel(plan_path))

    counts = {
        "frontier": len(frontier_entries) if "frontier" in selected else 0,
        "critic": len(critic_anomalies) if "critic" in selected else 0,
        "tms": len(tms_conflicts) if "tms" in selected else 0,
        "ethics": len(ethics_violations) if "ethics" in selected else 0,
    }

    if fmt == "json":
        payload: dict[str, object] = {
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
            payload["receipts"] = {name: rel(path) for name, path in receipts.items()}
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


def register(subparsers: "argparse._SubParsersAction[object]") -> None:
    import argparse

    parser = subparsers.add_parser(
        "scan",
        help="Run frontier, critic, tms, and ethics loops in one pass",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Frontier entry limit (default: 10)",
    )
    parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format (default: table)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Directory to write receipts (files: frontier.json, critic.json, tms.json, ethics.json)",
    )
    parser.add_argument(
        "--emit-bus",
        action="store_true",
        help="Emit bus claims for critic/ethics results (requires --out)",
    )
    parser.add_argument(
        "--emit-plan",
        action="store_true",
        help="Emit plan skeletons for TMS conflicts (requires --out)",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print component counts instead of detailed tables",
    )
    parser.add_argument(
        "--only",
        action="append",
        choices=SCAN_COMPONENTS,
        help="Run only the specified component(s) (repeat flag for multiple)",
    )
    parser.add_argument(
        "--skip",
        action="append",
        choices=SCAN_COMPONENTS,
        help="Skip the specified component(s) (repeat flag for multiple)",
    )
    parser.set_defaults(func=run)


__all__ = ["register", "run"]
