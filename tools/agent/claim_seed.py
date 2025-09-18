#!/usr/bin/env python3
"""Seed a claim file for a task before assignment."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CLAIMS_DIR = ROOT / "_bus" / "claims"
ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"
TERMINAL_STATUSES = {"done", "released", "closed", "cancelled", "abandoned"}


def iso_now() -> str:
    return datetime.now(timezone.utc).strftime(ISO_FMT)


def load_claim(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON in {path}: {exc}") from exc


def write_claim(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_payload(
    *,
    task_id: str,
    agent_id: str,
    status: str,
    plan_id: str | None,
    branch: str | None,
    notes: str | None,
    claimed_at: str | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "task_id": task_id,
        "agent_id": agent_id,
        "status": status,
        "claimed_at": claimed_at or iso_now(),
    }
    if plan_id:
        payload["plan_id"] = plan_id
    if branch:
        payload["branch"] = branch
    if notes:
        payload["notes"] = notes
    return payload


def ensure_seed_allowed(existing: dict[str, Any] | None, *, agent_id: str, status: str) -> None:
    if existing is None:
        return
    existing_agent = str(existing.get("agent_id", "")).strip()
    existing_status = str(existing.get("status", "")).strip().lower()
    if existing_status not in TERMINAL_STATUSES and existing_agent and existing_agent != agent_id:
        raise SystemExit(
            f"task already claimed by {existing_agent} (status={existing_status or 'active'})"
        )


def handle_seed(args: argparse.Namespace) -> int:
    task_id = args.task.upper()
    agent_id = args.agent
    status = args.status.lower()
    path = CLAIMS_DIR / f"{task_id}.json"
    existing = load_claim(path)
    ensure_seed_allowed(existing, agent_id=agent_id, status=status)

    claimed_at = args.claimed_at
    if claimed_at:
        try:
            datetime.strptime(claimed_at, ISO_FMT)
        except ValueError as exc:
            raise SystemExit("--claimed-at must be ISO8601 UTC (YYYY-MM-DDTHH:MM:SSZ)") from exc

    payload = build_payload(
        task_id=task_id,
        agent_id=agent_id,
        status=status,
        plan_id=args.plan,
        branch=args.branch,
        notes=args.notes,
        claimed_at=claimed_at,
    )
    # Preserve released_at if supplied explicitly
    if existing and existing.get("released_at") and status in TERMINAL_STATUSES:
        payload["released_at"] = existing["released_at"]
    write_claim(path, payload)
    print(f"seeded claim {path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Seed a claim file before assignment")
    parser.add_argument("--task", required=True, help="Task identifier (e.g., QUEUE-010)")
    parser.add_argument("--agent", required=True, help="Agent id to assign")
    parser.add_argument("--plan", help="Plan identifier to record")
    parser.add_argument("--branch", help="Branch name to record")
    parser.add_argument("--status", default="paused", help="Initial claim status (default: paused)")
    parser.add_argument("--notes", help="Optional notes")
    parser.add_argument("--claimed-at", help="Override timestamp (ISO8601 UTC)")
    parser.set_defaults(func=handle_seed)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except SystemExit as exc:
        raise exc
    except Exception as exc:  # pragma: no cover
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
