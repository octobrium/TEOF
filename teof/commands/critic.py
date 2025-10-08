from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from tools.autonomy import critic as critic_mod

from ._utils import module_root, relpath


def run(args: Namespace) -> int:
    anomalies = critic_mod.detect_anomalies()
    if args.format == "json":
        print(json.dumps(anomalies, ensure_ascii=False, indent=2))
    else:
        print(critic_mod.render_table(anomalies))

    base_root = module_root(critic_mod)
    receipt_path = None
    if args.out:
        out_path = args.out if args.out.is_absolute() else (base_root / args.out)
        receipt_path = critic_mod.write_receipt(anomalies, out_path)
        print(f"wrote receipt → {relpath(receipt_path, base_root)}")

    if args.emit_bus:
        if receipt_path is None:
            print("::error:: --emit-bus requires --out for provenance")
            return 2
        emitted = []
        for anomaly in anomalies:
            claim_path = critic_mod.emit_bus_claim(anomaly, receipt_path)
            emitted.append(relpath(claim_path, base_root))
        if emitted:
            print("emitted bus claims:")
            for item in emitted:
                print(f"  - {item}")
    return 0


def register(subparsers: "argparse._SubParsersAction[object]") -> None:
    import argparse

    parser = subparsers.add_parser(
        "critic",
        help="Detect anomalies and emit repair suggestions",
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
        help="Optional path to write critic receipt JSON",
    )
    parser.add_argument(
        "--emit-bus",
        action="store_true",
        help="Emit repair tasks into _bus/claims (requires --out)",
    )
    parser.set_defaults(func=run)


__all__ = ["register", "run"]
