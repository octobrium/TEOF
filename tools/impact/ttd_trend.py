"""Analyse TTΔ direction-of-travel history and emit trend summaries."""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT / "memory" / "impact" / "ttd.jsonl"

SPARKLINE_CHARS = ["_", ".", "-", "=", "+", "*", "^", "#"]


@dataclass
class TrendSeries:
    metric: str
    field: str
    values: list[float]
    timestamps: list[datetime]

    @property
    def latest(self) -> float | None:
        return self.values[-1] if self.values else None

    @property
    def delta(self) -> float | None:
        if len(self.values) < 2:
            return None
        return self.values[-1] - self.values[0]

    @property
    def slope_per_entry(self) -> float | None:
        if len(self.values) < 2:
            return None
        return (self.values[-1] - self.values[0]) / (len(self.values) - 1)

    @property
    def sparkline(self) -> str:
        return build_sparkline(self.values)


METRIC_FIELDS: dict[str, str] = {
    "observation.capacity": "plan_to_first_receipt_median",
    "recursion.depth": "open_ratio",
    "sustainability.signal": "quickstart_age_hours",
    "optional.safe": "overall_trust",
}

STATUS_FIELDS: dict[str, str] = {
    "integrity.gap": "readiness_status",
    "sustainability.signal": "readiness_status",
}

ALERT_RULES = (
    ("integrity.gap", lambda payload: str(payload.get("readiness_status", "")).lower() != "green", "Integrity gap readiness requires attention"),
    ("sustainability.signal", lambda payload: str(payload.get("readiness_status", "")).lower() != "green", "Sustainability readiness requires attention"),
    ("optional.safe", lambda payload: isinstance(payload.get("overall_trust"), (int, float)) and float(payload["overall_trust"]) < 0.7, "Optional safety trust below 0.7"),
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="Path to memory/impact/ttd.jsonl (default: repo canonical)",
    )
    parser.add_argument(
        "--window",
        type=int,
        default=14,
        help="Number of most recent entries to analyse (default: 14)",
    )
    parser.add_argument(
        "--days",
        type=float,
        help="Optional time window (days) to filter entries",
    )
    parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format (default: table)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Optional path to write JSON summary",
    )
    return parser.parse_args(argv)


def load_entries(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    entries: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            entries.append(payload)
    return entries


def filter_entries(
    entries: Sequence[Mapping[str, object]],
    *,
    window: int,
    days: float | None,
) -> list[Mapping[str, object]]:
    items = list(entries)
    if days is not None and days >= 0:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        filtered: list[Mapping[str, object]] = []
        for entry in reversed(items):
            ts_raw = entry.get("ts")
            if isinstance(ts_raw, str):
                ts_dt = parse_dt(ts_raw)
                if ts_dt and ts_dt >= cutoff:
                    filtered.append(entry)
        items = list(reversed(filtered)) if filtered else []
    if window > 0 and len(items) > window:
        items = items[-window:]
    return items


def parse_dt(value: str) -> datetime | None:
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def numeric_series(entries: Sequence[Mapping[str, object]]) -> list[TrendSeries]:
    series: list[TrendSeries] = []
    for metric, field in METRIC_FIELDS.items():
        values: list[float] = []
        timestamps: list[datetime] = []
        for entry in entries:
            metrics_payload = entry.get("metrics")
            if not isinstance(metrics_payload, Mapping):
                continue
            payload = metrics_payload.get(metric)
            if not isinstance(payload, Mapping):
                continue
            value = payload.get(field)
            if not isinstance(value, (int, float)):
                continue
            ts_raw = entry.get("ts")
            ts = parse_dt(ts_raw) if isinstance(ts_raw, str) else None
            timestamps.append(ts or datetime.now(timezone.utc))
            values.append(float(value))
        series.append(TrendSeries(metric=metric, field=field, values=values, timestamps=timestamps))
    return series


def status_snapshot(entries: Sequence[Mapping[str, object]]) -> dict[str, str | None]:
    snapshot: dict[str, str | None] = {}
    if not entries:
        return snapshot
    latest = entries[-1]
    metrics_payload = latest.get("metrics")
    if not isinstance(metrics_payload, Mapping):
        return snapshot
    for metric, field in STATUS_FIELDS.items():
        payload = metrics_payload.get(metric)
        if isinstance(payload, Mapping):
            value = payload.get(field)
            snapshot[metric] = str(value) if value is not None else None
    return snapshot


def build_sparkline(values: Sequence[float]) -> str:
    if not values:
        return ""
    if len(values) == 1:
        return SPARKLINE_CHARS[-1]
    minimum = min(values)
    maximum = max(values)
    if math.isclose(minimum, maximum):
        return SPARKLINE_CHARS[len(SPARKLINE_CHARS) // 2] * len(values)
    scale = (maximum - minimum) or 1.0
    buckets = len(SPARKLINE_CHARS) - 1
    chars: list[str] = []
    for value in values:
        idx = int(round(((value - minimum) / scale) * buckets))
        idx = max(0, min(buckets, idx))
        chars.append(SPARKLINE_CHARS[idx])
    return "".join(chars)


def derive_trend(delta: float | None, tolerance: float = 1e-9) -> str | None:
    if delta is None:
        return None
    if abs(delta) <= tolerance:
        return "flat"
    return "up" if delta > 0 else "down"


def collect_alerts(entries: Sequence[Mapping[str, object]]) -> list[str]:
    if not entries:
        return []
    latest = entries[-1]
    metrics_payload = latest.get("metrics")
    if not isinstance(metrics_payload, Mapping):
        return []
    alerts: list[str] = []
    for metric, rule, message in ALERT_RULES:
        payload = metrics_payload.get(metric)
        if isinstance(payload, Mapping) and rule(payload):
            alerts.append(f"{metric}: {message}")
    return alerts


def to_payload(
    entries: Sequence[Mapping[str, object]],
    series: Sequence[TrendSeries],
    statuses: Mapping[str, str | None],
    alerts: Sequence[str],
    *,
    input_path: Path,
    window: int,
    days: float | None,
) -> dict[str, object]:
    payload_series: dict[str, object] = {}
    for item in series:
        payload_series[item.metric] = {
            "field": item.field,
            "latest": item.latest,
            "delta": item.delta,
            "slope_per_entry": item.slope_per_entry,
            "trend": derive_trend(item.delta),
            "sparkline": item.sparkline,
            "sample_size": len(item.values),
        }
    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "input": str(input_path),
        "entry_count": len(entries),
        "window": window,
        "days": days,
        "metrics": payload_series,
        "statuses": dict(statuses),
        "alerts": list(alerts),
    }


def render_table(series: Sequence[TrendSeries], statuses: Mapping[str, str | None], alerts: Sequence[str]) -> str:
    headers = ["Metric", "Field", "Latest", "Δ", "Trend", "Sparkline"]
    rows: list[list[str]] = []
    for item in series:
        latest = "n/a" if item.latest is None else f"{item.latest:.4g}"
        delta_val = item.delta
        delta = "n/a" if delta_val is None else f"{delta_val:+.3g}"
        trend = derive_trend(delta_val) or "n/a"
        sparkline = item.sparkline or ""
        rows.append([
            item.metric,
            item.field,
            latest,
            delta,
            trend,
            sparkline,
        ])
    widths = [len(header) for header in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))
    fmt = " ".join(f"{{:<{width}}}" for width in widths)
    lines = [fmt.format(*headers), "-" * (sum(widths) + len(widths) - 1)]
    for row in rows:
        lines.append(fmt.format(*row))
    if statuses:
        lines.append("")
        lines.append("Statuses:")
        for metric, status in statuses.items():
            lines.append(f"- {metric}: {status}")
    if alerts:
        lines.append("")
        lines.append("Alerts:")
        for alert in alerts:
            lines.append(f"! {alert}")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.window <= 0:
        raise SystemExit("--window must be positive")
    if args.days is not None and args.days < 0:
        raise SystemExit("--days must be non-negative")

    entries = load_entries(args.input)
    filtered = filter_entries(entries, window=args.window, days=args.days)
    series = numeric_series(filtered)
    statuses = status_snapshot(filtered)
    alerts = collect_alerts(filtered)
    payload = to_payload(
        filtered,
        series,
        statuses,
        alerts,
        input_path=args.input,
        window=args.window,
        days=args.days,
    )

    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_table(series, statuses, alerts))

    if args.out:
        output = args.out if args.out.is_absolute() else ROOT / args.out
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        try:
            rel = output.relative_to(ROOT)
        except ValueError:
            rel = output
        print(f"wrote summary → {rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
