#!/usr/bin/env python3
"""Convergence metrics pipeline (collect → aggregate → guard)."""
from __future__ import annotations

import argparse
import json
import math
import statistics
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RECON_DIR = ROOT / "_report" / "reconciliation"
DEFAULT_RECEIPT_SYNC_DIR = ROOT / "_report" / "network" / "receipt_sync"
DEFAULT_PLANS_DIR = ROOT / "_plans"
DEFAULT_AUTONOMY_AUDIT_DIR = ROOT / "_report" / "usage" / "autonomy-audit"
DEFAULT_DATASET = ROOT / "artifacts" / "convergence" / "records-latest.json"
DEFAULT_REPORT_DIR = ROOT / "_report" / "reconciliation" / "convergence-metrics"


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_json(path: Path) -> Mapping[str, object] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _iter_json_files(base: Path) -> Iterable[Path]:
    if not base.exists():
        return []
    if base.is_file():
        return [base]
    return sorted(p for p in base.rglob("*.json") if p.is_file())


def _coerce_float(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _average(values: Sequence[float | None]) -> float | None:
    nums = [float(v) for v in values if isinstance(v, (int, float))]
    if not nums:
        return None
    return statistics.fmean(nums)


def _collect_reconciliation_metrics(base: Path) -> tuple[list[float], list[float]]:
    hash_rates: list[float] = []
    anchor_latencies: list[float] = []
    for path in _iter_json_files(base):
        payload = _load_json(path)
        if not isinstance(payload, Mapping):
            continue
        metrics = payload.get("metrics")
        source = metrics if isinstance(metrics, Mapping) else payload
        rate = _coerce_float(source.get("hash_match_rate"))
        if rate is not None:
            hash_rates.append(rate)
        latency = _coerce_float(source.get("anchor_latency_minutes"))
        if latency is not None:
            anchor_latencies.append(latency)
    return hash_rates, anchor_latencies


def _collect_gap_rates(base: Path) -> list[float]:
    gap_rates: list[float] = []
    for path in _iter_json_files(base):
        payload = _load_json(path)
        if not isinstance(payload, Mapping):
            continue
        rate = (
            _coerce_float(payload.get("gap_rate"))
            or _coerce_float((payload.get("summary") or {}).get("gap_rate") if isinstance(payload.get("summary"), Mapping) else None)
        )
        if rate is not None:
            gap_rates.append(rate)
    return gap_rates


@dataclass
class CmdStats:
    cmd_steps: int = 0
    total_steps: int = 0


def _collect_plan_cmd_stats(plans_dir: Path) -> CmdStats:
    stats = CmdStats()
    for path in _iter_json_files(plans_dir):
        payload = _load_json(path)
        if not isinstance(payload, Mapping):
            continue
        steps = payload.get("steps")
        if not isinstance(steps, list):
            continue
        for step in steps:
            if not isinstance(step, Mapping):
                continue
            stats.total_steps += 1
            text_bits = [
                str(step.get("title") or ""),
                str(step.get("notes") or ""),
            ]
            text = " ".join(text_bits).upper()
            if "CMD-" in text:
                stats.cmd_steps += 1
    return stats


@dataclass
class AutomationStats:
    correct: int = 0
    total: int = 0


def _collect_automation_stats(base: Path) -> AutomationStats:
    stats = AutomationStats()
    for path in _iter_json_files(base):
        payload = _load_json(path)
        if not isinstance(payload, Mapping):
            continue
        correct = payload.get("automation_correct") or payload.get("correct")
        total = payload.get("automation_total") or payload.get("total")
        if isinstance(correct, int) and isinstance(total, int) and total > 0:
            stats.correct += correct
            stats.total += total
    return stats


def cmd_collect(args: argparse.Namespace) -> int:
    recon_rates, anchor_latencies = _collect_reconciliation_metrics(args.reconciliation)
    gap_rates = _collect_gap_rates(args.receipt_sync)
    cmd_stats = _collect_plan_cmd_stats(args.plans)
    auto_stats = _collect_automation_stats(args.autonomy_audit)

    payload = {
        "generated_at": _iso_now(),
        "reconciliation_rates": recon_rates,
        "anchor_latencies": anchor_latencies,
        "receipt_gap_rates": gap_rates,
        "plan_cmd_stats": {"cmd_steps": cmd_stats.cmd_steps, "total_steps": cmd_stats.total_steps},
        "automation_stats": {"correct": auto_stats.correct, "total": auto_stats.total},
        "sources": {
            "reconciliation": str(args.reconciliation),
            "receipt_sync": str(args.receipt_sync),
            "plans": str(args.plans),
            "autonomy_audit": str(args.autonomy_audit),
        },
    }

    out_path = args.out if args.out.is_absolute() else ROOT / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rel = _rel(out_path)
    print(f"convergence dataset → {rel}")
    return 0


def _rel(path: Path) -> Path:
    try:
        return path.relative_to(ROOT)
    except ValueError:
        return path


def _write_latest(summary_path: Path, report_dir: Path) -> None:
    latest = report_dir / "latest.json"
    latest.write_text(summary_path.read_text(encoding="utf-8"), encoding="utf-8")


def cmd_aggregate(args: argparse.Namespace) -> int:
    source = args.source if args.source.is_absolute() else ROOT / args.source
    if not source.exists():
        raise SystemExit(f"dataset missing: {source}")
    payload = _load_json(source)
    if not isinstance(payload, Mapping):
        raise SystemExit(f"invalid dataset: {source}")

    recon_rates = payload.get("reconciliation_rates") or []
    gap_rates = payload.get("receipt_gap_rates") or []
    anchor_latencies = payload.get("anchor_latencies") or []
    cmd_stats = payload.get("plan_cmd_stats") or {}
    auto_stats = payload.get("automation_stats") or {}

    hash_rate = _average(recon_rates)
    gap_rate = _average(gap_rates)
    latency = _average(anchor_latencies)
    cmd_steps = int(cmd_stats.get("cmd_steps") or 0)
    cmd_total = int(cmd_stats.get("total_steps") or 0)
    cmd_ratio = (cmd_steps / cmd_total) if cmd_total > 0 else None
    auto_correct = int(auto_stats.get("correct") or 0)
    auto_total = int(auto_stats.get("total") or 0)
    automation_accuracy = (auto_correct / auto_total) if auto_total > 0 else None

    metrics = {
        "hash_match_rate": hash_rate,
        "receipt_gap_rate": gap_rate,
        "anchor_latency_minutes": latency,
        "cmd_tag_ratio": cmd_ratio,
        "automation_accuracy": automation_accuracy,
    }

    thresholds = {
        "hash_match_rate": 0.95,
        "receipt_gap_rate": 0.05,
        "anchor_latency_minutes": 30.0,
        "cmd_tag_ratio": 0.80,
        "automation_accuracy": 0.90,
    }

    summary = {
        "generated_at": _iso_now(),
        "window_days": args.window_days,
        "metrics": metrics,
        "thresholds": thresholds,
        "dataset": str(_rel(source)),
        "sources": payload.get("sources") or {},
    }

    report_dir = args.report_dir if args.report_dir.is_absolute() else ROOT / args.report_dir
    report_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    summary_path = report_dir / f"convergence-{timestamp}.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _write_latest(summary_path, report_dir)
    rel_summary = _rel(summary_path)
    print(f"convergence summary → {rel_summary}")

    markdown_path = args.markdown
    if markdown_path is None:
        markdown_path = ROOT / "docs" / "reports" / "convergence-metrics.md"
    elif not markdown_path.is_absolute():
        markdown_path = ROOT / markdown_path
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(_render_markdown(summary), encoding="utf-8")
    print(f"convergence dashboard → {_rel(markdown_path)}")
    return 0


def _render_markdown(summary: Mapping[str, object]) -> str:
    metrics = summary.get("metrics") or {}
    thresholds = summary.get("thresholds") or {}

    def row(name: str, key: str, comparator: str) -> str:
        value = metrics.get(key)
        threshold = thresholds.get(key)
        met = _threshold_status(value, threshold, comparator)
        formatted = "-" if value is None else f"{value:.3f}"
        thresh_str = "-" if threshold is None else f"{threshold:.3f}"
        return f"| {name} | {formatted} | {thresh_str} | {met} |"

    lines = [
        "# Convergence Metrics",
        "",
        f"- Generated at: {summary.get('generated_at', '-')}",
        f"- Window (days): {summary.get('window_days', '-')}",
        "",
        "| Metric | Value | Threshold | Status |",
        "| --- | --- | --- | --- |",
        row("Hash match rate", "hash_match_rate", "min"),
        row("Receipt gap rate", "receipt_gap_rate", "max"),
        row("Anchor latency (min)", "anchor_latency_minutes", "max"),
        row("CMD tag ratio", "cmd_tag_ratio", "min"),
        row("Automation accuracy", "automation_accuracy", "min"),
        "",
        f"_Dataset: {summary.get('dataset')}_",
    ]
    return "\n".join(lines) + "\n"


def _threshold_status(value: object, threshold: object, comparator: str) -> str:
    if not isinstance(value, (int, float)) or not isinstance(threshold, (int, float)):
        return "n/a"
    if comparator == "min":
        return "ok" if value >= threshold else "FAIL"
    if comparator == "max":
        return "ok" if value <= threshold else "FAIL"
    return "n/a"


def cmd_guard(args: argparse.Namespace) -> int:
    summary_path = args.summary if args.summary.is_absolute() else ROOT / args.summary
    summary = _load_json(summary_path)
    if not isinstance(summary, Mapping):
        raise SystemExit(f"invalid summary: {summary_path}")
    metrics = summary.get("metrics") or {}
    failures: list[str] = []

    def _check(name: str, key: str, comparator: str, limit: float) -> None:
        value = metrics.get(key)
        if not isinstance(value, (int, float)):
            return
        if comparator == "min" and value < limit:
            failures.append(f"{name} {value:.3f} < {limit:.3f}")
        if comparator == "max" and value > limit:
            failures.append(f"{name} {value:.3f} > {limit:.3f}")

    _check("hash_match_rate", "hash_match_rate", "min", args.hash_min)
    _check("receipt_gap_rate", "receipt_gap_rate", "max", args.gap_max)
    _check("anchor_latency_minutes", "anchor_latency_minutes", "max", args.latency_max)
    _check("cmd_tag_ratio", "cmd_tag_ratio", "min", args.cmd_min)
    _check("automation_accuracy", "automation_accuracy", "min", args.automation_min)

    if failures:
        print("convergence guard failures:")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("convergence guard: all metrics within thresholds")
    return 0


def configure_subparser(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    sub = parser.add_subparsers(dest="command", required=True)

    collect = sub.add_parser("collect", help="Collect convergence dataset")
    collect.add_argument("--reconciliation", type=Path, default=DEFAULT_RECON_DIR)
    collect.add_argument("--receipt-sync", type=Path, default=DEFAULT_RECEIPT_SYNC_DIR)
    collect.add_argument("--plans", type=Path, default=DEFAULT_PLANS_DIR)
    collect.add_argument("--autonomy-audit", type=Path, default=DEFAULT_AUTONOMY_AUDIT_DIR)
    collect.add_argument("--out", type=Path, default=DEFAULT_DATASET)
    collect.set_defaults(func=cmd_collect)

    aggregate = sub.add_parser("aggregate", help="Aggregate dataset into summary + dashboard")
    aggregate.add_argument("--source", type=Path, default=DEFAULT_DATASET)
    aggregate.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    aggregate.add_argument("--markdown", type=Path, help="Optional markdown output path")
    aggregate.add_argument("--window-days", type=int, default=14)
    aggregate.set_defaults(func=cmd_aggregate)

    guard = sub.add_parser("guard", help="Validate convergence summary against thresholds")
    guard.add_argument("--summary", type=Path, required=True)
    guard.add_argument("--hash-min", type=float, default=0.95)
    guard.add_argument("--gap-max", type=float, default=0.05)
    guard.add_argument("--latency-max", type=float, default=30.0)
    guard.add_argument("--cmd-min", type=float, default=0.80)
    guard.add_argument("--automation-min", type=float, default=0.90)
    guard.set_defaults(func=cmd_guard)

    return parser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    return configure_subparser(parser)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
