"""Session + memory guard utilities enforcing recent observation before bus actions."""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "AGENT_MANIFEST.json"
SESSION_DIR = ROOT / "_report" / "session"
AGENT_REPORT_DIR = ROOT / "_report" / "agent"
MEMORY_LOG_PATH = ROOT / "memory" / "log.jsonl"
DEFAULT_MAX_AGE_SECONDS = 3600
DEFAULT_MEMORY_MAX_AGE_SECONDS = 7200
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


def _memory_guard_dir(agent_id: str) -> Path:
    path = AGENT_REPORT_DIR / agent_id / "memory_guard"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _log_memory_guard_event(agent_id: str, code: str, message: str, *, details: dict[str, Any] | None = None) -> None:
    payload: dict[str, Any] = {
        "ts": _iso_now(),
        "agent_id": agent_id,
        "code": code,
        "message": message,
    }
    if details:
        payload.update(details)
    events = _memory_guard_dir(agent_id) / "events.jsonl"
    with events.open("a", encoding="utf-8") as handle:
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


def _read_last_memory_entry(memory_log: Path) -> dict[str, Any]:
    if not memory_log.exists():
        raise SystemExit(f"memory log missing at {memory_log}")
    last_line: str | None = None
    with memory_log.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                last_line = stripped
    if not last_line:
        raise SystemExit(f"memory log {memory_log} has no entries")
    try:
        entry = json.loads(last_line)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"unable to parse last memory entry ({memory_log}): {exc}") from exc
    return entry


def _memory_check_file(agent_id: str) -> Path:
    return _memory_guard_dir(agent_id) / "checks.jsonl"


def _rel_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


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


def record_memory_observation(
    agent_id: str,
    *,
    memory_log: Path | None = None,
    context: str = "dna",
    note: str | None = None,
) -> Path:
    """Record the most recent memory/log entry as an observation receipt."""

    log_path = memory_log or MEMORY_LOG_PATH
    entry = _read_last_memory_entry(log_path)
    record = {
        "ts": _iso_now(),
        "agent_id": agent_id,
        "context": context,
        "memory_entry": {
            "path": _rel_path(log_path),
            "ts": entry.get("ts"),
            "summary": entry.get("summary"),
            "ref": entry.get("ref"),
        },
    }
    if note:
        record["note"] = note
    log_path = _memory_check_file(agent_id)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    return log_path


def ensure_recent_memory_observation(
    agent_id: str,
    *,
    context: str = "dna",
    max_age_seconds: int | None = None,
    allow_stale: bool = False,
) -> None:
    """Ensure a memory observation receipt exists within the freshness window."""

    log_path = _memory_check_file(agent_id)
    max_age = max_age_seconds or DEFAULT_MEMORY_MAX_AGE_SECONDS
    if not log_path.exists():
        message = (
            f"memory guard: no recorded memory check for {agent_id} (context={context}). "
            "Run 'python -m tools.agent.session_guard log-memory-check --context "
            f"{context}' after reviewing memory/log.jsonl."
        )
        _log_memory_guard_event(agent_id, "memory_missing", message, details={"context": context})
        if allow_stale:
            _log_memory_guard_event(agent_id, "memory_override", message, details={"context": context})
            return
        raise SystemExit(message)

    latest: dict[str, Any] | None = None
    with log_path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if payload.get("context") == context:
                latest = payload
    if latest is None:
        message = (
            f"memory guard: no memory check logged for context '{context}' in {log_path}. "
            "Record an observation before editing the corresponding surfaces."
        )
        _log_memory_guard_event(agent_id, "memory_context_missing", message, details={"context": context})
        if allow_stale:
            _log_memory_guard_event(agent_id, "memory_override", message, details={"context": context})
            return
        raise SystemExit(message)

    entry_ts = latest.get("ts")
    if not entry_ts:
        message = (
            f"memory guard: latest memory check for {agent_id} is missing ts in {log_path}. "
            "Record a fresh observation."
        )
        _log_memory_guard_event(agent_id, "memory_invalid", message, details={"context": context})
        if allow_stale:
            _log_memory_guard_event(agent_id, "memory_override", message, details={"context": context})
            return
        raise SystemExit(message)

    try:
        observed_at = datetime.strptime(entry_ts, ISO_FMT).replace(tzinfo=timezone.utc)
    except ValueError:
        message = f"memory guard: unable to parse timestamp '{entry_ts}' in {log_path}"
        _log_memory_guard_event(agent_id, "memory_invalid", message, details={"context": context})
        if allow_stale:
            _log_memory_guard_event(agent_id, "memory_override", message, details={"context": context})
            return
        raise SystemExit(message)

    age_seconds = (datetime.now(timezone.utc) - observed_at).total_seconds()
    if age_seconds <= max_age:
        return

    message = (
        f"memory guard: last memory check for {agent_id} captured at {entry_ts} "
        f"({int(age_seconds)}s ago) exceeds freshness threshold ({max_age}s). "
        "Re-read memory/log.jsonl and log a fresh observation."
    )
    _log_memory_guard_event(
        agent_id,
        "memory_stale",
        message,
        details={"context": context, "age_seconds": int(age_seconds), "max_age_seconds": max_age},
    )
    if allow_stale:
        _log_memory_guard_event(agent_id, "memory_override", message, details={"context": context})
        return
    raise SystemExit(message)


__all__ = [
    "DEFAULT_MAX_AGE_SECONDS",
    "SessionGuardError",
    "ensure_recent_session",
    "ensure_recent_memory_observation",
    "record_memory_observation",
    "resolve_agent_id",
]


def _build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Session + memory guard helpers")
    sub = parser.add_subparsers(dest="command", required=True)

    log_mem = sub.add_parser("log-memory-check", help="Record that memory/log.jsonl was consulted")
    log_mem.add_argument("--agent", help="Agent id (defaults to AGENT_MANIFEST.json)")
    log_mem.add_argument("--context", default="dna", help="Context label (default: dna)")
    log_mem.add_argument(
        "--memory-log",
        default=str(MEMORY_LOG_PATH),
        help="Path to memory/log.jsonl (default: repo memory/log.jsonl)",
    )
    log_mem.add_argument("--note", help="Optional note to record with the observation")

    verify = sub.add_parser("verify-memory-check", help="Ensure a recent memory check exists")
    verify.add_argument("--agent", help="Agent id (defaults to AGENT_MANIFEST.json)")
    verify.add_argument("--context", default="dna", help="Context label to verify")
    verify.add_argument(
        "--max-age-seconds",
        type=int,
        default=DEFAULT_MEMORY_MAX_AGE_SECONDS,
        help="Freshness threshold in seconds (default: 7200)",
    )
    verify.add_argument(
        "--allow-stale",
        action="store_true",
        help="Log and continue when the memory check is missing or stale",
    )
    return parser


def _cmd_log_memory(args: argparse.Namespace) -> int:
    agent_id = resolve_agent_id(args.agent)
    memory_log = Path(args.memory_log).expanduser()
    record_memory_observation(agent_id, memory_log=memory_log, context=args.context, note=args.note)
    print(
        f"Logged memory observation for {agent_id} "
        f"(context={args.context}, entry={_rel_path(memory_log)})"
    )
    return 0


def _cmd_verify_memory(args: argparse.Namespace) -> int:
    agent_id = resolve_agent_id(args.agent)
    ensure_recent_memory_observation(
        agent_id,
        context=args.context,
        max_age_seconds=args.max_age_seconds,
        allow_stale=args.allow_stale,
    )
    print(
        f"Memory observation for {agent_id} (context={args.context}) "
        f"is within {args.max_age_seconds}s threshold."
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_cli_parser()
    args = parser.parse_args(argv)
    if args.command == "log-memory-check":
        return _cmd_log_memory(args)
    if args.command == "verify-memory-check":
        return _cmd_verify_memory(args)
    parser.error("Unknown command")


if __name__ == "__main__":
    import sys

    sys.exit(main())
