#!/usr/bin/env python3
"""Append a memory log entry."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parents[2] / "memory" / "log.jsonl"


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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Append a line to memory/log.jsonl")
    parser.add_argument("--summary", required=True)
    parser.add_argument("--ref", required=True, help="Branch/PR/commit reference")
    parser.add_argument("--actor", default=default_actor())
    parser.add_argument("--artifact", action="append", default=[], help="Artifact path or URL")
    parser.add_argument("--signature", action="append", default=[], help="Signature identifier")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not LOG_PATH.exists():
        raise SystemExit("memory/log.jsonl missing")

    record = {
        "ts": dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "actor": args.actor,
        "summary": args.summary,
        "ref": args.ref,
        "artifacts": args.artifact,
        "signatures": args.signature,
    }

    with LOG_PATH.open("a", encoding="utf-8") as handle:
        json.dump(record, handle, ensure_ascii=False, separators=(",", ":"))
        handle.write("\n")

    print("Appended memory entry", record["ts"], "->", LOG_PATH)


if __name__ == "__main__":
    main()
