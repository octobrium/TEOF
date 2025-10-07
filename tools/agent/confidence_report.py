#!/usr/bin/env python3
"""Summarise logged confidence reports for a given agent."""
from __future__ import annotations

import argparse
import json
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DIR = ROOT / "_report" / "agent"


@dataclass
class ConfidenceEntry:
    ts: str
    agent: str
    confidence: float
    note: str | None


def _coerce_float(value: object) -> float | None:
    if isinstance(value, (int, float)):
        result = float(value)
        if 0.0 <= result <= 1.0:
            return result
    return None


def load_entries(path: Path) -> list[ConfidenceEntry]:
    entries: list[ConfidenceEntry] = []
    if not path.exists():
        return entries
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        confidence = _coerce_float(payload.get("confidence"))
        if confidence is None:
            continue
        ts = str(payload.get("ts") or "-")
        agent = str(payload.get("agent") or "-")
        note = payload.get("note") if isinstance(payload.get("note"), str) else None
        entries.append(ConfidenceEntry(ts=ts, agent=agent, confidence=confidence, note=note))
    return entries


def summarise(entries: Iterable[ConfidenceEntry], *, warn_threshold: float) -> dict[str, object]:
    entries = list(entries)
    if not entries:
        return {
            "count": 0,
            "average": None,
            "median": None,
            "high_confidence_count": 0,
            "warn_threshold": warn_threshold,
            "latest": None,
        }
    confidences = [entry.confidence for entry in entries]
    high_conf = [entry for entry in entries if entry.confidence >= warn_threshold]
    latest = entries[-1]
    return {
        "count": len(entries),
        "average": statistics.fmean(confidences),
        "median": statistics.median(confidences),
        "high_confidence_count": len(high_conf),
        "warn_threshold": warn_threshold,
        "latest": {
            "ts": latest.ts,
            "confidence": latest.confidence,
            "note": latest.note,
        },
    }


def format_summary(summary: dict[str, object]) -> str:
    count = summary["count"]
    if count == 0:
        return "No confidence entries found."
    average = summary.get("average")
    median = summary.get("median")
    latest = summary.get("latest") or {}
    lines = [
        f"Total entries: {count}",
        f"Average confidence: {average:.3f}" if average is not None else "Average confidence: n/a",
        f"Median confidence: {median:.3f}" if median is not None else "Median confidence: n/a",
        f"Entries ≥ {summary['warn_threshold']:.2f}: {summary['high_confidence_count']}",
    ]
    latest_ts = latest.get("ts", "-")
    latest_conf = latest.get("confidence")
    latest_line = "Latest entry: ts=%s confidence=%s" % (
        latest_ts,
        f"{latest_conf:.3f}" if isinstance(latest_conf, (int, float)) else latest_conf,
    )
    if latest.get("note"):
        latest_line += f" note={latest['note']}"
    lines.append(latest_line)
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent", required=True, help="Agent identifier")
    parser.add_argument(
        "--dir",
        type=Path,
        default=DEFAULT_DIR,
        help="Directory containing _report/agent/<id>/confidence.jsonl",
    )
    parser.add_argument(
        "--warn-threshold",
        type=float,
        default=0.9,
        help="Confidence threshold to highlight (default: 0.9)",
    )
    parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not 0.0 <= args.warn_threshold <= 1.0:
        parser.error("--warn-threshold must be between 0.0 and 1.0")

    log_path = args.dir / args.agent / "confidence.jsonl"
    entries = load_entries(log_path)
    summary = summarise(entries, warn_threshold=args.warn_threshold)

    if args.format == "json":
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(format_summary(summary))
        if summary["count"] > 0 and summary["high_confidence_count"] > 0:
            print(
                f"warning: {summary['high_confidence_count']} entries meet or exceed "
                f"the {args.warn_threshold:.2f} threshold"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

