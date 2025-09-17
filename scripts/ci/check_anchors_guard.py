#!/usr/bin/env python3
"""Append-only guard for governance/anchors.json.

Checks that contributors append exactly one well-formed event, keep timestamps
monotonic, and chain `prev_content_hash` to the previous file contents.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Mapping, MutableMapping, Sequence

ROOT = Path(__file__).resolve().parents[2]
P = ROOT / "governance" / "anchors.json"

ISO_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
REQUIRED_KEYS = {"ts", "by", "note", "prev_content_hash"}


class AnchorsGuardError(Exception):
    """Raised when the append-only constraints are violated."""


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def git_show(pathspec: str) -> bytes:
    try:
        return subprocess.check_output(["git", "show", pathspec], cwd=ROOT)
    except subprocess.CalledProcessError:
        return b""


def load_json_bytes(b: bytes):
    try:
        return json.loads(b.decode("utf-8"))
    except Exception:
        return None


def _require_event_fields(event: Mapping[str, object]) -> None:
    missing = [key for key in REQUIRED_KEYS if key not in event]
    if missing:
        raise AnchorsGuardError(
            f"appended event missing required fields: {', '.join(sorted(missing))}"
        )

    ts = str(event.get("ts", ""))
    if not ISO_TS_RE.match(ts):
        raise AnchorsGuardError("event ts must be ISO8601 UTC (YYYY-MM-DDTHH:MM:SSZ)")

    if not str(event.get("by", "")).strip():
        raise AnchorsGuardError("event 'by' must be non-empty")
    if not str(event.get("note", "")).strip():
        raise AnchorsGuardError("event 'note' must be non-empty")

    prev_hash = str(event.get("prev_content_hash", ""))
    if len(prev_hash) != 64 or not all(c in "0123456789abcdef" for c in prev_hash.lower()):
        raise AnchorsGuardError("prev_content_hash must be 64 hex characters")


def validate_events(
    head_json: MutableMapping[str, object] | None,
    current_json: MutableMapping[str, object],
    head_bytes: bytes,
) -> str:
    events = current_json.get("events")
    if not isinstance(events, list):
        raise AnchorsGuardError("current anchors.json is invalid or missing 'events' list")

    head_events: Sequence[object] = []
    if head_json is not None:
        head_events = head_json.get("events", []) if isinstance(head_json.get("events", []), list) else []

    if head_json is not None:
        if len(events) < len(head_events):
            raise AnchorsGuardError(
                f"events truncated: head={len(head_events)} current={len(events)}"
            )
        prefix_len = len(head_events)
        if events[:prefix_len] != list(head_events):
            raise AnchorsGuardError("mid-file edits detected (prefix differs from HEAD)")
    else:
        prefix_len = 0
        if not events:
            raise AnchorsGuardError("anchors.json has no events")

    if len(events) == prefix_len:
        return "anchors-guard: OK (no new events)"

    added = events[prefix_len:]
    if len(added) != 1:
        raise AnchorsGuardError("append exactly one anchors event per change")

    appended = added[0]
    if not isinstance(appended, dict):
        raise AnchorsGuardError("appended event must be a JSON object")

    _require_event_fields(appended)

    if head_json is not None and head_events:
        last_ts = str(head_events[-1]["ts"])  # type: ignore[index]
        if str(appended["ts"]) < last_ts:
            raise AnchorsGuardError(f"non-monotonic ts: {appended['ts']} < {last_ts}")

    head_hash = sha256_bytes(head_bytes)
    if appended["prev_content_hash"] != head_hash:
        raise AnchorsGuardError(
            "prev_content_hash must match SHA-256 of HEAD:governance/anchors.json"
        )

    return "anchors-guard: OK (append-only; tip hash valid; fields present)"


def fail(msg: str) -> None:
    print(f"❌ anchors-guard: {msg}")
    sys.exit(1)


def main() -> None:
    if not P.exists():
        print("anchors-guard: governance/anchors.json missing (skip)")
        return

    head_b = git_show("HEAD:governance/anchors.json")
    cur_b = P.read_bytes()

    head_j = load_json_bytes(head_b) if head_b else None
    cur_j = load_json_bytes(cur_b)
    if cur_j is None:
        fail("current anchors.json is not valid JSON")

    try:
        msg = validate_events(head_j, cur_j, head_b if head_b else b"")
    except AnchorsGuardError as exc:
        fail(str(exc))
    else:
        print(msg)


if __name__ == "__main__":
    main()
