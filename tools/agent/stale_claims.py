"""Detect and optionally release stale bus claims (shared stewardship guard)."""
from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Iterator, Mapping

from teof._paths import repo_root

ROOT = repo_root(default=Path(__file__).resolve().parents[2])
CLAIMS_DIR = ROOT / "_bus" / "claims"
EVENTS_FILE = ROOT / "_bus" / "events" / "events.jsonl"


@dataclass
class Claim:
    task_id: str
    agent_id: str
    plan_id: str | None
    claimed_at: datetime
    status: str
    path: Path


@dataclass
class StaleClaim:
    claim: Claim
    last_touch: datetime
    age_hours: float


def _parse_iso_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _utc_now() -> datetime:
    return datetime.utcnow().replace(tzinfo=timezone.utc)


def _iter_claims(agent_filter: str | None = None) -> Iterator[Claim]:
    if not CLAIMS_DIR.exists():
        return iter(())
    for path in sorted(CLAIMS_DIR.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        agent = str(payload.get("agent_id", "")).strip()
        if agent_filter and agent_filter != agent:
            continue
        tasks_id = str(payload.get("task_id", "")).strip()
        claimed_at = _parse_iso_ts(payload.get("claimed_at"))
        status = str(payload.get("status", "")).strip()
        if not (tasks_id and claimed_at and status):
            continue
        yield Claim(
            task_id=tasks_id,
            agent_id=agent,
            plan_id=(payload.get("plan_id") or "").strip() or None,
            claimed_at=claimed_at,
            status=status,
            path=path,
        )


def _load_latest_events() -> Mapping[str, datetime]:
    latest: dict[str, datetime] = {}
    if not EVENTS_FILE.exists():
        return latest
    for line in EVENTS_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        task_id = payload.get("task_id")
        if not isinstance(task_id, str) or not task_id.strip():
            continue
        ts = _parse_iso_ts(payload.get("ts"))
        if not ts:
            continue
        existing = latest.get(task_id)
        if not existing or ts > existing:
            latest[task_id] = ts
    return latest


def find_stale_claims(
    *,
    agent: str | None,
    threshold_hours: float,
    now: datetime | None = None,
) -> list[StaleClaim]:
    current = now or _utc_now()
    latest_events = _load_latest_events()
    stale: list[StaleClaim] = []
    threshold = timedelta(hours=threshold_hours)

    for claim in _iter_claims(agent):
        if claim.status != "active":
            continue
        last_touch = claim.claimed_at
        event_ts = latest_events.get(claim.task_id)
        if event_ts and event_ts > last_touch:
            last_touch = event_ts
        age = current - last_touch
        if age >= threshold:
            stale.append(
                StaleClaim(
                    claim=claim,
                    last_touch=last_touch,
                    age_hours=round(age.total_seconds() / 3600, 2),
                )
            )
    return sorted(stale, key=lambda row: row.age_hours, reverse=True)


def release_claim(task_id: str, agent: str | None) -> None:
    notes = "Auto-release stale claim (> threshold)"
    cmd = [
        "python3",
        "-m",
        "teof",
        "bus_claim",
        "release",
        "--task",
        task_id,
        "--status",
        "released",
        "--notes",
        notes,
    ]
    if agent:
        cmd.extend(["--agent", agent])
    subprocess.run(cmd, check=True, cwd=ROOT)


def format_table(rows: Iterable[StaleClaim]) -> str:
    lines = ["task_id | agent | plan_id | hours_stale | last_touch"]
    lines.append("-" * 72)
    for row in rows:
        claim = row.claim
        lines.append(
            f"{claim.task_id} | {claim.agent_id} | {claim.plan_id or '-'} | "
            f"{row.age_hours:.2f} | {row.last_touch.isoformat(timespec='seconds')}"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent", help="Limit to claims owned by agent id")
    parser.add_argument(
        "--threshold-hours",
        type=float,
        default=6.0,
        help="Consider claims stale when idle for ≥ this many hours (default: 6)",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON summary")
    parser.add_argument(
        "--fail-on-stale",
        action="store_true",
        help="Exit with status 1 if stale claims are detected",
    )
    parser.add_argument(
        "--release",
        action="store_true",
        help="Release stale claims owned by the current agent (requires agent manifest)",
    )
    args = parser.parse_args(argv)

    stale = find_stale_claims(agent=args.agent, threshold_hours=args.threshold_hours)
    if args.json:
        payload = [
            {
                "task_id": row.claim.task_id,
                "agent_id": row.claim.agent_id,
                "plan_id": row.claim.plan_id,
                "hours_stale": row.age_hours,
                "last_touch": row.last_touch.isoformat(timespec="seconds"),
                "path": str(row.claim.path.relative_to(ROOT)),
            }
            for row in stale
        ]
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        if stale:
            print(format_table(stale))
        else:
            print("No stale claims detected.")

    if args.release:
        if not args.agent:
            raise SystemExit("--release currently requires --agent to avoid releasing other seats")
        for row in stale:
            if row.claim.agent_id != args.agent:
                continue
            release_claim(row.claim.task_id, args.agent)

    if args.fail_on_stale and stale:
        count = len(stale)
        print(f"::error ::detected {count} stale claim(s)")
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())


__all__ = ["find_stale_claims", "format_table", "main"]
