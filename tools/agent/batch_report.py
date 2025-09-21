#!/usr/bin/env python3
"""Summarise batch refinement log receipts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = ROOT / "_report" / "usage" / "batch-refinement"


def load_logs(limit: int | None = None) -> List[dict]:
    if not LOG_DIR.exists():
        return []
    files = sorted(LOG_DIR.glob("batch-refinement-*.json"))
    if limit is not None:
        files = files[-limit:]
    logs: List[dict] = []
    for path in files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            data["_path"] = path
            logs.append(data)
        except json.JSONDecodeError:
            continue
    return logs


def format_log(entry: dict) -> str:
    summary = entry.get("operator_preset", {}).get("summary", "?")
    missing = entry.get("receipts_hygiene", {}).get("metrics", {}).get("plans_missing_receipts")
    slow = entry.get("receipts_hygiene", {}).get("metrics", {}).get("slow_plans") or []
    slow_top = slow[0][0] if slow else "-"
    generated = entry.get("generated_at")
    agent = entry.get("agent")
    path = entry.get("_path")
    return (
        f"{generated} | agent={agent} | summary={summary} | "
        f"missing={missing} | slowest={slow_top} | receipt={path}"
    )


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, help="Show only the most recent N entries")
    parser.add_argument("--json", action="store_true", help="Emit JSON array instead of text")
    args = parser.parse_args(argv)

    logs = load_logs(limit=args.limit)
    if args.json:
        serialisable = []
        for entry in logs:
            copy = dict(entry)
            path = copy.pop("_path", None)
            if path:
                copy["log_path"] = str(Path(path).relative_to(ROOT)) if Path(path).is_relative_to(ROOT) else str(path)
            serialisable.append(copy)
        print(json.dumps(serialisable, ensure_ascii=False, indent=2))
    else:
        if not logs:
            print("No batch refinement logs found.")
            return 0
        for entry in logs:
            print(format_log(entry))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
