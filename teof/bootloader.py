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
from . import status_report

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


if __name__ == "__main__":
    sys.exit(main())
