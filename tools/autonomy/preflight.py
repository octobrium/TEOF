"""Aggregate preflight checks for autonomy runs."""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Iterable

from tools.autonomy import critic, ethics_gate, frontier, objectives_status, tms
from tools.fractal import conformance as fractal_conformance

try:  # optional bus integration
    from tools.agent import bus_event as bus_event_mod
except ImportError:  # pragma: no cover - bus module optional
    bus_event_mod = None

ROOT = Path(__file__).resolve().parents[2]
AUTH_JSON = ROOT / "_report" / "usage" / "external-authenticity.json"
STATUS_PATH = ROOT / "_report" / "planner" / "validate" / "summary-latest.json"
DEFAULT_RECEIPT_DIR = ROOT / "_report" / "usage" / "autonomy-preflight"
FRACTAL_BASELINE_PATH = ROOT / "docs" / "fractal" / "baseline.json"


def _load_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def gather_snapshot(*, frontier_limit: int = 5, objectives_window_days: float = 7.0) -> dict:
    authenticity = _load_json(AUTH_JSON)
    planner_status = _load_json(STATUS_PATH)
    objectives = objectives_status.compute_status(window_days=objectives_window_days)
    frontier_preview = []
    try:
        frontier_preview = [entry.as_dict() for entry in frontier.compute_frontier(limit=max(0, frontier_limit))]
    except Exception:
        frontier_preview = []
    critic_alerts = critic.detect_anomalies()
    tms_conflicts = tms.detect_conflicts()
    ethics_violations = ethics_gate.detect_violations()
    fractal_report = fractal_conformance.build_report(strict=False)
    fractal_baseline = {}
    try:
        fractal_baseline = json.loads(FRACTAL_BASELINE_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        fractal_baseline = {}

    return {
        "generated_at": dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "authenticity": authenticity,
        "planner_status": planner_status,
        "objectives": objectives,
        "frontier_preview": frontier_preview,
        "critic_alerts": critic_alerts,
        "tms_conflicts": tms_conflicts,
        "ethics_violations": ethics_violations,
        "fractal_conformance": {
            "summary": fractal_report.get("summary", {}),
            "issues": {
                "queue": [entry for entry in fractal_report.get("queue", []) if entry.get("issues")],
                "plans": [entry for entry in fractal_report.get("plans", []) if entry.get("issues")],
                "memory": [entry for entry in fractal_report.get("memory", []) if entry.get("issues")],
            },
            "baseline": (fractal_baseline or {}).get("summary", {}),
        },
    }


def evaluate_snapshot(snapshot: dict) -> tuple[bool, list[str]]:
    issues: list[str] = []

    auth = snapshot.get("authenticity") or {}
    overall = auth.get("overall_avg_trust")
    attention = auth.get("attention_feeds") or []
    try:
        trust_ok = float(overall) >= 0.7 if overall is not None else False
    except (TypeError, ValueError):  # pragma: no cover - defensive
        trust_ok = False
    if not trust_ok or attention:
        issues.append("authenticity below threshold")

    planner_status = snapshot.get("planner_status") or {}
    status_ok = (planner_status.get("status") or "").lower() in {"ok", "pass"}
    exit_code = planner_status.get("exit_code")
    if not status_ok and exit_code is None:
        issues.append("planner status not ok")
    if isinstance(exit_code, int) and exit_code != 0:
        issues.append(f"planner exit_code={exit_code}")

    if snapshot.get("ethics_violations"):
        issues.append("ethics violations present")
    if snapshot.get("tms_conflicts"):
        issues.append("tms conflicts present")
    if snapshot.get("critic_alerts"):
        issues.append("critic alerts present")

    fractal = snapshot.get("fractal_conformance") or {}
    fractal_summary = fractal.get("summary") or {}
    baseline = fractal.get("baseline") or {}
    for key in ("queue_with_issues", "plans_with_issues", "memory_with_issues"):
        observed = fractal_summary.get(key, 0)
        allowed = baseline.get(key, 0)
        if observed > allowed:
            issues.append("fractal conformance gaps present")
            break

    healthy = len(issues) == 0
    return healthy, issues


def write_receipt(snapshot: dict, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out_path


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="Receipt path (default: _report/usage/autonomy-preflight/preflight-<UTC>.json)")
    parser.add_argument("--frontier-limit", type=int, default=5, help="Number of frontier items to include")
    parser.add_argument("--objectives-window", type=float, default=7.0, help="Window in days for objectives snapshot")
    parser.add_argument(
        "--emit-bus",
        action="store_true",
        help="Emit a bus status event when issues are detected",
    )
    parser.add_argument(
        "--bus-agent",
        default="autonomy-preflight",
        help="Agent id to use when emitting bus events (default: autonomy-preflight)",
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    snapshot = gather_snapshot(frontier_limit=args.frontier_limit, objectives_window_days=args.objectives_window)
    healthy, issues = evaluate_snapshot(snapshot)
    snapshot["issues"] = issues
    timestamp = snapshot["generated_at"].replace(":", "").replace("-", "")
    out_path = args.out or (DEFAULT_RECEIPT_DIR / f"preflight-{timestamp}.json")
    write_receipt(snapshot, out_path)
    try:
        rel = out_path.relative_to(ROOT)
    except ValueError:
        rel = out_path
    print(f"preflight: wrote receipt → {rel}")

    if args.emit_bus and not healthy and bus_event_mod is not None:
        summary = "autonomy preflight issues: " + ", ".join(issues)
        try:
            bus_event_mod.log_event(
                event="status",
                summary=summary,
                agent=args.bus_agent,
                root=ROOT,
            )
        except Exception as exc:  # pragma: no cover - best effort
            print(f"::error:: failed to emit bus event: {exc}", flush=True)

    return 0 if healthy else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
