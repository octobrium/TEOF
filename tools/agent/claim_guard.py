"""Shared claim guard helpers for agent bus tools."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

TERMINAL_CLAIM_STATUSES = {"done", "released", "closed", "cancelled", "abandoned"}


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _record_guard_failure(
    *,
    report_root: Path,
    agent_id: str,
    action: str,
    reason: str,
    task_id: str | None,
    claim_owner: str | None,
    claim_status: str | None,
) -> None:
    report_dir = report_root / agent_id
    report_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "ts": _iso_now(),
        "agent_id": agent_id,
        "event": action,
        "reason": reason,
    }
    if task_id:
        payload["task_id"] = task_id
    if claim_owner is not None:
        payload["claim_owner"] = claim_owner
    if claim_status is not None:
        payload["claim_status"] = claim_status
    with (report_dir / "errors.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, sort_keys=True) + "\n")


def _load_claim(path: Path) -> Mapping[str, Any] | None:
    if not path.exists():
        return None
    try:
        data: Mapping[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive guard
        raise SystemExit(f"invalid claim JSON in {path}: {exc}") from exc
    return data


def ensure_claim_owner(
    *,
    claims_dir: Path,
    report_root: Path,
    agent_id: str,
    task_id: str,
    action: str,
) -> None:
    """Enforce claim ownership before writing guarded records.

    Args:
        claims_dir: Directory containing claim files.
        report_root: Base directory for agent error logs.
        agent_id: Agent attempting the action.
        task_id: Task identifier associated with the action.
        action: Human-readable action label (event or message type).

    Raises:
        SystemExit: If the claim is missing or held by a different agent.
    """

    claim_path = claims_dir / f"{task_id}.json"
    claim = _load_claim(claim_path)
    if claim is None:
        reason = (
            f"task {task_id} has no claim file; run `python -m tools.agent.bus_claim claim --task {task_id}` first"
        )
        _record_guard_failure(
            report_root=report_root,
            agent_id=agent_id,
            action=action,
            reason=reason,
            task_id=task_id,
            claim_owner=None,
            claim_status=None,
        )
        raise SystemExit(reason)

    owner = str(claim.get("agent_id", "")).strip()
    status = str(claim.get("status", "")).strip().lower()
    if status in TERMINAL_CLAIM_STATUSES:
        return
    if owner != agent_id:
        reason = (
            f"task {task_id} currently claimed by {owner or 'UNKNOWN'} (status={status or 'active'}); "
            f"run bus_claim release/claim before logging {action}"
        )
        _record_guard_failure(
            report_root=report_root,
            agent_id=agent_id,
            action=action,
            reason=reason,
            task_id=task_id,
            claim_owner=owner or None,
            claim_status=status or None,
        )
        raise SystemExit(reason)


__all__ = ["ensure_claim_owner", "TERMINAL_CLAIM_STATUSES"]
