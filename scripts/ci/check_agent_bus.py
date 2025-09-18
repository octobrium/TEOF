#!/usr/bin/env python3
"""Validate the agent coordination bus artifacts."""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CLAIMS_DIR = ROOT / "_bus" / "claims"
EVENTS_LOG = ROOT / "_bus" / "events" / "events.jsonl"

VALID_STATUS = {"active", "paused", "released", "done"}
ISO_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def _validate_iso(value: str, *, field: str, errors: list[str]) -> None:
    if not ISO_REGEX.match(value):
        errors.append(f"{field} must be ISO8601 UTC (YYYY-MM-DDTHH:MM:SSZ)")
        return
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        errors.append(f"{field} has invalid timestamp '{value}'")


def _validate_claim(path: Path, errors: list[str]) -> None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{path.relative_to(ROOT)} invalid JSON: {exc}")
        return

    expected_task = path.stem
    task_id = data.get("task_id")
    if task_id != expected_task:
        errors.append(f"{path.relative_to(ROOT)} task_id '{task_id}' must match filename '{expected_task}'")
    agent_id = data.get("agent_id")
    if not isinstance(agent_id, str) or not agent_id.strip():
        errors.append(f"{path.relative_to(ROOT)} agent_id must be non-empty string")
    branch = data.get("branch")
    if not isinstance(branch, str) or not branch.strip():
        errors.append(f"{path.relative_to(ROOT)} branch must be non-empty string")
    elif not branch.startswith("agent/"):
        errors.append(f"{path.relative_to(ROOT)} branch must start with 'agent/'")
    status = data.get("status")
    if status not in VALID_STATUS:
        errors.append(f"{path.relative_to(ROOT)} status '{status}' not in {sorted(VALID_STATUS)}")
    claimed_at = data.get("claimed_at")
    if not isinstance(claimed_at, str):
        errors.append(f"{path.relative_to(ROOT)} claimed_at must be string")
    else:
        _validate_iso(claimed_at, field=f"{path.relative_to(ROOT)} claimed_at", errors=errors)
    released_at = data.get("released_at")
    if released_at is not None:
        if not isinstance(released_at, str):
            errors.append(f"{path.relative_to(ROOT)} released_at must be string when present")
        else:
            _validate_iso(released_at, field=f"{path.relative_to(ROOT)} released_at", errors=errors)


def _validate_events(errors: list[str]) -> None:
    if not EVENTS_LOG.exists():
        return
    with EVENTS_LOG.open(encoding="utf-8") as fh:
        for idx, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"_bus/events/events.jsonl line {idx} invalid JSON: {exc}")
                continue
            for field in ("ts", "agent_id", "event", "summary"):
                if field not in data:
                    errors.append(f"_bus/events/events.jsonl line {idx} missing field '{field}'")
            ts = data.get("ts")
            if isinstance(ts, str):
                _validate_iso(ts, field=f"events line {idx} ts", errors=errors)
            else:
                errors.append(f"_bus/events/events.jsonl line {idx} ts must be string")
            agent_id = data.get("agent_id")
            if not isinstance(agent_id, str) or not agent_id.strip():
                errors.append(f"_bus/events/events.jsonl line {idx} agent_id must be non-empty string")


def main() -> int:
    errors: list[str] = []

    if CLAIMS_DIR.exists():
        for path in sorted(CLAIMS_DIR.glob("*.json")):
            _validate_claim(path, errors)

    _validate_events(errors)

    if errors:
        for err in errors:
            print(f"::error::{err}")
        return 1

    print("::notice::agent bus artifacts validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
