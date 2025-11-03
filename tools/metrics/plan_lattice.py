"""Emit plan lattice hygiene metrics as canonical tuples.

Usage:
    python -m tools.metrics.plan_lattice --out _report/health/plan-lattice

The script scans `_plans/*.plan.json`, aggregates status and systemic coverage,
and writes a JSON receipt containing:
    - status_counts
    - clusters by keyword
    - systemic layer hotspots
    - stale active plans with recommended follow-up
    - metric tuples (`coherence_delta`, `truth_gain`,
      `proportion_index`, `reversibility_score`)

Each metric is reported as (value, evidence, window) per the canonical schema.
Where evidence is insufficient, the value is `null` and the evidence describes
missing signals so future runs can refine the tuple without deleting history.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


KEYWORDS = [
    "heartbeat",
    "queue",
    "plan hygiene",
    "quicklinks",
    "consensus",
    "governance",
    "capsule",
    "bus",
    "metrics",
    "commandment",
    "prune",
    "automation",
    "manager",
    "maintenance",
    "receipt",
    "tooling",
    "docs",
    "memory",
    "planner",
    "hygiene",
    "ledger",
    "claim",
    "backlog",
    "fractal",
]

ACTIVE_STATUSES = {"pending", "in_progress", "queued", "blocked"}


@dataclass
class PlanEntry:
    plan_id: str
    status: str
    created: dt.datetime
    updated: dt.datetime
    summary: str
    systemic_targets: Tuple[str, ...]
    layer_targets: Tuple[str, ...]
    layer: str | None
    path: Path

    @property
    def is_active(self) -> bool:
        return self.status in ACTIVE_STATUSES

    def age_days(self, now: dt.datetime) -> int:
        return int((now - self.updated).days)


def load_plans(root: Path) -> List[PlanEntry]:
    plans: List[PlanEntry] = []
    for path in sorted(root.glob("*.plan.json")):
        raw = json.loads(path.read_text())
        created = dt.datetime.fromisoformat(raw["created"].replace("Z", "+00:00"))
        created = created.astimezone(dt.timezone.utc)
        updated_raw = raw.get("updated", raw["created"])
        updated = dt.datetime.fromisoformat(updated_raw.replace("Z", "+00:00"))
        updated = updated.astimezone(dt.timezone.utc)
        plans.append(
            PlanEntry(
                plan_id=raw["plan_id"],
                status=raw.get("status", "").strip() or "unknown",
                created=created,
                updated=updated,
                summary=(raw.get("summary") or "").strip(),
                systemic_targets=tuple(raw.get("systemic_targets") or ()),
                layer_targets=tuple(raw.get("layer_targets") or ()),
                layer=raw.get("layer"),
                path=path,
            )
        )
    return plans


def keyword_bucket(summary: str) -> str:
    lowered = summary.lower()
    for token in KEYWORDS:
        if token in lowered:
            return token
    return "other"


def cluster_plans(plans: Sequence[PlanEntry]) -> List[Dict[str, object]]:
    buckets: Dict[str, List[PlanEntry]] = defaultdict(list)
    for plan in plans:
        buckets[keyword_bucket(plan.summary)].append(plan)
    cluster_rows: List[Dict[str, object]] = []
    for keyword, items in buckets.items():
        if len(items) < 5:
            continue
        cluster_rows.append(
            {
                "keyword": keyword,
                "count": len(items),
                "active": sum(1 for item in items if item.is_active),
            }
        )
    cluster_rows.sort(key=lambda row: (-row["count"], row["keyword"]))
    return cluster_rows


def systemic_hotspots(plans: Sequence[PlanEntry]) -> List[Dict[str, object]]:
    combos: Dict[Tuple[Tuple[str, ...], str | None], List[PlanEntry]] = defaultdict(list)
    for plan in plans:
        combos[(plan.systemic_targets, plan.layer)].append(plan)
    rows: List[Dict[str, object]] = []
    for (systemic, layer), items in combos.items():
        if len(items) <= 5:
            continue
        rows.append(
            {
                "systemic_targets": list(systemic),
                "layer": layer,
                "count": len(items),
                "active": sum(1 for item in items if item.is_active),
            }
        )
    rows.sort(key=lambda row: (-row["count"], row["layer"] or ""))
    return rows


def stale_plans(plans: Iterable[PlanEntry], now: dt.datetime, stale_after_days: int) -> List[Dict[str, object]]:
    stale_rows: List[Dict[str, object]] = []
    for plan in sorted(plans, key=lambda item: (item.updated, item.plan_id)):
        if not plan.is_active:
            continue
        age = plan.age_days(now)
        if age < stale_after_days:
            continue
        summary_lower = plan.summary.lower()
        if any(token in summary_lower for token in ("plan", "hygiene")):
            action = "Fold into consolidated plan hygiene sweep and close once receipts recorded"
        elif any(token in summary_lower for token in ("checklist", "push ready")):
            action = "Promote into workflow DNA or drop if redundant with push_ready helper receipts"
        elif any(token in summary_lower for token in ("scoreboard", "btc", "external")):
            action = "Decide scope of external observability; either anchor with receipts or archive as out-of-scope"
        else:
            action = "Review for relevance and either update with next steps or archive"
        stale_rows.append(
            {
                "plan_id": plan.plan_id,
                "status": plan.status,
                "age_days": age,
                "summary": plan.summary,
                "systemic_targets": list(plan.systemic_targets),
                "layer": plan.layer,
                "path": str(plan.path),
                "recommended_action": action,
            }
        )
    return stale_rows


def metric_tuples(
    plans: Sequence[PlanEntry],
    report_generated: dt.datetime,
    status_counts: Counter,
    ledger_totals: Dict[str, float],
    previous_report: Dict[str, object] | None,
) -> Dict[str, Dict[str, object]]:
    total = len(plans)
    done = status_counts.get("done", 0)
    blocked = status_counts.get("blocked", 0)
    active = sum(1 for plan in plans if plan.is_active)

    if total:
        coherence_value = round((done - blocked) / total, 3)
        curr_ratio = done / total
    else:
        coherence_value = None
        curr_ratio = None

    prev_ratio = None
    observation_window_days = None
    if previous_report:
        prev_counts = previous_report.get("status_counts", {})
        prev_total = prev_counts.get("done", 0) + prev_counts.get("blocked", 0) + previous_report.get("active_plan_count", 0)
        if prev_total:
            prev_ratio = prev_counts.get("done", 0) / prev_total
        try:
            prev_time = dt.datetime.fromisoformat(previous_report["generated"])
        except Exception:
            prev_time = None
        if prev_time:
            delta = report_generated - prev_time
            observation_window_days = max(delta.days, 1)

    coherence_gain_delta = None
    if prev_ratio is not None and curr_ratio is not None and observation_window_days:
        coherence_gain_delta = round((curr_ratio - prev_ratio) / observation_window_days, 4)

    total_force = ledger_totals.get("merge_cost_hours", 0.0)
    total_gain = ledger_totals.get("coherence_gain_estimate", 0.0) + ledger_totals.get("risk_reduction_estimate", 0.0)
    proportion_value = None
    if total_force and total_gain:
        proportion_value = round(total_force / total_gain, 3)

    metrics = {
        "coherence_delta": {
            "value": coherence_value,
            "evidence": {
                "total_plans": total,
                "done": done,
                "blocked": blocked,
                "active": active,
            },
            "window": {
                "baseline": None,
                "observed_at": report_generated.isoformat(),
            },
        },
        "truth_gain": {
            "value": coherence_gain_delta,
            "evidence": {
                "previous_done_ratio": prev_ratio,
                "current_done_ratio": curr_ratio,
            },
            "window": {
                "baseline": previous_report["generated"] if previous_report else None,
                "observed_at": report_generated.isoformat(),
            },
        },
        "proportion_index": {
            "value": proportion_value,
            "evidence": {
                "merge_cost_hours": total_force,
                "coherence_gain_estimate": ledger_totals.get("coherence_gain_estimate", 0.0),
                "risk_reduction_estimate": ledger_totals.get("risk_reduction_estimate", 0.0),
            },
            "window": {
                "baseline": None,
                "observed_at": report_generated.isoformat(),
            },
        },
        "reversibility_score": {
            "value": round((total - blocked) / total, 3) if total else None,
            "evidence": {
                "blocked_plans": blocked,
                "note": "Assumes blocked plans are the only non-recoverable portion; refine with rollback receipts",
            },
            "window": {
                "baseline": None,
                "observed_at": report_generated.isoformat(),
            },
        },
    }

    return metrics


def load_ledger_totals(ledger_path: Path) -> Dict[str, float]:
    totals = {
        "merge_cost_hours": 0.0,
        "coherence_gain_estimate": 0.0,
        "risk_reduction_estimate": 0.0,
    }
    if not ledger_path.exists():
        return totals
    for line in ledger_path.read_text().splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        totals["merge_cost_hours"] += float(entry.get("merge_cost_hours") or 0.0)
        totals["coherence_gain_estimate"] += float(entry.get("coherence_gain_estimate") or 0.0)
        totals["risk_reduction_estimate"] += float(entry.get("risk_reduction_estimate") or 0.0)
    return totals


def build_report(
    plans: Sequence[PlanEntry],
    stale_after_days: int,
    ledger_totals: Dict[str, float],
    previous_report: Dict[str, object] | None,
) -> Dict[str, object]:
    now = dt.datetime.now(dt.timezone.utc)
    status_counts: Counter = Counter(plan.status for plan in plans)
    clusters = cluster_plans(plans)
    hotspots = systemic_hotspots(plans)
    stale = stale_plans(plans, now=now, stale_after_days=stale_after_days)
    report = {
        "generated": now.isoformat(),
        "status_counts": dict(status_counts),
        "active_plan_count": sum(1 for plan in plans if plan.is_active),
        "stale_active_count": len(stale),
        "stale_active": stale,
        "clusters": clusters,
        "systemic_layer_hotspots": hotspots,
        "ledger_totals": ledger_totals,
        "recommendations": [],
        "metrics": metric_tuples(plans, now, status_counts, ledger_totals, previous_report),
    }

    for cluster in clusters:
        if cluster["keyword"] in {"receipt", "metrics", "bus", "heartbeat", "capsule", "automation", "governance"}:
            report["recommendations"].append(
                {
                    "type": "merge_cluster",
                    "keyword": cluster["keyword"],
                    "active_count": cluster["active"],
                    "suggestion": (
                        f"Merge active {cluster['keyword']} plans into a single quarterly hygiene track "
                        "and close duplicates after receipts backfill"
                    ),
                }
            )
    for hotspot in hotspots:
        if hotspot["layer"] == "L5" and hotspot["count"] > 15:
            report["recommendations"].append(
                {
                    "type": "relabel_hotspot",
                    "systemic_targets": hotspot["systemic_targets"],
                    "layer": hotspot["layer"],
                    "suggestion": (
                        "Re-label downstream work to cover neglected axes or justify concentration; "
                        "split into Unity/Energy core vs overlays"
                    ),
                }
            )
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Emit plan lattice hygiene metrics.")
    parser.add_argument("--plans", type=Path, default=Path("_plans"), help="Directory containing plan JSON files.")
    parser.add_argument("--out", type=Path, default=Path("_report/health/plan-lattice"), help="Output directory.")
    parser.add_argument("--snapshot", type=str, default=dt.datetime.now().strftime("%Y%m%d"), help="Snapshot label.")
    parser.add_argument("--stale-after-days", type=int, default=14, help="Age in days before an active plan is marked stale.")
    args = parser.parse_args(argv)

    plans = load_plans(args.plans)
    args.out.mkdir(parents=True, exist_ok=True)

    existing_snapshots = sorted(p for p in args.out.glob("*.json") if p.is_file())
    previous_report = None
    for candidate in reversed(existing_snapshots):
        if candidate.stem < args.snapshot:
            previous_report = json.loads(candidate.read_text())
            break

    ledger_totals = load_ledger_totals(args.out / "ledger.jsonl")
    report = build_report(
        plans,
        stale_after_days=args.stale_after_days,
        ledger_totals=ledger_totals,
        previous_report=previous_report,
    )

    out_path = args.out / f"{args.snapshot}.json"
    out_path.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
