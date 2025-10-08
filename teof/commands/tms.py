from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from tools.autonomy import tms as tms_mod

from ._utils import module_root, relpath


def run(args: Namespace) -> int:
    conflicts = tms_mod.detect_conflicts()
    if args.format == "json":
        print(json.dumps(conflicts, ensure_ascii=False, indent=2))
    else:
        print(tms_mod.render_table(conflicts))

    base_root = module_root(tms_mod)
    receipt_path = None
    if args.out:
        out_path = args.out if args.out.is_absolute() else (base_root / args.out)
        receipt_path = tms_mod.write_receipt(conflicts, out_path)
        print(f"wrote receipt → {relpath(receipt_path, base_root)}")

    if args.emit_plan:
        if receipt_path is None:
            print("::error:: --emit-plan requires --out for provenance")
            return 2
        emitted = []
        for conflict in conflicts:
            plan_path = tms_mod.emit_plan(conflict, receipt_path)
            emitted.append(relpath(plan_path, base_root))
        if emitted:
            print("emitted plans:")
            for item in emitted:
                print(f"  - {item}")
    return 0


def register(subparsers: "argparse._SubParsersAction[object]") -> None:
    import argparse

    parser = subparsers.add_parser(
        "tms",
        help="Detect fact conflicts (truth maintenance system)",
    )
    parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Optional path to write TMS receipt JSON",
    )
    parser.add_argument(
        "--emit-plan",
        action="store_true",
        help="Emit plan skeletons for detected conflicts",
    )
    parser.set_defaults(func=run)


__all__ = ["register", "run"]
