#!/usr/bin/env python3
"""Compute systemic ratchet metrics for TEOF scans."""
from __future__ import annotations

import dataclasses
import datetime as dt
import json
from dataclasses import dataclass, field
from pathlib import Path
from statistics import median
from typing import Iterable, Mapping, Sequence

HISTORY_DIR = Path("_report") / "usage" / "systemic-scan"
RATCHET_BASENAME = "ratchet.json"
TERMINAL_CLAIM_STATUSES = {"done", "released", "closed", "cancelled", "abandoned"}


def _load_json(path: Path) -> Mapping[str, object] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _iter_plan_paths(root: Path) -> Iterable[Path]:
    plans_dir = root / "_plans"
    if not plans_dir.exists():
        return ()
    return plans_dir.glob("*.plan.json")


def _iter_claim_paths(root: Path) -> Iterable[Path]:
    claims_dir = root / "_bus" / "claims"
    if not claims_dir.exists():
        return ()
    return claims_dir.glob("*.json")


@dataclass(frozen=True)
class PlanStats:
    total_plans: int = 0
    done_plans: int = 0
    active_plans: int = 0
    closed_steps: int = 0
    open_steps: int = 0
    checkpoint_satisfied: int = 0
    plan_age_days: Sequence[float] = field(default_factory=tuple)

    @property
    def median_age_days(self) -> float:
        if not self.plan_age_days:
            return 0.0
        return float(median(self.plan_age_days))


@dataclass(frozen=True)
class ClaimStats:
    total_claims: int = 0
    active_claims: int = 0
    terminal_claims: int = 0


@dataclass(frozen=True)
class RatchetSnapshot:
    stamp: str
    coherence_gain: float
    complexity_added: float
    closure_velocity: float
    risk_load: float
    ratchet_index: float
    plan_stats: PlanStats
    claim_stats: ClaimStats
    scan_counts: Mapping[str, int]

    def as_dict(self) -> dict[str, object]:
        return {
            "stamp": self.stamp,
            "coherence_gain": self.coherence_gain,
            "complexity_added": self.complexity_added,
            "closure_velocity": self.closure_velocity,
            "risk_load": self.risk_load,
            "ratchet_index": self.ratchet_index,
            "plan_stats": {
                "total_plans": self.plan_stats.total_plans,
                "done_plans": self.plan_stats.done_plans,
                "active_plans": self.plan_stats.active_plans,
                "closed_steps": self.plan_stats.closed_steps,
                "open_steps": self.plan_stats.open_steps,
                "checkpoint_satisfied": self.plan_stats.checkpoint_satisfied,
                "median_age_days": self.plan_stats.median_age_days,
            },
            "claim_stats": {
                "total_claims": self.claim_stats.total_claims,
                "active_claims": self.claim_stats.active_claims,
                "terminal_claims": self.claim_stats.terminal_claims,
            },
            "scan_counts": dict(self.scan_counts),
        }


def collect_plan_stats(root: Path, *, now: dt.datetime) -> PlanStats:
    total = done = active = closed_steps = open_steps = satisfied = 0
    ages: list[float] = []

    for path in _iter_plan_paths(root):
        data = _load_json(path)
        if not data:
            continue
        total += 1
        status = str(data.get("status") or "").lower()
        if status == "done":
            done += 1
        else:
            active += 1
        checkpoint = data.get("checkpoint") or {}
        if str(checkpoint.get("status")).lower() == "satisfied":
            satisfied += 1
        created_raw = data.get("created")
        if isinstance(created_raw, str):
            try:
                created = dt.datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
                if created.tzinfo is None:
                    created = created.replace(tzinfo=dt.timezone.utc)
                age = (now - created).total_seconds() / 86400.0
                if age >= 0:
                    ages.append(age)
            except ValueError:
                pass
        steps = data.get("steps") or []
        if isinstance(steps, list):
            for step in steps:
                status_raw = str((step or {}).get("status") or "").lower()
                if status_raw == "done":
                    closed_steps += 1
                else:
                    open_steps += 1

    return PlanStats(
        total_plans=total,
        done_plans=done,
        active_plans=active,
        closed_steps=closed_steps,
        open_steps=open_steps,
        checkpoint_satisfied=satisfied,
        plan_age_days=tuple(ages),
    )


def collect_claim_stats(root: Path) -> ClaimStats:
    total = active = terminal = 0
    for path in _iter_claim_paths(root):
        data = _load_json(path)
        if not data:
            continue
        total += 1
        status = str(data.get("status") or "").lower()
        if status in TERMINAL_CLAIM_STATUSES:
            terminal += 1
        else:
            active += 1
    return ClaimStats(total_claims=total, active_claims=active, terminal_claims=terminal)


def compute_snapshot(
    *,
    root: Path,
    now: dt.datetime,
    scan_counts: Mapping[str, int],
    frontier_entries: Sequence[Mapping[str, object]],
    critic_anomalies: Sequence[Mapping[str, object]],
    tms_conflicts: Sequence[Mapping[str, object]],
    ethics_violations: Sequence[Mapping[str, object]],
) -> RatchetSnapshot:
    plan_stats = collect_plan_stats(root, now=now)
    claim_stats = collect_claim_stats(root)

    coherence_gain = float(plan_stats.closed_steps + plan_stats.done_plans + claim_stats.terminal_claims)
    complexity_added = float(
        plan_stats.open_steps + plan_stats.active_plans + claim_stats.active_claims + len(frontier_entries)
    )
    closure_velocity = float(plan_stats.done_plans + claim_stats.terminal_claims) / float(
        max(plan_stats.active_plans + claim_stats.active_claims, 1)
    )
    risk_load = float(len(critic_anomalies) + len(tms_conflicts) + len(ethics_violations))
    ratchet_index = (coherence_gain + closure_velocity) / max(complexity_added + risk_load, 1.0)

    if now.tzinfo is None:
        now = now.replace(tzinfo=dt.timezone.utc)
    now_utc = now.astimezone(dt.timezone.utc)
    stamp = now_utc.replace(microsecond=0).isoformat().replace("+00:00", "Z")

    snapshot = RatchetSnapshot(
        stamp=stamp,
        coherence_gain=round(coherence_gain, 2),
        complexity_added=round(complexity_added, 2),
        closure_velocity=round(closure_velocity, 3),
        risk_load=round(risk_load, 2),
        ratchet_index=round(ratchet_index, 3),
        plan_stats=plan_stats,
        claim_stats=claim_stats,
        scan_counts=dict(scan_counts),
    )
    return snapshot


def write_snapshot(snapshot: RatchetSnapshot, *, root: Path, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = snapshot.as_dict()

    out_path = out_dir / RATCHET_BASENAME
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    history_dir = root / HISTORY_DIR
    history_dir.mkdir(parents=True, exist_ok=True)
    history_path = history_dir / "ratchet-history.jsonl"
    with history_path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, ensure_ascii=False) + "\n")

    return out_path


__all__ = [
    "RatchetSnapshot",
    "PlanStats",
    "ClaimStats",
    "collect_plan_stats",
    "collect_claim_stats",
    "compute_snapshot",
    "write_snapshot",
]
