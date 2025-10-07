#!/usr/bin/env python3
"""Aggregate agent confidence logs and flag overconfidence patterns."""
from __future__ import annotations

import argparse
import json
import statistics
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from tools.agent.confidence_report import ConfidenceEntry, load_entries

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DIR = ROOT / "_report" / "agent"

__all__ = [
    "AgentSummary",
    "build_parser",
    "build_report",
    "main",
    "run_watch",
    "scan_agents",
    "summarise_agent",
]


@dataclass
class AgentSummary:
    agent: str
    total_entries: int
    window_total: int
    high_count: int
    high_ratio: float
    average: float | None
    median: float | None
    latest_ts: str | None
    latest_confidence: float | None
    latest_note: str | None
    alert: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "agent": self.agent,
            "total_entries": self.total_entries,
            "window_total": self.window_total,
            "high_count": self.high_count,
            "high_ratio": self.high_ratio,
            "average": self.average,
            "median": self.median,
            "latest": {
                "ts": self.latest_ts,
                "confidence": self.latest_confidence,
                "note": self.latest_note,
            },
            "alert": self.alert,
        }


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _rel_to_root(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def summarise_agent(
    agent: str,
    entries: Sequence[ConfidenceEntry],
    *,
    warn_threshold: float,
    window: int,
    min_count: int,
    alert_ratio: float,
) -> AgentSummary:
    total_entries = len(entries)
    if window > 0:
        window_entries = entries[-window:]
    else:
        window_entries = entries
    window_total = len(window_entries)
    confidences = [entry.confidence for entry in window_entries]
    high_count = sum(1 for entry in window_entries if entry.confidence >= warn_threshold)
    high_ratio = (high_count / window_total) if window_total else 0.0
    average = statistics.fmean(confidences) if confidences else None
    median = statistics.median(confidences) if confidences else None
    latest = entries[-1] if entries else None
    alert = window_total >= min_count and high_ratio >= alert_ratio
    return AgentSummary(
        agent=agent,
        total_entries=total_entries,
        window_total=window_total,
        high_count=high_count,
        high_ratio=high_ratio,
        average=average,
        median=median,
        latest_ts=latest.ts if latest else None,
        latest_confidence=latest.confidence if latest else None,
        latest_note=latest.note if latest else None,
        alert=alert,
    )


def scan_agents(
    base_dir: Path,
    *,
    warn_threshold: float,
    window: int,
    min_count: int,
    alert_ratio: float,
) -> list[AgentSummary]:
    summaries: list[AgentSummary] = []
    if not base_dir.exists():
        return summaries
    for agent_dir in sorted(p for p in base_dir.iterdir() if p.is_dir()):
        agent_id = agent_dir.name
        log_path = agent_dir / "confidence.jsonl"
        if not log_path.exists():
            continue
        entries = load_entries(log_path)
        if not entries:
            continue
        summary = summarise_agent(
            agent_id,
            entries,
            warn_threshold=warn_threshold,
            window=window,
            min_count=min_count,
            alert_ratio=alert_ratio,
        )
        summaries.append(summary)
    return summaries


def build_report(
    summaries: Sequence[AgentSummary],
    *,
    warn_threshold: float,
    window: int,
    min_count: int,
    alert_ratio: float,
) -> dict[str, object]:
    alerts = [summary.agent for summary in summaries if summary.alert]
    return {
        "generated_at": _iso_now(),
        "warn_threshold": warn_threshold,
        "window": window,
        "min_count": min_count,
        "alert_ratio": alert_ratio,
        "agents": [summary.to_dict() for summary in summaries],
        "alerts": alerts,
    }


def _format_table(summaries: Sequence[AgentSummary]) -> str:
    if not summaries:
        return "No confidence logs found."
    lines = [
        "agent        total window high ratio  avg   median latest_ts              latest_conf alert"
    ]
    for summary in summaries:
        latest_conf = "-"
        if summary.latest_confidence is not None:
            latest_conf = f"{summary.latest_confidence:.2f}"
        latest_ts = summary.latest_ts or "-"
        avg_str = f"{summary.average:.2f}" if summary.average is not None else "-"
        median_str = f"{summary.median:.2f}" if summary.median is not None else "-"
        lines.append(
            f"{summary.agent:<12}{summary.total_entries:>5}  {summary.window_total:>5}  "
            f"{summary.high_count:>4} {summary.high_ratio:>5.2f}  {avg_str:>5}  {median_str:>6} "
            f"{latest_ts:<20} {latest_conf:<9} {'YES' if summary.alert else 'no '}"
        )
    return "\n".join(lines)


def _write_report(report: dict[str, object], directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = directory / f"confidence-watch-{timestamp}.json"
    with path.open("w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return path


def run_watch(
    *,
    base_dir: Path | None = None,
    warn_threshold: float = 0.9,
    window: int = 10,
    min_count: int = 5,
    alert_ratio: float = 0.6,
    report_dir: Path | None = None,
) -> tuple[list[AgentSummary], dict[str, object], Path | None]:
    """Execute the scan and optionally persist a report snapshot."""

    summaries = scan_agents(
        base_dir or DEFAULT_DIR,
        warn_threshold=warn_threshold,
        window=window,
        min_count=min_count,
        alert_ratio=alert_ratio,
    )
    report = build_report(
        summaries,
        warn_threshold=warn_threshold,
        window=window,
        min_count=min_count,
        alert_ratio=alert_ratio,
    )
    written: Path | None = None
    if report_dir is not None:
        written = _write_report(report, report_dir)
    return summaries, report, written


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
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
        help="Confidence threshold considered high (default: 0.9)",
    )
    parser.add_argument(
        "--window",
        type=int,
        default=10,
        help="Number of recent entries to evaluate (default: 10; 0 = all)",
    )
    parser.add_argument(
        "--min-count",
        type=int,
        default=5,
        help="Minimum entries in the evaluation window before alerts fire (default: 5)",
    )
    parser.add_argument(
        "--alert-ratio",
        type=float,
        default=0.6,
        help="Minimum fraction of high-confidence entries in the window to trigger an alert (default: 0.6)",
    )
    parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)",
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        help="Optional directory to write a JSON snapshot",
    )
    parser.add_argument(
        "--fail-on-alert",
        action="store_true",
        help="Exit with status 1 if any agent triggers an overconfidence alert",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not 0.0 <= args.warn_threshold <= 1.0:
        parser.error("--warn-threshold must be between 0.0 and 1.0")
    if not 0.0 <= args.alert_ratio <= 1.0:
        parser.error("--alert-ratio must be between 0.0 and 1.0")
    if args.window < 0:
        parser.error("--window must be zero or a positive integer")
    if args.min_count < 1:
        parser.error("--min-count must be at least 1")

    summaries = scan_agents(
        args.dir,
        warn_threshold=args.warn_threshold,
        window=args.window,
        min_count=args.min_count,
        alert_ratio=args.alert_ratio,
    )
    report = build_report(
        summaries,
        warn_threshold=args.warn_threshold,
        window=args.window,
        min_count=args.min_count,
        alert_ratio=args.alert_ratio,
    )

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(_format_table(summaries))
        if report["alerts"]:
            joined = ", ".join(report["alerts"])
            print(f"warning: overconfidence alerts for {joined}")

    if args.report_dir:
        written = _write_report(report, args.report_dir)
        print(f"report written to {_rel_to_root(written)}")

    if report["alerts"] and args.fail_on_alert:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
