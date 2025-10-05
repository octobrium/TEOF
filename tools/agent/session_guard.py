"""Session guard utilities enforcing recent handshakes before bus actions."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "AGENT_MANIFEST.json"
SESSION_DIR = ROOT / "_report" / "session"
AGENT_REPORT_DIR = ROOT / "_report" / "agent"
DEFAULT_MAX_AGE_SECONDS = 3600
ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"


class SessionGuardError(RuntimeError):
    """Raised when session guard invariants fail."""


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime(ISO_FMT)


def _default_agent(manifest_path: Path | None = None) -> str | None:
    path = manifest_path or MANIFEST_PATH
    if not path.exists():
        return None
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    agent = manifest.get("agent_id")
    if isinstance(agent, str) and agent.strip():
        return agent.strip()
    return None


def resolve_agent_id(explicit: str | None, *, manifest_path: Path | None = None) -> str:
    """Resolve the agent id, enforcing manifest alignment."""

    manifest_agent = _default_agent(manifest_path)
    if explicit is not None:
        agent_id = explicit.strip()
        if not agent_id:
            raise SystemExit("agent id required; use --agent or populate AGENT_MANIFEST.json")
        if manifest_agent and manifest_agent != agent_id:
            raise SystemExit(
                "agent mismatch: AGENT_MANIFEST.json declares"
                f" '{manifest_agent}' but command used '{agent_id}'. Run session_boot"
                " or update the manifest before proceeding."
            )
        return agent_id

    if manifest_agent:
        return manifest_agent

    raise SystemExit("agent id required; use --agent or populate AGENT_MANIFEST.json")


def _log_guard_event(agent_id: str, code: str, message: str, *, details: dict[str, Any] | None = None) -> None:
    report_dir = AGENT_REPORT_DIR / agent_id / "session_guard"
    report_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "ts": _iso_now(),
        "agent_id": agent_id,
        "code": code,
        "message": message,
    }
    if details:
        payload.update(details)
    with (report_dir / "events.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def _resolve_max_age(max_age_seconds: int | None) -> int:
    if max_age_seconds is not None and max_age_seconds > 0:
        return max_age_seconds
    env_value = os.environ.get("TEOF_SESSION_MAX_AGE")
    if env_value:
        try:
            parsed = int(env_value)
        except ValueError:
            parsed = DEFAULT_MAX_AGE_SECONDS
        else:
            if parsed > 0:
                return parsed
    return DEFAULT_MAX_AGE_SECONDS


def _parse_captured_at(path: Path) -> datetime:
    captured_at: str | None = None
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            if line.startswith("# captured_at="):
                captured_at = line.partition("=")[2].strip()
                break
    if not captured_at:
        raise SessionGuardError("session receipt missing '# captured_at=' header")
    try:
        return datetime.strptime(captured_at, ISO_FMT).replace(tzinfo=timezone.utc)
    except ValueError as exc:  # pragma: no cover - defensive guard
        raise SessionGuardError(f"unable to parse captured_at timestamp '{captured_at}'") from exc


def ensure_recent_session(
    agent_id: str,
    *,
    allow_stale: bool = False,
    max_age_seconds: int | None = None,
    context: str = "bus",
) -> None:
    """Verify the agent ran session_boot recently enough before bus writes."""

    if os.environ.get("TEOF_SESSION_GUARD_DISABLED", "").lower() in {"1", "true", "yes"}:
        return

    receipt_path = SESSION_DIR / agent_id / "manager-report-tail.txt"
    max_age = _resolve_max_age(max_age_seconds)

    if not receipt_path.exists():
        message = (
            f"session guard: no manager-report tail for {agent_id}. Run "
            "`python -m tools.agent.session_boot --agent {agent_id} --with-status` before using bus commands."
        )
        _log_guard_event(agent_id, "session_missing", message, details={"context": context})
        if allow_stale:
            _log_guard_event(agent_id, "session_override", message, details={"context": context})
            return
        raise SystemExit(message)

    try:
        captured_at = _parse_captured_at(receipt_path)
    except SessionGuardError as exc:
        message = f"session guard: {exc} ({receipt_path.relative_to(ROOT)})"
        _log_guard_event(
            agent_id,
            "session_invalid",
            message,
            details={"context": context, "receipt": receipt_path.relative_to(ROOT).as_posix()},
        )
        if allow_stale:
            _log_guard_event(agent_id, "session_override", message, details={"context": context})
            return
        raise SystemExit(message)

    age_seconds = (datetime.now(timezone.utc) - captured_at).total_seconds()
    if age_seconds <= max_age:
        return

    captured_iso = captured_at.strftime(ISO_FMT)
    message = (
        f"session guard: last session_boot for {agent_id} captured at {captured_iso} "
        f"({int(age_seconds)}s ago) exceeds freshness threshold ({max_age}s)."
        " Run session_boot again to refresh receipts."
    )
    _log_guard_event(
        agent_id,
        "session_stale",
        message,
        details={
            "context": context,
            "age_seconds": int(age_seconds),
            "max_age_seconds": max_age,
            "receipt": receipt_path.relative_to(ROOT).as_posix(),
        },
    )
    if allow_stale:
        _log_guard_event(agent_id, "session_override", message, details={"context": context})
        return
    raise SystemExit(message)


__all__ = [
    "DEFAULT_MAX_AGE_SECONDS",
    "SessionGuardError",
    "ensure_recent_session",
    "resolve_agent_id",
]
