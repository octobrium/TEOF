#!/usr/bin/env python3
"""Confidence calibration pipeline (collect → aggregate → alerts)."""
from __future__ import annotations

import argparse
import json
import math
import re
import statistics
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from tools.agent.confidence_report import ConfidenceEntry, load_entries


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_AGENT_DIR = ROOT / "_report" / "agent"
DEFAULT_PLANS_DIR = ROOT / "_plans"
DEFAULT_ARTIFACT_PATH = ROOT / "artifacts" / "confidence_calibration" / "latest.json"
DEFAULT_REPORT_DIR = ROOT / "_report" / "usage" / "confidence-calibration"
PLAN_ID_PATTERN = re.compile(r"plan[_-]?id[:= ](?P<plan>[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9-]+)", re.IGNORECASE)
PLAN_INLINE_PATTERN = re.compile(r"\b(20[0-9]{2}-[0-9]{2}-[0-9]{2}-[a-z0-9-]+)\b")


@dataclass
class CalibrationRecord:
    ts: str
    agent: str
    confidence: float
    note: str | None
    plan_id: str | None = None


@dataclass
class AgentMetrics:
    agent: str
    samples: int
    window_samples: int
    mean_delta: float | None
    mean_abs_delta: float | None
    overconfidence_rate: float
    underconfidence_rate: float
    brier_score: float | None
    latest_ts: str | None
    latest_confidence: float | None
    latest_plan: str | None
    alerts: list[str]


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_ts(value: str) -> datetime:
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)


def _plan_from_note(note: str | None) -> str | None:
    if not note:
        return None
    match = PLAN_ID_PATTERN.search(note)
    if match:
        return match.group("plan").strip()
    match = PLAN_INLINE_PATTERN.search(note)
    if match:
        return match.group(1).strip()
    return None


def discover_confidence_records(base_dir: Path) -> list[CalibrationRecord]:
    records: list[CalibrationRecord] = []
    if not base_dir.exists():
        return records
    for agent_dir in sorted(path for path in base_dir.iterdir() if path.is_dir()):
        log_path = agent_dir / "confidence.jsonl"
        if not log_path.exists():
            continue
        entries = load_entries(log_path)
        for entry in entries:
            plan_id = getattr(entry, "plan_id", None)
            if not plan_id:
                plan_id = _plan_from_note(entry.note)
            records.append(
                CalibrationRecord(
                    ts=entry.ts,
                    agent=entry.agent or agent_dir.name,
                    confidence=entry.confidence,
                    note=entry.note,
                    plan_id=plan_id,
                )
            )
    records.sort(key=lambda record: (_parse_ts(record.ts), record.agent))
    return records


def serialize_records(records: Sequence[CalibrationRecord]) -> dict[str, object]:
    return {
        "generated_at": _iso_now(),
        "count": len(records),
        "records": [
            {
                "ts": record.ts,
                "agent": record.agent,
                "confidence": record.confidence,
                "note": record.note,
                "plan_id": record.plan_id,
            }
            for record in records
        ],
    }


def _load_serialized_records(path: Path) -> list[CalibrationRecord]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    items = payload.get("records") or []
    records: list[CalibrationRecord] = []
    for entry in items:
        if not isinstance(entry, Mapping):
            continue
        confidence = entry.get("confidence")
        if not isinstance(confidence, (int, float)):
            continue
        records.append(
            CalibrationRecord(
                ts=str(entry.get("ts") or "-"),
                agent=str(entry.get("agent") or "-"),
                confidence=float(confidence),
                note=entry.get("note") if isinstance(entry.get("note"), str) else None,
                plan_id=entry.get("plan_id") if isinstance(entry.get("plan_id"), str) else None,
            )
        )
    records.sort(key=lambda record: (_parse_ts(record.ts), record.agent))
    return records


def load_plan_outcomes(plans_dir: Path) -> dict[str, bool]:
    outcomes: dict[str, bool] = {}
    if not plans_dir.exists():
        return outcomes
    for plan_path in sorted(plans_dir.glob("*.plan.json")):
        try:
            data = json.loads(plan_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        plan_id = data.get("plan_id")
        status = str(data.get("status", "")).lower()
        if isinstance(plan_id, str):
            outcomes[plan_id] = status == "done"
    return outcomes


def _attach_outcomes(records: Iterable[CalibrationRecord], outcomes: Mapping[str, bool]) -> list[tuple[CalibrationRecord, float | None]]:
    enriched: list[tuple[CalibrationRecord, float | None]] = []
    for record in records:
        outcome = None
        if record.plan_id and record.plan_id in outcomes:
            outcome = 1.0 if outcomes[record.plan_id] else 0.0
        enriched.append((record, outcome))
    return enriched


def _compute_agent_metrics(
    records: Sequence[tuple[CalibrationRecord, float | None]],
    *,
    window: int,
    delta_threshold: float,
) -> AgentMetrics:
    filtered = [(rec, outcome) for rec, outcome in records if outcome is not None]
    if window > 0:
        filtered = filtered[-window:]
    deltas = [(rec.confidence - outcome) for rec, outcome in filtered if outcome is not None]
    over = [delta for delta in deltas if delta > delta_threshold]
    under = [delta for delta in deltas if delta < -delta_threshold]
    brier = [(rec.confidence - outcome) ** 2 for rec, outcome in filtered if outcome is not None]
    latest = filtered[-1][0] if filtered else (records[-1][0] if records else None)
    alerts: list[str] = []
    mean_delta = statistics.fmean(deltas) if deltas else None
    if mean_delta is not None and abs(mean_delta) > delta_threshold:
        alerts.append("mean_delta")
    over_rate = len(over) / len(filtered) if filtered else 0.0
    under_rate = len(under) / len(filtered) if filtered else 0.0
    if over_rate > 0.3:
        alerts.append("overconfidence_rate")
    brier_score = statistics.fmean(brier) if brier else None
    return AgentMetrics(
        agent=records[-1][0].agent if records else "-",
        samples=len(records),
        window_samples=len(filtered),
        mean_delta=mean_delta,
        mean_abs_delta=statistics.fmean([abs(delta) for delta in deltas]) if deltas else None,
        overconfidence_rate=over_rate,
        underconfidence_rate=under_rate,
        brier_score=brier_score,
        latest_ts=latest.ts if latest else None,
        latest_confidence=latest.confidence if latest else None,
        latest_plan=latest.plan_id if latest else None,
        alerts=alerts,
    )


def aggregate_records(
    records: Iterable[CalibrationRecord],
    *,
    window: int,
    delta_threshold: float,
    plan_outcomes: Mapping[str, bool],
) -> dict[str, object]:
    grouped: dict[str, list[CalibrationRecord]] = {}
    for record in records:
        grouped.setdefault(record.agent, []).append(record)
    for agent, items in grouped.items():
        enriched = _attach_outcomes(items, plan_outcomes)
        grouped[agent] = enriched

    metrics: list[AgentMetrics] = []
    for items in grouped.values():
        if items:
            metrics.append(_compute_agent_metrics(items, window=window, delta_threshold=delta_threshold))
    metrics.sort(key=lambda entry: entry.agent)
    alerts = [entry.agent for entry in metrics if entry.alerts]
    global_brier = statistics.fmean([entry.brier_score for entry in metrics if entry.brier_score is not None]) if metrics else None
    return {
        "generated_at": _iso_now(),
        "window": window,
        "delta_threshold": delta_threshold,
        "agents": [
            {
                "agent": entry.agent,
                "samples": entry.samples,
                "window_samples": entry.window_samples,
                "mean_delta": entry.mean_delta,
                "mean_abs_delta": entry.mean_abs_delta,
                "brier_score": entry.brier_score,
                "overconfidence_rate": entry.overconfidence_rate,
                "underconfidence_rate": entry.underconfidence_rate,
                "latest": {
                    "ts": entry.latest_ts,
                    "confidence": entry.latest_confidence,
                    "plan_id": entry.latest_plan,
                },
                "alerts": entry.alerts,
            }
            for entry in metrics
        ],
        "alerts": alerts,
        "global": {
            "agents": len(metrics),
            "brier_score": global_brier,
        },
    }


def render_markdown(summary: Mapping[str, object]) -> str:
    lines = [
        "# Confidence Calibration Summary",
        "",
        f"- Generated at: {summary.get('generated_at')}",
        f"- Window: {summary.get('window')} reports per agent",
        f"- Delta threshold: {summary.get('delta_threshold')}",
        f"- Agents processed: {len(summary.get('agents') or [])}",
        f"- Alerts: {', '.join(summary.get('alerts') or []) or 'none'}",
        "",
        "| Agent | samples | window | mean Δ | |Δ| | overconf | underconf | brier | latest plan |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    agents = summary.get("agents") or []
    if not agents:
        lines.append("| _none_ | 0 | 0 | – | – | – | – | – | – | – |")
    else:
            for entry in agents:
                lines.append(
                    "| {agent} | {samples} | {window} | {mean_delta} | {mean_abs_delta} | {over} | {under} | {brier} | {plan} |".format(
                        agent=entry.get("agent", "-"),
                        samples=entry.get("samples", 0),
                        window=entry.get("window_samples", 0),
                        mean_delta=_fmt(entry.get("mean_delta")),
                        mean_abs_delta=_fmt(entry.get("mean_abs_delta")),
                        over=_fmt(entry.get("overconfidence_rate"), digits=2),
                        under=_fmt(entry.get("underconfidence_rate"), digits=2),
                        brier=_fmt(entry.get("brier_score")),
                        plan=(entry.get("latest") or {}).get("plan_id") or "–",
                    )
                )
    return "\n".join(lines) + "\n"


def _fmt(value: object, *, digits: int = 3) -> str:
    if isinstance(value, (int, float)) and not math.isnan(value):
        return f"{value:.{digits}f}"
    return "-"


def configure_parser(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    sub = parser.add_subparsers(dest="command", required=True)

    collect = sub.add_parser("collect", help="Collect raw confidence reports")
    collect.add_argument("--base-dir", type=Path, default=DEFAULT_AGENT_DIR, help="Directory containing _report/agent/*/confidence.jsonl")
    collect.add_argument("--out", type=Path, default=DEFAULT_ARTIFACT_PATH, help="Path to write collected dataset JSON")
    collect.set_defaults(func=cmd_collect)

    aggregate = sub.add_parser("aggregate", help="Aggregate collected reports into metrics & receipts")
    aggregate.add_argument("--source", type=Path, default=DEFAULT_ARTIFACT_PATH, help="Path to collected dataset JSON")
    aggregate.add_argument("--plans-dir", type=Path, default=DEFAULT_PLANS_DIR, help="Directory containing plan JSON files")
    aggregate.add_argument("--window", type=int, default=20, help="Window size per agent (default: 20, 0 = unlimited)")
    aggregate.add_argument("--delta-threshold", type=float, default=0.15, help="Tolerance for calibration delta")
    aggregate.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR, help="Output directory for summary receipts")
    aggregate.add_argument("--markdown", type=Path, help="Optional markdown output path")
    aggregate.set_defaults(func=cmd_aggregate)

    alerts = sub.add_parser("alerts", help="Evaluate summary and emit alerts")
    alerts.add_argument("--summary", type=Path, required=True, help="Summary JSON emitted by aggregate step")
    alerts.add_argument("--mean-delta-limit", type=float, default=0.15, help="Abs mean delta threshold for alerting")
    alerts.add_argument("--overconfidence-limit", type=float, default=0.30, help="Overconfidence rate threshold")
    alerts.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR, help="Output directory for alert receipts")
    alerts.add_argument("--emit-bus", action="store_true", help="Emit bus status event when alerts fire")
    alerts.add_argument("--agent", help="Agent id for bus events (defaults to manifest)")
    alerts.set_defaults(func=cmd_alerts)

    return parser


def cmd_collect(args: argparse.Namespace) -> int:
    base_dir = args.base_dir if args.base_dir.is_absolute() else ROOT / args.base_dir
    records = discover_confidence_records(base_dir)
    out_path = args.out if args.out.is_absolute() else ROOT / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = serialize_records(records)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"collected {payload['count']} confidence entries → {out_path.relative_to(ROOT)}")
    return 0


def cmd_aggregate(args: argparse.Namespace) -> int:
    source = args.source if args.source.is_absolute() else ROOT / args.source
    if not source.exists():
        raise SystemExit(f"collect dataset missing: {source}")
    records = _load_serialized_records(source)
    plans_dir = args.plans_dir if args.plans_dir.is_absolute() else ROOT / args.plans_dir
    outcomes = load_plan_outcomes(plans_dir)
    summary = aggregate_records(
        records,
        window=max(args.window, 0),
        delta_threshold=max(args.delta_threshold, 0.0),
        plan_outcomes=outcomes,
    )

    report_dir = args.report_dir if args.report_dir.is_absolute() else ROOT / args.report_dir
    report_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    summary_path = report_dir / f"summary-{timestamp}.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"confidence summary → {summary_path.relative_to(ROOT)}")

    markdown_path = args.markdown
    if markdown_path is None:
        markdown_path = report_dir / f"summary-{timestamp}.md"
    elif not markdown_path.is_absolute():
        markdown_path = ROOT / markdown_path
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(render_markdown(summary), encoding="utf-8")
    print(f"confidence dashboard → {markdown_path.relative_to(ROOT)}")
    return 0


def _default_manifest_agent() -> str | None:
    manifest = ROOT / "AGENT_MANIFEST.json"
    if manifest.exists():
        try:
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            agent_id = payload.get("agent_id")
            if isinstance(agent_id, str) and agent_id.strip():
                return agent_id.strip()
        except json.JSONDecodeError:
            return None
    return None


def cmd_alerts(args: argparse.Namespace) -> int:
    summary_path = args.summary if args.summary.is_absolute() else ROOT / args.summary
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    agents = summary.get("agents") or []
    triggered: list[dict[str, object]] = []
    for entry in agents:
        mean_delta = entry.get("mean_delta")
        over_rate = entry.get("overconfidence_rate", 0.0)
        reasons: list[str] = []
        if isinstance(mean_delta, (int, float)) and abs(mean_delta) > args.mean_delta_limit:
            reasons.append("mean_delta")
        if isinstance(over_rate, (int, float)) and over_rate > args.overconfidence_limit:
            reasons.append("overconfidence_rate")
        if reasons:
            triggered.append(
                {
                    "agent": entry.get("agent"),
                    "reasons": reasons,
                    "mean_delta": mean_delta,
                    "overconfidence_rate": over_rate,
                }
            )
    report_dir = args.report_dir if args.report_dir.is_absolute() else ROOT / args.report_dir
    report_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    alerts_path = report_dir / f"alerts-{timestamp}.json"
    payload = {
        "generated_at": _iso_now(),
        "summary": str(summary_path.relative_to(ROOT)),
        "mean_delta_limit": args.mean_delta_limit,
        "overconfidence_limit": args.overconfidence_limit,
        "alerts": triggered,
    }
    alerts_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"confidence alerts → {alerts_path.relative_to(ROOT)} (count={len(triggered)})")

    if triggered and args.emit_bus:
        agent_id = args.agent or _default_manifest_agent()
        if not agent_id:
            raise SystemExit("cannot emit bus event: agent id missing (use --agent)")
        summary_text = ", ".join(f"{item['agent']}[{','.join(item['reasons'])}]" for item in triggered)
        subprocess.run(
            [
                "python3",
                "-m",
                "teof",
                "bus_event",
                "log",
                "--event",
                "status",
                "--task",
                "confidence-alert",
                "--summary",
                f"Confidence drift detected: {summary_text}",
            ],
            cwd=ROOT,
            check=False,
        )
    return 1 if triggered else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    return configure_parser(parser)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
