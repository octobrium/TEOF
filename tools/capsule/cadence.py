"""Capsule cadence helpers (generate receipts for CI guards)."""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Iterable, Sequence

ROOT = Path(__file__).resolve().parents[2]


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _default_consensus_path() -> Path:
    return ROOT / "_report" / "consensus" / "summary-latest.json"


def _default_receipts() -> list[Path]:
    return [
        ROOT / "capsule" / "README.md",
        ROOT / "capsule" / "current" / "hashes.json",
        ROOT / "governance" / "anchors.json",
    ]


def _detect_capsule_version(capsule_dir: Path) -> str:
    current = capsule_dir / "current"
    if current.is_symlink():
        try:
            target = current.resolve()
        except FileNotFoundError:
            return "current"
        if target.parent == capsule_dir:
            return target.name
        return _relative(target)
    if current.is_dir():
        return "current"
    versions = sorted(
        (path.name for path in capsule_dir.iterdir() if path.is_dir() and path.name.startswith("v")),
        reverse=True,
    )
    return versions[0] if versions else "unknown"


def build_summary(
    *,
    consensus_path: Path | None = None,
    receipts: Sequence[Path] | None = None,
    now: dt.datetime | None = None,
) -> dict[str, object]:
    receipts = list(receipts) if receipts is not None else _default_receipts()
    summary_path = _default_consensus_path() if consensus_path is None else consensus_path
    capsule_dir = ROOT / "capsule"
    timestamp = (now or dt.datetime.utcnow()).replace(microsecond=0)
    required = sorted({_relative(path) for path in receipts})

    return {
        "generated_at": timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "capsule_version": _detect_capsule_version(capsule_dir),
        "required_receipts": required,
        "consensus_summary": _relative(summary_path),
    }


def _write_summary(data: dict[str, object], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def cmd_summary(args: argparse.Namespace) -> int:
    summary_path = Path(args.out) if args.out else ROOT / "_report" / "capsule" / "summary-latest.json"
    data = build_summary()
    _write_summary(data, summary_path)
    print(f"capsule cadence: wrote { _relative(summary_path) }")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m tools.capsule.cadence", description="Capsule cadence helpers")
    sub = parser.add_subparsers(dest="command", required=True)

    summary = sub.add_parser("summary", help="Generate capsule cadence summary JSON")
    summary.add_argument("--out", type=str, help="Optional output path (defaults to _report/capsule/summary-latest.json)")
    summary.set_defaults(func=cmd_summary)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
