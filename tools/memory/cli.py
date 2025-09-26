"""Command-line helpers for the TEOF memory layer."""
from __future__ import annotations

import argparse
import json
import hashlib
from pathlib import Path
from typing import Any, Iterable

from . import memory


def _load_log_entries() -> list[dict[str, Any]]:
    if not memory.LOG_PATH.exists():
        return []
    entries: list[dict[str, Any]] = []
    with memory.LOG_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def _rehash(entry: dict[str, Any]) -> str:
    payload = dict(entry)
    payload.pop("hash_self", None)
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def cmd_doctor(_: argparse.Namespace) -> int:
    entries = _load_log_entries()
    errors: list[str] = []
    prev_hash: str | None = None
    for idx, entry in enumerate(entries):
        actual_prev = entry.get("hash_prev")
        if actual_prev != prev_hash:
            errors.append(f"log[{idx}] hash_prev mismatch (expected {prev_hash}, found {actual_prev})")
        recomputed = _rehash(entry)
        if recomputed != entry.get("hash_self"):
            errors.append(f"log[{idx}] hash_self mismatch (expected {recomputed}, found {entry.get('hash_self')})")
        run_id = entry.get("run_id")
        if run_id:
            run_dir = memory.RUNS_DIR / str(run_id)
            if not run_dir.exists():
                errors.append(f"missing run capsule for {run_id}")
        prev_hash = entry.get("hash_self")

    if errors:
        for err in errors:
            print(f"ERROR: {err}")
        return 1
    print("memory doctor: ok")
    return 0


def cmd_timeline(args: argparse.Namespace) -> int:
    entries = _load_log_entries()
    if args.task:
        entries = [entry for entry in entries if entry.get("task") == args.task]
    entries = entries[-args.limit :]
    for entry in entries:
        ts = entry.get("ts")
        summary = entry.get("summary")
        task = entry.get("task", "-")
        print(f"{ts} :: {task} :: {summary}")
    if not entries:
        print("(no entries)")
    return 0


def _load_run_meta(run_id: str) -> dict[str, Any]:
    meta_path = memory.RUNS_DIR / run_id / "meta.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"run capsule {run_id} missing meta.json")
    return json.loads(meta_path.read_text(encoding="utf-8"))


def cmd_diff(args: argparse.Namespace) -> int:
    base = _load_run_meta(args.run)
    if args.against:
        other = _load_run_meta(args.against)
    else:
        entries = _load_log_entries()
        other_entry = None
        for entry in reversed(entries):
            run = entry.get("run_id")
            if run and run != args.run:
                other_entry = run
                break
        if other_entry is None:
            print("No prior run to diff against")
            return 1
        other = _load_run_meta(other_entry)
    diffs: list[str] = []
    for key in sorted(set(base.keys()) | set(other.keys())):
        if base.get(key) != other.get(key):
            diffs.append(f"{key}: {base.get(key)} != {other.get(key)}")
    if diffs:
        for line in diffs:
            print(line)
    else:
        print("runs identical")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="teof memory", description="Memory diagnostics")
    sub = parser.add_subparsers(dest="command", required=True)

    doctor = sub.add_parser("doctor", help="Validate memory hash chain and capsules")
    doctor.set_defaults(func=cmd_doctor)

    timeline = sub.add_parser("timeline", help="Show recent memory events")
    timeline.add_argument("--task", help="Filter to a specific task id")
    timeline.add_argument("--limit", type=int, default=10, help="Number of entries to show")
    timeline.set_defaults(func=cmd_timeline)

    diff = sub.add_parser("diff", help="Compare run capsules")
    diff.add_argument("--run", required=True, help="Run id to inspect")
    diff.add_argument("--against", help="Run id to compare against (defaults to previous run)")
    diff.set_defaults(func=cmd_diff)

    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    func = getattr(args, "func")
    return int(func(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
