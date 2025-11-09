"""Aggregate systemic health signals into a single receipt."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from tools.autonomy.shared import load_json, utc_timestamp, write_receipt_payload, atomic_write_text

ROOT = Path(__file__).resolve().parents[2]
BACKLOG_DIR = ROOT / "_report" / "usage" / "backlog-health"
MACRO_HYGIENE_PATH = ROOT / "_report" / "usage" / "macro-hygiene-status.json"
AUTONOMY_STATUS_PATH = ROOT / "_report" / "usage" / "autonomy-status.json"
MEMORY_LOG_PATH = ROOT / "memory" / "log.jsonl"
PLAN_DIR = ROOT / "_plans"
RADAR_DIR = ROOT / "_report" / "usage" / "systemic-radar"
DEFAULT_BASELINE = ROOT / "docs" / "automation" / "systemic-radar.baseline.json"


@dataclass
class AxisSignal:
    axis: str
    layer: str
    status: str
    detail: str
    receipts: list[str]
    metric: float | int | None = None
    threshold: float | int | None = None


def _load_baseline(path: Path) -> dict[str, Any]:
    data = load_json(path)
    if not isinstance(data, dict):
        raise RuntimeError(f"systemic radar baseline missing or invalid: {path}")
    return data


def _latest_backlog_receipt(threshold: int | None = None) -> AxisSignal:
    files = sorted(BACKLOG_DIR.glob("*.json"), key=lambda path: path.stat().st_mtime if path.exists() else 0.0)
    if not files:
        return AxisSignal(
            axis="S3",
            layer="L5",
            status="attention",
            detail="No backlog-health receipts found",
            receipts=[],
        )
    latest = files[-1]
    data = load_json(latest) or {}
    pending = int(data.get("pending_count") or 0)
    raw_threshold = threshold if threshold is not None else data.get("pending_threshold") or data.get("threshold") or 0
    threshold_val = int(raw_threshold)
    breached = bool(data.get("pending_threshold_breached"))
    status = "breach" if breached else ("ready" if pending >= threshold_val else "attention")
    detail = f"pending={pending}, threshold={threshold_val}, breached={breached}"
    return AxisSignal(
        axis="S3",
        layer="L5",
        status=status,
        detail=detail,
        receipts=[str(latest.relative_to(ROOT))],
        metric=pending,
        threshold=threshold_val,
    )


def _macro_hygiene_signal() -> AxisSignal:
    data = load_json(MACRO_HYGIENE_PATH) or {}
    summary = data.get("summary") if isinstance(data, dict) else None
    ready = bool(summary and summary.get("attention") == 0)
    status = "ready" if ready else "attention"
    detail = (
        f"ready={summary.get('ready', 0)} attention={summary.get('attention', 0)}"
        if isinstance(summary, dict)
        else "macro hygiene receipt missing"
    )
    receipts = [str(MACRO_HYGIENE_PATH.relative_to(ROOT))] if summary else []
    return AxisSignal(
        axis="S4",
        layer="L4",
        status=status,
        detail=detail,
        receipts=receipts,
    )


def _plan_receipt_ratio(threshold: float = 0.8) -> AxisSignal:
    plan_paths = list(PLAN_DIR.glob("*.plan.json"))
    done = 0
    covered = 0
    for path in plan_paths:
        data = load_json(path) or {}
        if (data.get("status") or "").lower() != "done":
            continue
        done += 1
        receipts = data.get("receipts")
        if isinstance(receipts, list) and receipts:
            covered += 1
    ratio = (covered / done) if done else 0.0
    status = "ready" if done and ratio >= threshold else "attention"
    detail = f"done={done}, with_receipts={covered}, ratio={ratio:.2f}, threshold={threshold}"
    return AxisSignal(
        axis="S6",
        layer="L4",
        status=status,
        detail=detail,
        receipts=[],
        metric=ratio,
        threshold=threshold,
    )


def _memory_signal(window_days: int = 7, target: int = 5) -> AxisSignal:
    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
    count = 0
    try:
        with MEMORY_LOG_PATH.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts = entry.get("ts")
                if not ts:
                    continue
                try:
                    observed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                except ValueError:
                    continue
                if observed >= cutoff:
                    count += 1
    except FileNotFoundError:
        pass
    status = "ready" if count >= target else "attention"
    detail = f"{count} entries within last {window_days}d (target >= {target})"
    receipts = [str(MEMORY_LOG_PATH.relative_to(ROOT))] if count else []
    return AxisSignal(
        axis="S1",
        layer="L0",
        status=status,
        detail=detail,
        receipts=receipts,
        metric=count,
        threshold=target,
    )


def _autonomy_signal(max_age_hours: int | None = None) -> AxisSignal:
    data = load_json(AUTONOMY_STATUS_PATH) or {}
    if not data:
        return AxisSignal(
            axis="S2",
            layer="L6",
            status="attention",
            detail="autonomy status receipt missing",
            receipts=[],
        )
    ready = bool(data.get("autonomy_guard_ready"))
    pending = data.get("pending_followups") or []
    generated = (
        data.get("generated_at")
        or data.get("summary", {}).get("generated_at")
        or data.get("hygiene", {}).get("generated_at")
    )
    age_hours = None
    breach = False
    if generated:
        try:
            ts = datetime.fromisoformat(generated.replace("Z", "+00:00"))
            age = datetime.now(timezone.utc) - ts
            age_hours = age.total_seconds() / 3600.0
            if max_age_hours and age > timedelta(hours=max_age_hours):
                breach = True
        except ValueError:
            pass
    status = "ready" if ready else "attention"
    if breach:
        status = "breach"
    detail = f"autonomy_guard_ready={ready}, pending_followups={len(pending)}, generated_at={generated}, age_hours={age_hours:.2f}" if generated and age_hours is not None else f"autonomy_guard_ready={ready}, pending_followups={len(pending)}"
    receipts = [str(AUTONOMY_STATUS_PATH.relative_to(ROOT))]
    return AxisSignal(
        axis="S2",
        layer="L6",
        status=status,
        detail=detail,
        receipts=receipts,
        metric=age_hours,
        threshold=max_age_hours,
    )


def _summarise(signals: Iterable[AxisSignal]) -> dict[str, int]:
    summary = {"ready": 0, "attention": 0, "breach": 0}
    for signal in signals:
        summary.setdefault(signal.status, 0)
        summary[signal.status] += 1
    return summary


def build_payload(args: argparse.Namespace, baseline: dict[str, Any]) -> dict[str, Any]:
    axes_cfg = {entry["axis"]: entry for entry in baseline.get("axes", []) if isinstance(entry, dict) and entry.get("axis")}
    signals = [
        _memory_signal(
            window_days=axes_cfg.get("S1", {}).get("window_days", args.memory_window_days),
            target=axes_cfg.get("S1", {}).get("threshold", args.memory_target),
        ),
        _autonomy_signal(max_age_hours=axes_cfg.get("S2", {}).get("max_age_hours")),
        _latest_backlog_receipt(threshold=axes_cfg.get("S3", {}).get("threshold")),
        _macro_hygiene_signal(),
        _plan_receipt_ratio(threshold=axes_cfg.get("S6", {}).get("threshold", args.plan_receipt_threshold)),
    ]
    payload = {
        "generated_at": utc_timestamp(),
        "version": 0,
        "axes": [
            {
                "axis": signal.axis,
                "layer": signal.layer,
                "status": signal.status,
                "detail": signal.detail,
                "receipts": signal.receipts,
                "metric": signal.metric,
                "threshold": signal.threshold,
            }
            for signal in signals
        ],
        "summary": _summarise(signals),
    }
    return payload


def persist_payload(payload: dict[str, Any], *, output: Path | None) -> Path:
    output_dir = output.parent if output else RADAR_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    if not output:
        stamp = payload["generated_at"].replace(":", "").replace("-", "")
        output = output_dir / f"systemic-radar-{stamp}.json"
    path = write_receipt_payload(output, payload)
    latest_link = output_dir / "latest.json"
    try:
        if latest_link.is_symlink() or latest_link.exists():
            latest_link.unlink()
        latest_link.symlink_to(path.name)
    except OSError:
        pass
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aggregate systemic health signals")
    parser.add_argument("--memory-window-days", type=int, default=7, help="Trailing days for memory cadence (default: 7)")
    parser.add_argument("--memory-target", type=int, default=5, help="Minimum entries within the window (default: 5)")
    parser.add_argument(
        "--plan-receipt-threshold",
        type=float,
        default=0.8,
        help="Minimum ratio of done plans with receipts (default: 0.8)",
    )
    parser.add_argument("--baseline-config", type=Path, default=DEFAULT_BASELINE, help="Baseline config path")
    parser.add_argument("--output", type=Path, help="Optional explicit receipt path")
    parser.add_argument("--markdown", type=Path, help="Optional markdown summary path")
    return parser.parse_args()


def _write_markdown(payload: dict[str, Any], receipt_path: Path, markdown_path: Path) -> None:
    rel = receipt_path.relative_to(ROOT)
    lines = [
        "# Systemic Radar Summary",
        "",
        f"**Updated:** {payload['generated_at']}  ",
        f"**Receipt:** `{rel}`",
        "",
        f"Summary: ready={payload['summary'].get('ready', 0)}, attention={payload['summary'].get('attention', 0)}, breach={payload['summary'].get('breach', 0)}",
        "",
        "## Axes",
    ]
    for axis in payload["axes"]:
        detail = axis["detail"]
        lines.append(f"- `{axis['axis']}:{axis['layer']}` — {axis['status']} — {detail}")
    lines.append("")
    lines.append("Generated automatically by `python -m tools.autonomy.systemic_radar --markdown …`.")
    atomic_write_text(markdown_path, "\n".join(lines) + "\n")


def main() -> int:
    args = parse_args()
    baseline = _load_baseline(args.baseline_config)
    payload = build_payload(args, baseline)
    path = persist_payload(payload, output=args.output)
    if args.markdown:
        _write_markdown(payload, path, args.markdown)
    print(f"systemic radar receipt -> {path.relative_to(ROOT)}")
    print(json.dumps(payload["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
