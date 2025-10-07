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
EVENT_REQUIRED_KEYS = {"ts", "by", "note", "prev_content_hash"}
ANCHOR_REQUIRED_KEYS = {"ts", "prev_content_hash"}


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


def _serialize_json(payload: MutableMapping[str, object]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def _compute_backfilled_events(head_json: MutableMapping[str, object]) -> list[dict[str, object]]:
    events = head_json.get("events")
    if not isinstance(events, list):
        return []

    base: MutableMapping[str, object] = json.loads(json.dumps(head_json))
    base["events"] = []

    computed: list[dict[str, object]] = []
    for raw_event in events:
        if not isinstance(raw_event, dict):
            return []
        prev_hash = sha256_bytes(_serialize_json(base).encode("utf-8"))
        event = dict(raw_event)
        event["prev_content_hash"] = prev_hash
        computed.append(event)
        base["events"].append(event)
    return computed


def _require_event_fields(event: Mapping[str, object]) -> None:
    missing = [key for key in EVENT_REQUIRED_KEYS if key not in event]
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


def _require_anchor_fields(anchor: Mapping[str, object], *, last_ts: str | None) -> None:
    missing = [key for key in ANCHOR_REQUIRED_KEYS if key not in anchor]
    if missing:
        raise AnchorsGuardError(
            f"appended anchor missing required fields: {', '.join(sorted(missing))}"
        )

    ts = str(anchor.get("ts", ""))
    if not ISO_TS_RE.match(ts):
        raise AnchorsGuardError("anchor ts must be ISO8601 UTC (YYYY-MM-DDTHH:MM:SSZ)")

    if last_ts is not None and ts < last_ts:
        raise AnchorsGuardError(f"anchor non-monotonic ts: {ts} < {last_ts}")

    prev_hash = str(anchor.get("prev_content_hash", ""))
    if len(prev_hash) != 64 or not all(c in "0123456789abcdef" for c in prev_hash.lower()):
        raise AnchorsGuardError("anchor prev_content_hash must be 64 hex characters")


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

    backfill_ok = False

    if head_json is not None:
        if len(events) < len(head_events):
            raise AnchorsGuardError(
                f"events truncated: head={len(head_events)} current={len(events)}"
            )
        prefix_len = len(head_events)
        if events[:prefix_len] != list(head_events):
            expected_backfill = _compute_backfilled_events(head_json)
            if expected_backfill and events[:prefix_len] == expected_backfill:
                backfill_ok = True
            else:
                raise AnchorsGuardError("mid-file edits detected (prefix differs from HEAD)")
    else:
        prefix_len = 0
        if not events:
            raise AnchorsGuardError("anchors.json has no events")

    if len(events) == prefix_len:
        return "events prev_content_hash backfill" if backfill_ok else "events unchanged"

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

    return "events append-only; tip hash valid; fields present"


def validate_anchor_appends(
    head_json: MutableMapping[str, object] | None,
    current_json: MutableMapping[str, object],
    head_bytes: bytes,
) -> str:
    anchors = current_json.get("anchors")
    if not isinstance(anchors, list):
        raise AnchorsGuardError("current anchors.json is invalid or missing 'anchors' list")

    head_anchors: Sequence[object] = []
    if head_json is not None:
        raw = head_json.get("anchors", []) if isinstance(head_json.get("anchors", []), list) else []
        head_anchors = raw

    if head_json is not None:
        if len(anchors) < len(head_anchors):
            raise AnchorsGuardError(
                f"anchors truncated: head={len(head_anchors)} current={len(anchors)}"
            )
        prefix_len = len(head_anchors)
        if anchors[:prefix_len] != list(head_anchors):
            raise AnchorsGuardError("mid-file edits detected in anchors list")
    else:
        prefix_len = 0

    if len(anchors) == prefix_len:
        return "anchors unchanged"

    appended = anchors[prefix_len:]
    if len(appended) != 1:
        raise AnchorsGuardError("append exactly one anchor event per change")

    appended_anchor = appended[0]
    if not isinstance(appended_anchor, dict):
        raise AnchorsGuardError("appended anchor must be a JSON object")

    last_ts: str | None = None
    if head_anchors:
        prev_anchor = head_anchors[-1]
        if isinstance(prev_anchor, dict):
            prev_ts = prev_anchor.get("ts")
            if isinstance(prev_ts, str):
                last_ts = prev_ts

    _require_anchor_fields(appended_anchor, last_ts=last_ts)

    head_hash = sha256_bytes(head_bytes)
    if appended_anchor["prev_content_hash"] != head_hash:
        raise AnchorsGuardError(
            "anchor prev_content_hash must match SHA-256 of HEAD:governance/anchors.json"
        )

    return "anchors append-only; tip hash valid; fields present"


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
        event_msg = validate_events(head_j, cur_j, head_b if head_b else b"")
        anchor_msg = validate_anchor_appends(head_j, cur_j, head_b if head_b else b"")
    except AnchorsGuardError as exc:
        fail(str(exc))
    else:
        details = [event_msg, anchor_msg]
        print(f"anchors-guard: OK ({'; '.join(details)})")


if __name__ == "__main__":
    main()
