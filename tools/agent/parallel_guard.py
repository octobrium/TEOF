"""Detect and enforce safeguards when multiple agents operate in parallel."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from tools.autonomy.shared import load_json


ROOT = Path(__file__).resolve().parents[2]
EVENT_LOG = ROOT / "_bus" / "events" / "events.jsonl"
CLAIMS_DIR = ROOT / "_bus" / "claims"
CONSENT_POLICY_PATH = ROOT / "docs" / "automation" / "autonomy-consent.json"

DEFAULT_CONFIG = {
    "hard_window_seconds": 900,
    "soft_window_seconds": 1800,
    "stale_window_seconds": 3600,
    "require_plan_claim": True,
    "require_scan_receipt": True,
}


@dataclass
class ParallelReport:
    """Summary of active peers and resulting guard requirements."""

    agent_id: str | None
    severity: str
    generated_at: str
    hard_agents: list[str] = field(default_factory=list)
    soft_agents: list[str] = field(default_factory=list)
    stale_agents: list[str] = field(default_factory=list)
    active_claims: list[dict[str, Any]] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)
    self_active_claims: list[dict[str, Any]] = field(default_factory=list)
    requirements: dict[str, bool] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "severity": self.severity,
            "generated_at": self.generated_at,
            "hard_agents": sorted(set(self.hard_agents)),
            "soft_agents": sorted(set(self.soft_agents)),
            "stale_agents": sorted(set(self.stale_agents)),
            "active_claims": self.active_claims,
            "events": self.events,
            "notes": self.notes,
            "config": self.config,
            "self_active_claims": self.self_active_claims,
            "requirements": self.requirements,
        }


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_iso(value: str) -> datetime | None:
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def _load_parallel_config() -> dict[str, Any]:
    data = load_json(CONSENT_POLICY_PATH)
    if isinstance(data, Mapping):
        parallel = data.get("parallel")
        if isinstance(parallel, Mapping):
            merged = dict(DEFAULT_CONFIG)
            for key, value in parallel.items():
                merged[key] = value
            return merged
    return dict(DEFAULT_CONFIG)


def _iter_claims() -> Iterable[dict[str, Any]]:
    if not CLAIMS_DIR.exists():
        return []
    claims: list[dict[str, Any]] = []
    for path in sorted(CLAIMS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        data["_path"] = path.relative_to(ROOT).as_posix()
        claims.append(data)
    return claims


def _iter_recent_events(now: datetime, max_age: int) -> list[dict[str, Any]]:
    if not EVENT_LOG.exists():
        return []
    try:
        lines = EVENT_LOG.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    events: list[dict[str, Any]] = []
    for raw in reversed(lines):
        if not raw.strip():
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        agent_id = payload.get("agent_id")
        timestamp = _parse_iso(payload.get("ts")) if isinstance(payload.get("ts"), str) else None
        if timestamp is None:
            continue
        age = (now - timestamp).total_seconds()
        if age < 0:
            age = 0
        if age > max_age:
            break
        payload["_age_seconds"] = age
        events.append(payload)
    return events


def _bucket_events(
    *,
    events: Iterable[dict[str, Any]],
    agent_id: str | None,
    config: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[str], list[str], list[str]]:
    hard_agents: list[str] = []
    soft_agents: list[str] = []
    stale_agents: list[str] = []
    bucketed: list[dict[str, Any]] = []

    hard_window = max(int(config.get("hard_window_seconds", DEFAULT_CONFIG["hard_window_seconds"])), 0)
    soft_window = max(int(config.get("soft_window_seconds", DEFAULT_CONFIG["soft_window_seconds"])), hard_window)
    stale_window = max(int(config.get("stale_window_seconds", DEFAULT_CONFIG["stale_window_seconds"])), soft_window)

    for event in events:
        other_agent = event.get("agent_id")
        if not isinstance(other_agent, str) or (agent_id and other_agent == agent_id):
            continue
        age = float(event.get("_age_seconds", 0))
        if age <= hard_window:
            bucket = "hard"
            hard_agents.append(other_agent)
        elif age <= soft_window:
            bucket = "soft"
            soft_agents.append(other_agent)
        elif age <= stale_window:
            bucket = "stale"
            stale_agents.append(other_agent)
        else:
            continue
        bucketed.append(
            {
                "agent_id": other_agent,
                "event": event.get("event"),
                "ts": event.get("ts"),
                "age_seconds": int(age),
                "bucket": bucket,
                "summary": event.get("summary"),
                "task_id": event.get("task_id"),
            }
        )

    return bucketed, hard_agents, soft_agents, stale_agents


def detect_parallel_state(agent_id: str | None, *, now: datetime | None = None) -> ParallelReport:
    generated_at = _iso_now()
    if agent_id is None:
        report = ParallelReport(
            agent_id=None,
            severity="none",
            generated_at=generated_at,
            notes=["agent_id_unresolved"],
            config=dict(DEFAULT_CONFIG),
        )
        report.requirements = {
            "session_boot": False,
            "plan_claim": False,
            "post_run_scan": False,
        }
        return report

    now = now or datetime.now(timezone.utc)
    config = _load_parallel_config()
    stale_window = max(int(config.get("stale_window_seconds", DEFAULT_CONFIG["stale_window_seconds"])), 0)

    claims = list(_iter_claims())
    active_claims: list[dict[str, Any]] = []
    self_claims: list[dict[str, Any]] = []
    for claim in claims:
        claim_agent = claim.get("agent_id")
        status = str(claim.get("status", "")).lower()
        released = claim.get("released_at")
        is_active = status in {"active", "paused"} and not released
        if not is_active:
            continue
        summary = {
            "agent_id": claim_agent,
            "task_id": claim.get("task_id"),
            "plan_id": claim.get("plan_id"),
            "status": status,
            "claimed_at": claim.get("claimed_at"),
            "path": claim.get("_path"),
        }
        if claim_agent == agent_id:
            self_claims.append(summary)
        else:
            active_claims.append(summary)

    events = _iter_recent_events(now, stale_window)
    bucketed, hard_agents, soft_agents, stale_agents = _bucket_events(
        events=events,
        agent_id=agent_id,
        config=config,
    )

    severity = "none"
    if active_claims or hard_agents:
        severity = "hard"
    elif soft_agents:
        severity = "soft"
    elif stale_agents:
        severity = "stale"

    requirements = {
        "session_boot": severity in {"soft", "hard"},
        "plan_claim": severity == "hard" and bool(config.get("require_plan_claim", True)),
        "post_run_scan": severity == "hard" and bool(config.get("require_scan_receipt", True)),
    }

    report = ParallelReport(
        agent_id=agent_id,
        severity=severity,
        generated_at=generated_at,
        hard_agents=hard_agents,
        soft_agents=soft_agents,
        stale_agents=stale_agents,
        active_claims=active_claims,
        events=bucketed,
        notes=[],
        config=dict(config),
        self_active_claims=self_claims,
        requirements=requirements,
    )

    if not events and not active_claims:
        report.notes.append("no_parallel_signals")

    return report


def write_parallel_receipt(agent_id: str, report: ParallelReport) -> Path:
    receipt_dir = ROOT / "_report" / "session" / agent_id / "parallel-state"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    safe_ts = report.generated_at.replace(":", "").replace("-", "")
    receipt_path = receipt_dir / f"parallel-state-{safe_ts}.json"
    receipt_path.write_text(json.dumps(report.to_payload(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return receipt_path


def format_summary(report: ParallelReport) -> str:
    if report.severity in {"none", "unknown"}:
        return "Parallel state: none (no active peers detected)"

    agents = sorted(set(report.hard_agents + report.soft_agents + report.stale_agents))
    desc = ", ".join(agents) if agents else "unknown"
    claim_note = "; active claims present" if report.active_claims else ""
    return f"Parallel state: {report.severity.upper()} (agents: {desc}{claim_note})"


def agent_has_active_claim(agent_id: str, report: ParallelReport | None = None) -> bool:
    if report is not None and report.self_active_claims:
        return True
    for claim in _iter_claims():
        if claim.get("agent_id") != agent_id:
            continue
        status = str(claim.get("status", "")).lower()
        if status in {"active", "paused"} and not claim.get("released_at"):
            return True
    return False


__all__ = [
    "ParallelReport",
    "detect_parallel_state",
    "write_parallel_receipt",
    "format_summary",
    "agent_has_active_claim",
]
