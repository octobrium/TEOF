import copy
import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from scripts.ci.check_anchors_guard import (
    AnchorsGuardError,
    sha256_bytes,
    validate_anchor_appends,
    validate_events,
)

ROOT = Path(__file__).resolve().parents[1]
ANCHORS = ROOT / "governance" / "anchors.json"


def load_head():
    head_bytes = ANCHORS.read_bytes()
    head_json = json.loads(head_bytes.decode("utf-8"))
    return head_json, head_bytes


def make_event(ts: str, prev_hash: str) -> dict:
    return {
        "ts": ts,
        "by": "automation",
        "note": "append-only guard test event",
        "prev_content_hash": prev_hash,
    }


def make_anchor(ts: str, prev_hash: str) -> dict:
    return {
        "ts": ts,
        "type": "capsule_freeze",
        "version": "v-test",
        "prev_content_hash": prev_hash,
        "notes": "append-only guard test anchor",
    }


def future_event_ts(head_json: dict, *, offset_seconds: int) -> str:
    timestamps = [
        event["ts"]
        for event in head_json.get("events", [])
        if isinstance(event, dict) and event.get("ts")
    ]
    latest = max(datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ") for ts in timestamps)
    return (latest + timedelta(seconds=offset_seconds)).strftime("%Y-%m-%dT%H:%M:%SZ")


def future_anchor_ts(head_json: dict, *, offset_seconds: int) -> str:
    anchors = head_json.get("anchors", []) or []
    timestamps = [
        anchor["ts"]
        for anchor in anchors
        if isinstance(anchor, dict) and anchor.get("ts")
    ]
    if timestamps:
        latest = max(datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ") for ts in timestamps)
    else:
        latest = max(
            datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
            for ts in (
                event["ts"]
                for event in head_json.get("events", [])
                if isinstance(event, dict) and event.get("ts")
            )
        )
    return (latest + timedelta(seconds=offset_seconds)).strftime("%Y-%m-%dT%H:%M:%SZ")


def test_validate_events_allows_prev_hash_backfill():
    full_head_json, _ = load_head()
    head_json = copy.deepcopy(full_head_json)
    for ev in head_json.get("events", []):
        if isinstance(ev, dict):
            ev.pop("prev_content_hash", None)

    head_bytes = json.dumps(head_json, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
    current = copy.deepcopy(head_json)

    backfilled: list[dict] = []
    for idx, ev in enumerate(current.get("events", [])):
        state = copy.deepcopy(current)
        state["events"] = [copy.deepcopy(e) for e in backfilled]
        prev_hash = sha256_bytes(json.dumps(state, ensure_ascii=False, indent=2).encode("utf-8") + b"\n")
        updated = dict(ev)
        updated["prev_content_hash"] = prev_hash
        backfilled.append(updated)

    current["events"] = backfilled

    msg = validate_events(head_json, current, head_bytes)
    assert "prev_content_hash backfill" in msg


def test_validate_events_accepts_single_well_formed_append():
    head_json, head_bytes = load_head()
    current = copy.deepcopy(head_json)

    prev = sha256_bytes(head_bytes)
    current["events"].append(make_event(future_event_ts(head_json, offset_seconds=60), prev))

    msg = validate_events(head_json, current, head_bytes)
    assert "events append-only" in msg


def test_validate_events_rejects_missing_prev_hash():
    head_json, head_bytes = load_head()
    current = copy.deepcopy(head_json)

    event = make_event(future_event_ts(head_json, offset_seconds=120), sha256_bytes(head_bytes))
    del event["prev_content_hash"]
    current["events"].append(event)

    with pytest.raises(AnchorsGuardError):
        validate_events(head_json, current, head_bytes)


def test_validate_events_rejects_multiple_appends():
    head_json, head_bytes = load_head()
    current = copy.deepcopy(head_json)
    prev = sha256_bytes(head_bytes)

    current["events"].append(make_event(future_event_ts(head_json, offset_seconds=180), prev))
    current["events"].append(make_event(future_event_ts(head_json, offset_seconds=240), prev))

    with pytest.raises(AnchorsGuardError):
        validate_events(head_json, current, head_bytes)


def test_validate_anchor_appends_accepts_single_append():
    head_json, head_bytes = load_head()
    current = copy.deepcopy(head_json)

    prev = sha256_bytes(head_bytes)
    current.setdefault("anchors", []).append(
        make_anchor(future_anchor_ts(head_json, offset_seconds=300), prev)
    )

    msg = validate_anchor_appends(head_json, current, head_bytes)
    assert "anchors append-only" in msg


def test_validate_anchor_appends_rejects_missing_prev_hash():
    head_json, head_bytes = load_head()
    current = copy.deepcopy(head_json)

    anchor = make_anchor(
        future_anchor_ts(head_json, offset_seconds=360), sha256_bytes(head_bytes)
    )
    del anchor["prev_content_hash"]
    current.setdefault("anchors", []).append(anchor)

    with pytest.raises(AnchorsGuardError):
        validate_anchor_appends(head_json, current, head_bytes)


def test_validate_anchor_appends_rejects_prev_hash_mismatch():
    head_json, head_bytes = load_head()
    current = copy.deepcopy(head_json)

    current.setdefault("anchors", []).append(
        make_anchor("2025-09-17T18:10:00Z", "0" * 64)
    )

    with pytest.raises(AnchorsGuardError):
        validate_anchor_appends(head_json, current, head_bytes)
