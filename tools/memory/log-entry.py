#!/usr/bin/env python3
"""Append a memory log entry."""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

try:  # Import lazily so tests can monkeypatch module-level paths.
    from tools.memory import memory
except Exception as exc:  # pragma: no cover - defensive import guard.
    raise RuntimeError("Failed to import tools.memory.memory") from exc


def _log_path() -> Path:
    return memory.LOG_PATH


def default_actor() -> str:
    try:
        result = subprocess.run(
            ["git", "config", "user.name"],
            check=True,
            capture_output=True,
            text=True,
        )
        name = result.stdout.strip()
        return name or "unknown"
    except subprocess.CalledProcessError:
        return "unknown"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Append a line to memory/log.jsonl")
    parser.add_argument("--summary", required=True)
    parser.add_argument("--ref", required=True, help="Branch/PR/commit reference")
    parser.add_argument("--actor", default=default_actor())
    parser.add_argument("--artifact", action="append", default=[], help="Artifact path or URL")
    parser.add_argument("--signature", action="append", default=[], help="Signature identifier")
    parser.add_argument("--task", help="Optional task identifier associated with the run")
    parser.add_argument("--layer", help="Optional L-layer tag (e.g. L4)")
    parser.add_argument("--systemic-scale", type=int, help="Optional systemic scale (1-10)")
    parser.add_argument("--receipt", action="append", default=[], help="Receipt path supporting the entry")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    log_path = _log_path()
    if not log_path.exists():
        raise SystemExit("memory/log.jsonl missing")

    event: dict[str, object] = {
        "summary": args.summary,
        "actor": args.actor,
        "ref": args.ref,
        "artifacts": list(args.artifact),
        "signatures": list(args.signature),
    }
    if args.task:
        event["task"] = args.task
    if args.layer:
        event["layer"] = args.layer
    if args.systemic_scale is not None:
        event["systemic_scale"] = args.systemic_scale
    if args.receipt:
        event["receipts"] = list(args.receipt)

    payload = memory.write_log(event)
    print(
        "Appended memory entry",
        payload["ts"],
        "run_id=",
        payload.get("run_id"),
        "hash=",
        payload.get("hash_self"),
        "->",
        log_path,
    )


if __name__ == "__main__":
    main()
