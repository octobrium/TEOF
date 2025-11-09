#!/usr/bin/env python3
"""Automate evidence_usage scans plus targeted prune cadence receipts."""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any, List, Sequence

from tools.maintenance import evidence_usage, prune_artifacts

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT_SUBDIR = Path("_report") / "usage" / "evidence-prune"
DEFAULT_TARGETS = ("_report/usage",)
POINTER_NAME = "latest.json"
ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"


def _utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _iso_timestamp(when: dt.datetime | None = None) -> str:
    return (when or _utc_now()).strftime(ISO_FMT)


def _stamp_token(when: dt.datetime | None = None) -> str:
    return (when or _utc_now()).strftime("%Y%m%dT%H%M%SZ")


def _rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _resolve_out_dir(root: Path, out_arg: Path | None) -> Path:
    if out_arg is None:
        return (root / DEFAULT_OUT_SUBDIR).resolve()
    return out_arg.resolve() if out_arg.is_absolute() else (root / out_arg).resolve()


def _run_evidence_scan(root: Path, out_dir: Path, *, orphan_limit: int) -> tuple[Path, dict[str, Any]]:
    entries = evidence_usage._build_index(root)  # type: ignore[attr-defined]
    report = evidence_usage.analyse_index(entries, orphan_limit=orphan_limit)
    stamp = _stamp_token()
    evidence_path = out_dir / f"evidence-{stamp}.json"
    payload = {
        "generated_at": _iso_timestamp(),
        "root": str(root),
        "report": report,
    }
    _write_json(evidence_path, payload)
    return evidence_path, report


def _is_under(parent: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(parent)
        return True
    except ValueError:
        return False


def _run_prune(
    root: Path,
    out_dir: Path,
    *,
    targets: Sequence[str],
    cutoff_hours: float,
    apply_moves: bool,
    evidence_receipt: Path,
) -> tuple[Path, dict[str, Any]]:
    stamp = _stamp_token()
    cutoff = _utc_now() - dt.timedelta(hours=cutoff_hours)
    raw_moves = prune_artifacts.discover_moves(
        root,
        targets,
        cutoff,
        stamp,
    )
    moves: List[prune_artifacts.MovePlan] = []
    for move in raw_moves:
        if _is_under(out_dir, move.source):
            continue
        moves.append(move)
    if apply_moves and moves:
        prune_artifacts.execute_moves(moves, dry_run=False)

    move_rows = []
    for move in moves:
        src_rel, dst_rel = move.relative_paths(root)
        move_rows.append(
            {
                "source": src_rel,
                "destination": dst_rel,
                "newest_mtime": move.newest_mtime.strftime(ISO_FMT),
            }
        )
    payload = {
        "generated_at": _iso_timestamp(),
        "stamp": stamp,
        "root": str(root),
        "targets": list(targets),
        "cutoff_hours": cutoff_hours,
        "applied": apply_moves,
        "move_count": len(move_rows),
        "skipped_moves": len(raw_moves) - len(moves),
        "moves": move_rows,
        "evidence_receipt": _rel(evidence_receipt, root),
    }
    prune_path = out_dir / f"prune-{stamp}.json"
    _write_json(prune_path, payload)
    return prune_path, payload


def _update_pointer(
    out_dir: Path,
    root: Path,
    *,
    evidence_path: Path,
    evidence_report: dict[str, Any],
    prune_info: dict[str, Any] | None,
) -> Path:
    pointer_payload: dict[str, Any] = {
        "generated_at": _iso_timestamp(),
        "evidence_receipt": _rel(evidence_path, root),
        "summary": evidence_report.get("summary"),
        "orphan_receipts": evidence_report.get("summary", {}).get("orphan_receipts"),
        "plans_missing_receipts": evidence_report.get("summary", {}).get("plans_missing_receipts"),
    }
    if prune_info is not None:
        pointer_payload["prune"] = {
            "receipt": prune_info.get("receipt"),
            "applied": prune_info.get("applied"),
            "move_count": prune_info.get("move_count"),
            "cutoff_hours": prune_info.get("cutoff_hours"),
            "stamp": prune_info.get("stamp"),
        }
    pointer_path = out_dir / POINTER_NAME
    _write_json(pointer_path, pointer_payload)
    return pointer_path


def cmd_run(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    out_dir = _resolve_out_dir(root, args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    evidence_path, report = _run_evidence_scan(root, out_dir, orphan_limit=args.orphan_limit)

    prune_paths: dict[str, Any] | None = None
    prune_receipt_path: Path | None = None
    if not args.skip_prune:
        prune_receipt_path, prune_payload = _run_prune(
            root,
            out_dir,
            targets=tuple(args.targets or DEFAULT_TARGETS),
            cutoff_hours=args.cutoff_hours,
            apply_moves=bool(args.apply_prune),
            evidence_receipt=evidence_path,
        )
        prune_payload["receipt"] = _rel(prune_receipt_path, root)
        prune_paths = prune_payload

    pointer = _update_pointer(
        out_dir,
        root,
        evidence_path=evidence_path,
        evidence_report=report,
        prune_info=prune_paths,
    )

    print(f"evidence receipt → {_rel(evidence_path, root)}")
    if prune_receipt_path is not None:
        print(f"prune receipt → {_rel(prune_receipt_path, root)}")
    print(f"pointer updated → {_rel(pointer, root)}")
    return 0


def _load_pointer(root: Path, out_dir: Path) -> dict[str, Any]:
    pointer_path = out_dir / POINTER_NAME
    if not pointer_path.exists():
        raise FileNotFoundError(f"pointer missing: {_rel(pointer_path, root)}")
    return json.loads(pointer_path.read_text(encoding="utf-8"))


def cmd_guard(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    out_dir = _resolve_out_dir(root, args.out)
    errors: List[str] = []
    try:
        pointer = _load_pointer(root, out_dir)
    except FileNotFoundError as exc:
        errors.append(str(exc))
        pointer = {}

    if pointer:
        generated_at = pointer.get("generated_at")
        parsed = None
        if generated_at:
            try:
                parsed = dt.datetime.strptime(generated_at, ISO_FMT).replace(tzinfo=dt.timezone.utc)
            except ValueError:
                errors.append(f"pointer has invalid timestamp: {generated_at}")
        else:
            errors.append("pointer missing generated_at")
        if parsed:
            age_hours = (_utc_now() - parsed).total_seconds() / 3600
            if age_hours > args.max_age_hours:
                errors.append(
                    f"pointer older than {args.max_age_hours}h (age={age_hours:.1f}h)",
                )

        orphans = int(pointer.get("orphan_receipts") or 0)
        prune_info = pointer.get("prune")
        if orphans > args.max_orphans:
            if not prune_info or not prune_info.get("applied"):
                errors.append(
                    f"orphan_receipts={orphans} exceeds max {args.max_orphans} without applied prune receipt",
                )

    if errors:
        for message in errors:
            print(f"::error:: {message}")
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_cmd = subparsers.add_parser("run", help="Capture evidence_usage summary and optional prune receipts")
    run_cmd.add_argument("--root", type=Path, default=ROOT, help="Repository root (default: repo)")
    run_cmd.add_argument("--out", type=Path, help="Receipt output directory (default: _report/usage/evidence-prune)")
    run_cmd.add_argument("--orphan-limit", type=int, default=20, help="Orphan entries to record in detail (default: 20)")
    run_cmd.add_argument(
        "--target",
        action="append",
        dest="targets",
        help="Directory to prune (repeatable, default: _report/usage)",
    )
    run_cmd.add_argument(
        "--cutoff-hours",
        type=float,
        default=168.0,
        help="Artifacts older than this are eligible for pruning (default: 168h / 7 days)",
    )
    run_cmd.add_argument(
        "--apply-prune",
        action="store_true",
        help="Actually move stale artifacts (default: dry-run only)",
    )
    run_cmd.add_argument(
        "--skip-prune",
        action="store_true",
        help="Skip prune planning entirely (still writes evidence receipt)",
    )
    run_cmd.set_defaults(func=cmd_run)

    guard_cmd = subparsers.add_parser("guard", help="Validate evidence/prune cadence receipts exist and are fresh")
    guard_cmd.add_argument("--root", type=Path, default=ROOT, help="Repository root (default: repo)")
    guard_cmd.add_argument("--out", type=Path, help="Receipt directory (default: _report/usage/evidence-prune)")
    guard_cmd.add_argument(
        "--max-age-hours",
        type=float,
        default=24.0,
        help="Maximum age in hours for latest pointer (default: 24h)",
    )
    guard_cmd.add_argument(
        "--max-orphans",
        type=int,
        default=0,
        help="Allowed orphan_receipts count before requiring a prune run (default: 0)",
    )
    guard_cmd.set_defaults(func=cmd_guard)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    func = getattr(args, "func", None)
    if not callable(func):
        parser.print_help()
        return 2
    return func(args)


if __name__ == "__main__":
    raise SystemExit(main())
