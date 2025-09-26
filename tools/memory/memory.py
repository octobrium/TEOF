"""TEOF memory layer helpers (log/state/artifacts/runs)."""
from __future__ import annotations

import json
import uuid
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[2]  # repo root
MEMORY_DIR = ROOT / "memory"
LOG_PATH = MEMORY_DIR / "log.jsonl"
STATE_PATH = MEMORY_DIR / "state.json"
ARTIFACTS_PATH = MEMORY_DIR / "artifacts.json"
RUNS_DIR = MEMORY_DIR / "runs"

ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"


@dataclass(frozen=True)
class LogEvent:
    payload: Mapping[str, Any]
    raw: str
    hash_self: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime(ISO_FMT)


def _ensure_memory_dirs() -> None:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)


def _load_log_entries() -> list[Mapping[str, Any]]:
    if not LOG_PATH.exists():
        return []
    entries: list[Mapping[str, Any]] = []
    with LOG_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            entries.append(json.loads(line))
    return entries


def _hash_payload(payload: Mapping[str, Any]) -> str:
    data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _serialise_event(event: Mapping[str, Any]) -> LogEvent:
    payload = dict(event)
    if "ts" not in payload:
        payload["ts"] = _utc_now()
    if "run_id" not in payload:
        payload["run_id"] = payload["ts"].replace(":", "").replace("-", "") + f"-{uuid.uuid4().hex[:6]}"
    entries = _load_log_entries()
    if entries:
        payload.setdefault("hash_prev", entries[-1].get("hash_self"))
    else:
        payload.setdefault("hash_prev", None)
    payload["hash_self"] = _hash_payload(payload)
    raw = json.dumps(payload, sort_keys=True)
    return LogEvent(payload=payload, raw=raw, hash_self=payload["hash_self"])


def write_log(event: Mapping[str, Any], *, capsule: Mapping[str, Any] | None = None) -> Mapping[str, Any]:
    """Append an event to the memory log and optionally persist a run capsule.

    Args:
        event: Core event payload. `ts` and `run_id` default automatically.
        capsule: Optional structure mirroring the event with additional context.
            When provided, the capsule is persisted under `memory/runs/<run_id>/`.

    Returns:
        The serialised event (dict) that was written.
    """

    _ensure_memory_dirs()
    log_event = _serialise_event(event)
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(log_event.raw + "\n")

    if capsule is not None:
        run_dir = RUNS_DIR / log_event.payload["run_id"]
        run_dir.mkdir(parents=True, exist_ok=True)
        meta_path = run_dir / "meta.json"
        context_path = run_dir / "context.json"
        meta_path.write_text(json.dumps(log_event.payload, indent=2) + "\n", encoding="utf-8")
        context_path.write_text(json.dumps(capsule, indent=2) + "\n", encoding="utf-8")

    return log_event.payload


def _load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {"version": 0, "facts": []}
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def promote_fact(fact: Mapping[str, Any]) -> None:
    """Promote or update a fact in state.json.

    The fact must include an ``id`` field. Existing facts with the same id
    are replaced; otherwise the fact is appended.
    """

    _ensure_memory_dirs()
    state = _load_state()
    facts: list[dict[str, Any]] = state.get("facts", [])
    fact_id = fact.get("id")
    if not isinstance(fact_id, str) or not fact_id:
        raise ValueError("fact must include non-empty 'id'")

    replaced = False
    for idx, existing in enumerate(facts):
        if existing.get("id") == fact_id:
            facts[idx] = dict(fact)
            replaced = True
            break
    if not replaced:
        facts.append(dict(fact))

    state["facts"] = facts
    state["last_updated"] = _utc_now()
    STATE_PATH.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def _load_artifacts() -> dict[str, Any]:
    if not ARTIFACTS_PATH.exists():
        return {"version": 0, "artifacts": {}}
    return json.loads(ARTIFACTS_PATH.read_text(encoding="utf-8"))


def register_artifacts(task: str, artifacts: Iterable[Mapping[str, Any]]) -> None:
    """Record artifacts produced by a task with hash-based deduplication."""

    _ensure_memory_dirs()
    index = _load_artifacts()
    store = index.setdefault("artifacts", {})
    entries = store.setdefault(task, [])
    seen = {item.get("sha256") for item in entries}
    for artifact in artifacts:
        sha = artifact.get("sha256")
        if sha in seen:
            continue
        entries.append(dict(artifact))
        seen.add(sha)
    ARTIFACTS_PATH.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")


def recall(query: str, *, limit: int = 5) -> dict[str, list[Mapping[str, Any]]]:
    """Recall log events and facts matching a query string.

    Returns a dict with ``log`` and ``facts`` lists ordered from newest to oldest.
    """

    query_lower = query.lower()
    log_matches: list[Mapping[str, Any]] = []
    for entry in reversed(_load_log_entries()):
        if query_lower in json.dumps(entry, sort_keys=True).lower():
            log_matches.append(entry)
        if len(log_matches) >= limit:
            break

    state = _load_state()
    fact_matches = [fact for fact in state.get("facts", []) if query_lower in json.dumps(fact, sort_keys=True).lower()]

    return {
        "log": log_matches,
        "facts": fact_matches[:limit],
    }


__all__ = [
    "write_log",
    "promote_fact",
    "register_artifacts",
    "recall",
]
