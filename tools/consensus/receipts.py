#!/usr/bin/env python3
"""Append normalized consensus receipts under `_report/consensus/`."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DIR = ROOT / "_report" / "consensus"
ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime(ISO_FMT)


def _resolve_output(decision_id: str, output: Path | None) -> Path:
    if output is None:
        stamp = _iso_now().replace(":", "")
        output = Path(f"{decision_id}-{stamp}.jsonl")
    if not output.is_absolute():
        output = DEFAULT_DIR / output
    return output.resolve()


def append_receipt(
    *,
    decision_id: str,
    summary: str,
    agent_id: str,
    event: str,
    receipts: Sequence[str] | None = None,
    metadata: dict[str, str] | None = None,
    output: Path | None = None,
) -> Path:
    """Append a consensus receipt and return the filesystem path."""

    path = _resolve_output(decision_id, output)
    path.parent.mkdir(parents=True, exist_ok=True)

    payload: dict[str, object] = {
        "decision_id": decision_id,
        "summary": summary,
        "agent_id": agent_id,
        "event": event,
        "ts": _iso_now(),
    }
    if receipts:
        payload["receipts"] = list(receipts)
    if metadata:
        payload["meta"] = dict(metadata)

    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Append consensus receipts")
    parser.add_argument("--decision", required=True, help="Decision identifier")
    parser.add_argument("--summary", required=True, help="Receipt summary")
    parser.add_argument("--agent", required=True, help="Agent id recording the receipt")
    parser.add_argument("--event", default="consensus", help="Event name (default: %(default)s)")
    parser.add_argument("--receipt", action="append", dest="receipts", help="Reference receipt (repeatable)")
    parser.add_argument("--meta", action="append", help="Additional key=value metadata")
    parser.add_argument(
        "--output",
        help="Optional filename or path for the receipt (relative paths go under _report/consensus/)",
    )
    return parser


def _parse_meta(pairs: Sequence[str] | None) -> dict[str, str]:
    meta: dict[str, str] = {}
    if not pairs:
        return meta
    for item in pairs:
        key, sep, value = item.partition("=")
        if not sep:
            raise SystemExit(f"invalid metadata entry '{item}', expected key=value")
        meta[key] = value
    return meta


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    output: Path | None = Path(args.output) if args.output else None
    meta = _parse_meta(args.meta)
    append_receipt(
        decision_id=args.decision,
        summary=args.summary,
        agent_id=args.agent,
        event=args.event,
        receipts=args.receipts or [],
        metadata=meta,
        output=output,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
