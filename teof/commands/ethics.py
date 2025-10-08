from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from tools.autonomy import ethics_gate as ethics_mod

from ._utils import module_root, relpath


def run(args: Namespace) -> int:
    violations = ethics_mod.detect_violations()
    if args.format == "json":
        print(json.dumps(violations, ensure_ascii=False, indent=2))
    else:
        print(ethics_mod.render_table(violations))

    base_root = module_root(ethics_mod)
    receipt_path = None
    if args.out:
        out_path = args.out if args.out.is_absolute() else (base_root / args.out)
        receipt_path = ethics_mod.write_receipt(violations, out_path)
        print(f"wrote receipt → {relpath(receipt_path, base_root)}")

    if args.emit_bus:
        if receipt_path is None:
            print("::error:: --emit-bus requires --out for provenance")
            return 2
        emitted = []
        for violation in violations:
            claim_path = ethics_mod.emit_bus_claim(violation, receipt_path)
            emitted.append(relpath(claim_path, base_root))
        if emitted:
            print("emitted bus claims:")
            for path in emitted:
                print(f"  - {path}")
    return 0


def register(subparsers: "argparse._SubParsersAction[object]") -> None:
    import argparse

    parser = subparsers.add_parser(
        "ethics",
        help="Enforce high-risk automation guardrails",
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
        help="Optional path to write ethics receipt JSON",
    )
    parser.add_argument(
        "--emit-bus",
        action="store_true",
        help="Emit review claims for high-risk items missing consent receipts",
    )
    parser.set_defaults(func=run)


__all__ = ["register", "run"]
