#!/usr/bin/env python3
"""Ensure memory/state.json promotions are backed by receipts in memory/log.jsonl."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / "memory" / "state.json"
LOG_PATH = ROOT / "memory" / "log.jsonl"


@dataclass
class FactChange:
    fact_id: str
    fact: dict[str, Any]
    reason: str


def _git_show(path: str, base: str) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "show", f"{base}:{path}"],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        return []
    return [line for line in result.stdout.splitlines()]


def _load_state_lines(lines: Iterable[str]) -> dict[str, Any]:
    text = "\n".join(lines).strip()
    if not text:
        return {"facts": []}
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {"facts": []}
    if not isinstance(data, dict):
        return {"facts": []}
    data.setdefault("facts", [])
    return data


def _load_current_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {"facts": []}
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        raise SystemExit("::error ::memory/state.json invalid JSON")
    if not isinstance(data, dict):
        raise SystemExit("::error ::memory/state.json must be an object")
    data.setdefault("facts", [])
    return data


def _fact_map(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    mapping: dict[str, dict[str, Any]] = {}
    for fact in state.get("facts", []):
        if isinstance(fact, dict):
            fact_id = fact.get("id")
            if isinstance(fact_id, str):
                mapping[fact_id] = fact
    return mapping


def _detect_changes(base_state: dict[str, Any], head_state: dict[str, Any]) -> list[FactChange]:
    base_map = _fact_map(base_state)
    head_map = _fact_map(head_state)
    changes: list[FactChange] = []
    for fact_id, fact in head_map.items():
        base_fact = base_map.get(fact_id)
        if base_fact is None:
            changes.append(FactChange(fact_id, fact, "new fact"))
            continue
        if fact != base_fact:
            changes.append(FactChange(fact_id, fact, "updated fact"))
    return changes


def _load_log_lines(lines: Iterable[str]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for raw in lines:
        raw = raw.strip()
        if not raw:
            continue
        try:
            entry = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(entry, dict):
            entries.append(entry)
    return entries


def _read_current_log() -> list[str]:
    if not LOG_PATH.exists():
        return []
    return LOG_PATH.read_text(encoding="utf-8").splitlines()


def _fact_has_receipt(change: FactChange, appended_entries: list[dict[str, Any]]) -> bool:
    fact = change.fact
    source_run = fact.get("source_run")
    if not isinstance(source_run, str) or not source_run:
        return False

    for entry in appended_entries:
        run_id = entry.get("run_id")
        if isinstance(run_id, str) and run_id == source_run:
            return True
        derived = entry.get("derived_facts")
        if isinstance(derived, list) and change.fact_id in derived:
            return True
    return False


def main() -> int:
    base_sha = os.environ.get("BASE_SHA")
    if not base_sha:
        print("BASE_SHA not provided", file=sys.stderr)
        return 2

    base_state_lines = _git_show("memory/state.json", base_sha)
    base_state = _load_state_lines(base_state_lines)
    head_state = _load_current_state()

    changes = _detect_changes(base_state, head_state)
    if not changes:
        return 0

    base_log_lines = _git_show("memory/log.jsonl", base_sha)
    head_log_lines = _read_current_log()

    if base_log_lines and head_log_lines[: len(base_log_lines)] != base_log_lines:
        print("::error ::memory/log.jsonl must be append-only", file=sys.stderr)
        return 1

    appended_entries = _load_log_lines(head_log_lines[len(base_log_lines) :])

    errors = []
    for change in changes:
        if not _fact_has_receipt(change, appended_entries):
            errors.append(
                f"Fact '{change.fact_id}' ({change.reason}) lacks log receipt referencing source_run"
            )

    if errors:
        for err in errors:
            print(f"::error ::{err}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
